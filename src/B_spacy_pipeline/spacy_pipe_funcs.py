import json
import re
from pathlib import Path
from typing import Generator
from dataclasses import asdict

import pandas as pd
import requests
from icecream import ic
from spacy import Language
from spacy.matcher import Matcher
from spacy.tokens import Span, Doc

from src.A_data.company_data import comp_name_symbol_list, comp_name_list_without_legal, company_names_dict, symbol_comp_name_dict
from src.settings.config import ConfigBasic
from src.settings.enums import NaturalLanguage, SpacyComp, SpacyExt, IDXReferTo
from src.B_spacy_pipeline.spacy_input import SpacyInput
from src.B_spacy_pipeline.data_models import EntsWithCustExts, SearchMatch, Cluster, ClusterHead, DataContainer
from src.G_utils.concurrency import run_re_finditer_concurrently
from src.G_utils.funcs import fuzzy_search_one, exc_info_formatter
from src.G_utils.regex_funcs import split_company_name_to_name_and_legal

# ic.enable()
ic.disable()


class PipeFunc:
    """ The purpose of the parent class 'PipeComp' is to load and save the a_extract_conf (that was passed at build) to the
        pipeline components. Please see: https://spacy.io/usage/processing-pipelines#custom-components-factories
    """
    CUST_EXT_VAL_WAS_SET: bool = False

    def __init__(self, nlp, name, data: dict = None):
        """ spaCy requires that the __init__() of a custom class to build a custom pipe component must always get
                passed (at least): nlp (Language object), name (string) of component. It won't work without these two. """
        """ In the current setup, all custom pipe components/classes (beside the required nlp, name) get only one
            data parameter passed at most. If additional parameters shall get passed to any new or changed component,
            more data variables can be created here by adding 'data_2', 'data_3', etc."""
        self.nlp: Language = nlp
        self.name: str = name
        self.data: dict = data
        self.custom_extensions = [enum for enum in SpacyExt]
        self.relevant_labels: list = ConfigBasic.spacy_relevant_labels
        self.init_mark: str = ConfigBasic.spacy_init_mark
        self.comp_label: str = ConfigBasic.spacy_comp_label
        self.comp_mention_label: str = ConfigBasic.spacy_comp_mention_label
        self.token_matcher: Matcher | None = None
        self.regex_entity_pattern: re.Pattern | None = None

    @staticmethod
    def get_ents_with_custom_extension(ents: Doc.ents) -> list[EntsWithCustExts]:
        # print('ents:', ents)
        ents_with_custom_extension: list[EntsWithCustExts] = [EntsWithCustExts(start_char=ent.start_char, end_char=ent.end_char, ent_text=ent.text, comp_name=getattr(ent._, SpacyExt.COMP_NAME.value), comp_symbol=getattr(ent._, SpacyExt.COMP_SYMBOL.value), set_in=getattr(ent._, SpacyExt.SET_IN.value)) for ent in ents if getattr(ent._, SpacyExt.COMP_NAME.value) != ConfigBasic.spacy_init_mark]
        # print('ents_with_custom_extension:', ents_with_custom_extension)
        # print('--------------------------------------------------------')
        return ents_with_custom_extension if ents_with_custom_extension else []

    @staticmethod
    def get_sentences_with_custom_extensions(processed_doc: Doc) -> list[dict]:
        sents_with_cust_ext_ents: list[dict] = []
        for doc_sent in processed_doc.sents:
            if doc_sent.ents:
                ents_with_cust_ext: list[EntsWithCustExts] = PipeFunc.get_ents_with_custom_extension(ents=doc_sent.ents)
                if ents_with_cust_ext:
                    sent_with_cust_ext_ents = {'sentence': doc_sent.text, 'entities': [asdict(ent) for ent in ents_with_cust_ext]}
                    sents_with_cust_ext_ents.append(sent_with_cust_ext_ents)
        return sents_with_cust_ext_ents

    def to_disk(self, path: Path, file_name: str = 'model_data', exclude=tuple()):
        # This will receive the directory path + /my_component
        if not path.exists():
            path.mkdir()
        if self.data is not None:
            data_path = path / file_name
            with data_path.open("w", encoding="utf8") as f:
                f.write(json.dumps(self.data))  # if self.data_2 is not None:  #     data_2_path = path / "data_2.json"  #     with data_2_path.open("w", encoding="utf8") as f2:  #         f2.write(json.dumps(self.data_2))

    def from_disk(self, path: Path, file_name: str = 'model_data', exclude=tuple()):
        # This will receive the directory path + /my_component
        if self.data is not None:
            data_path = path / file_name
            with data_path.open("r", encoding="utf8") as f:
                self.data = json.load(f)
        # if self.data_2 is not None:
        #     data_2_path = path / "data_2.json"
        #     with data_2_path.open("r", encoding="utf8") as f2:
        #         self.data_2 = json.load(f2)
        return self

    """ This function is needed to load the a_extract_conf back if the pipeline is trained, see spaCy documentation. It must 
        at least contain the parameters: 'get_examples' and 'nlp' (Language object). It won't work without it. """

    def initialize(self, get_examples=None, nlp=None, data=None):
        self.data = data  # self.data_2 = data_2

    def resolve_span_conflicts_and_set_new_ents(self, doc: Doc, matches: list[SearchMatch], set_in: SpacyComp, overwrite_own_ext: bool = True) -> Doc:
        if not matches:
            return doc
        ents = sorted(list(doc.ents), key=lambda span: span.start)
        matches = sorted(matches)
        for m in matches:
            # Note: Do start_idx and end_idx refer to word- or char-indexes ?:
            if m.idx_refer_to == IDXReferTo.WORDS:
                new_ent = Span(doc, m.start_idx, m.end_idx, label=m.label)
            elif m.idx_refer_to == IDXReferTo.CHARS:
                new_ent = doc.char_span(m.start_idx, m.end_idx, label=m.label, alignment_mode='expand')
            else:
                raise ValueError('idx_refer_to must be set to clarify whether start/end refers to word or char indexes.')
            # Note: Remove old ents that overlap with new ents:
            old_ents_shall_be_substituted: bool = True
            old_ents_to_be_removed: list[Span] = []
            if ents:
                for old_ent in ents:
                    if old_ent.start > new_ent.end or old_ent.end <= new_ent.start:
                        continue
                    else:
                        if getattr(old_ent._, SpacyExt.SET_IN.value) == self.init_mark:
                            # Note: Case1: old_ent is set by spacy's SpacyComp.NER.factory_name
                            old_ents_to_be_removed.append(old_ent)
                        elif getattr(old_ent._, SpacyExt.SET_IN.value) != self.init_mark and (new_ent.start <= old_ent.start and new_ent.end >= old_ent.end):
                            # Note: Case2: old_ent is set by OWN FUNCTION but IS FULLY WITHIN BORDERS of new_ent
                            if overwrite_own_ext:
                                old_ents_to_be_removed.append(old_ent)
                            else:
                                old_ents_shall_be_substituted = False
                                break
                        else:
                            # Note: Case3: All other cases such as: old_ent is set by own function but IS NOT within borders of new_ent, etc.
                            old_ents_shall_be_substituted = False
                            break
            # Note: Set new_ent ONLY IF ALL old_ents WERE NOT SET PREVIOUSLY BY OWN FUNCTION OR IF old_ent is fully WITHIN BORDERS of new_ent:
            if old_ents_shall_be_substituted:
                for old_ent in old_ents_to_be_removed:
                    ents.remove(old_ent)
                ents.append(new_ent)
                comp_name = m.comp_name
                symbol = m.comp_symbol
                setattr(new_ent._, SpacyExt.SET_IN.value, set_in.custom_name)
                setattr(new_ent._, SpacyExt.COMP_NAME.value, comp_name)
                setattr(new_ent._, SpacyExt.COMP_SYMBOL.value, symbol)
                PipeFunc.CUST_EXT_VAL_WAS_SET = True  # print('##### ->>>>>>>>>> resolve_span_conflicts_and_set_new_ents: PipeFunc.CUST_EXT_VAL_WAS_SET:', PipeFunc.CUST_EXT_VAL_WAS_SET)

        doc.ents = ents
        return doc


# Note: Done !
@Language.factory(name=SpacyComp.INIT_EXTENSIONS.custom_name)
class InitExtensions(PipeFunc):

    def __init__(self, nlp: Language, name: str):
        super().__init__(nlp, name)
        for ext in self.custom_extensions:
            if Span.has_extension(ext.value):
                _ = Span.remove_extension(ext.value)
            Span.set_extension(ext.value, default=self.init_mark)

    def __call__(self, doc: Doc) -> Doc:
        return doc


# Note: Done !
@Language.factory(name=SpacyComp.OWN_SENTENCIZER.custom_name)
class OwnSentencizer(PipeFunc):

    def __init__(self, nlp: Language, name: str):
        super().__init__(nlp, name)

    def __call__(self, doc: Doc) -> Doc:
        for token in doc[:-1]:
            if token.text in [':', ';']:
                doc[token.i+1].is_sent_start = False
        return doc


# Note: Done !
@Language.factory(name=SpacyComp.OWN_REGEX_SEARCH.custom_name)
class OwnRegexSearch(PipeFunc):

    def __init__(self, nlp: Language, name: str):
        super().__init__(nlp, name)
        self.regex_entity_patterns: list[re.Pattern] = SpacyInput.compile_regex_entity_patterns()
        self.comp_label: str = "OWN-REGEX"
        print('regex_entity_pattern for own_regex_search were compiled.')

    def get_space_corrected_span(self, text: str, span: tuple[int, int]) -> tuple[int, int]:
        """ Index corrected for whitespace at end of text. """
        return span[0], (span[1] - len(text) + len(text.rstrip()))

    def get_search_match_instance(self, match: re.Match):
        group_key: str = [key for key, value in match.groupdict().items() if value is not None][0]
        text = match.group(group_key)
        span = match.span()
        try:
            corected_span = self.get_space_corrected_span(text=text, span=span)
        except:
            corected_span = span
            print('Correcting span did not work!')
        symbol = SpacyInput.symbol_to_groupname_convert(group_key, do_reverse=True)
        comp_name = symbol_comp_name_dict[symbol]
        search_match: SearchMatch = SearchMatch(comp_name=comp_name, comp_symbol=symbol, text=text,  # label=ConfigBasic.spacy_comp_label,
            label=self.comp_label, start_idx=corected_span[0], end_idx=corected_span[1], idx_refer_to=IDXReferTo.CHARS)
        print('search_match in get_search_match_instance:', search_match)
        return search_match

    def get_matches_from_regex_search(self, text: str, patterns: list[re.Pattern]) -> list[SearchMatch]:
        re_matches_generator: Generator = run_re_finditer_concurrently(pattern_list=patterns, text=text)
        matches: list[re.Match] = [match for sublist in [match_list for match_list in re_matches_generator] for match in sublist]
        search_matches: list[SearchMatch] = []
        for match in matches:
            search_match = self.get_search_match_instance(match)
            search_matches.append(search_match)
        print('search_matches in get_matches_from_regex_search:', search_matches)
        return search_matches

    def __call__(self, doc: Doc) -> Doc:
        # Note: returns list of tuples: list(symbol, company name, found_text, span(start, end), span-corrected(start, end))
        matches: list[SearchMatch] = self.get_matches_from_regex_search(text=doc.text, patterns=self.regex_entity_patterns)
        # print('matches (OwnRegexSearch):', matches)
        doc = self.resolve_span_conflicts_and_set_new_ents(doc=doc, matches=matches, set_in=SpacyComp.OWN_REGEX_SEARCH)
        return doc


# Note: Done !
@Language.factory(name=SpacyComp.CHECK_SPACY_ENT_WITH_FUZZY_MATCH.custom_name)
class CheckSpacyEntWithFuzzyMatch(PipeFunc):
    """ SPAN-based: This method checks ONLY those entities found by spacy's SpacyComp.NER.factory_name who are in the
    "spacy_relevant_labels" list. It then checks - via fuzzy_match - if one of those entities matches the companies we
    are looking for. """

    def __init__(self, nlp: Language, name: str):
        super().__init__(nlp, name)
        self.comp_label: str = "FUZZY"

    def fuzzy_search_comp_name_with_and_without_legal(self, ent_text: str) -> tuple[str, str, float, int]:
        comp_name_without_legal, _ = split_company_name_to_name_and_legal(company_name=ent_text)
        if comp_name_without_legal is None:
            return '', '', 0.00, 0
        match_wo, similarity_wo, index_wo = fuzzy_search_one(text=comp_name_without_legal, choices=comp_name_list_without_legal, use_partial=False, case_sensitive=False)
        match_w, similarity_w, index_w = fuzzy_search_one(text=ent_text, choices=comp_name_list_without_legal, use_partial=False, case_sensitive=False)
        if similarity_wo > similarity_w:
            return comp_name_without_legal, match_wo, similarity_wo, index_wo
        else:
            return ent_text, match_w, similarity_w, index_w

    def __call__(self, doc: Doc) -> Doc:
        ents = list(doc.ents)
        search_matches: list[SearchMatch] = []
        for ind, ent in enumerate(ents):
            if ent.label_ in self.relevant_labels and getattr(ent._, SpacyExt.SET_IN.value) == self.init_mark:
                # Note: Try to split entity found by spacy into name and legal and match company name,
                #  else do not write to extensions:
                comp_name, match, similarity, index = self.fuzzy_search_comp_name_with_and_without_legal(ent.text)
                if comp_name:
                    if similarity > ConfigBasic.spacy_threshold_fuzzy_search:
                        search_match = SearchMatch(comp_name=comp_name_symbol_list[index][0], comp_symbol=comp_name_symbol_list[index][1], text=match,  # label=ConfigBasic.spacy_comp_label,
                            label=self.comp_label, start_idx=ent.start, end_idx=ent.end, idx_refer_to=IDXReferTo.WORDS)
                        search_matches.append(search_match)
        doc = self.resolve_span_conflicts_and_set_new_ents(doc=doc, matches=search_matches, set_in=SpacyComp.CHECK_SPACY_ENT_WITH_FUZZY_MATCH)
        return doc


# Note: Done !
@Language.factory(name=SpacyComp.ATTACH_ENT_ID_FROM_ENTITY_RULER_TO_CUSTOM_EXTENSION.custom_name)
class AttachEntIdValuesToCustExtension(PipeFunc):
    """ This method is currently only used by the "api_entity_ruler" to populate custom extensions with the values
     from "span.ent_id_" that are set by the "api_entity_ruler" based on matches for "entity_ruler_patterns.jsonl". """

    def __init__(self, nlp: Language, name: str):
        super().__init__(nlp, name)

    def __call__(self, doc: Doc) -> Doc:
        for ent in doc.ents:
            if ent.label_ == self.comp_label and ent.ent_id_ != self.init_mark:
                setattr(ent._, SpacyExt.SET_IN.value, SpacyComp.ATTACH_ENT_ID_FROM_ENTITY_RULER_TO_CUSTOM_EXTENSION.custom_name)
                setattr(ent._, SpacyExt.COMP_NAME.value, ent.ent_id_)
                setattr(ent._, SpacyExt.COMP_SYMBOL.value, company_names_dict.get(ent.ent_id_))
        return doc


@Language.factory(name=SpacyComp.COMP_NAME_TOKEN_REGEX_MATCH.custom_name)
class CompNameTokenRegexMatch(PipeFunc):
    """ TOKEN-based: This method checks tokens via regex token_matcher_patterns. If a match is found,
     the self.comp_mention_label is attached to the custom extension. Example: token "BMW-Vorstand". """

    def __init__(self, nlp: Language, name: str):
        super().__init__(nlp, name)
        self.comp_label: str = "ORG-PART"
        """ Add entity_token_matcher_patterns to search for from JSONL-file. """
        self.token_matcher: Matcher = Matcher(vocab=nlp.vocab, validate=True)
        with open(file=ConfigBasic.path_to_entity_token_matcher_patterns, encoding='utf-8') as token_file:
            for line in token_file:
                token_pattern_dict = json.loads(line)
                key = next(iter(token_pattern_dict.keys()))
                pattern = next(iter(token_pattern_dict.values()))
                self.token_matcher.add(key=key, patterns=pattern)
        print('Added patterns to token_matcher')

    def __call__(self, doc: Doc) -> Doc:
        matches: list[SearchMatch] = [SearchMatch(comp_name=self.nlp.vocab.strings[match_id], comp_symbol=company_names_dict.get(self.nlp.vocab.strings[match_id]), text=doc[start:end].text,  # label=[ent.label_ for ent in doc[start:end].ents][0] if doc[
            #                                                         start:end].ents else self.comp_mention_label,
            label=self.comp_label, start_idx=start, end_idx=end, idx_refer_to=IDXReferTo.WORDS) for match_id, start, end in self.token_matcher(doc)]
        # print('matches (CompNameTokenRegexMatch):', matches)
        doc = self.resolve_span_conflicts_and_set_new_ents(doc=doc, matches=matches, set_in=SpacyComp.COMP_NAME_TOKEN_REGEX_MATCH)
        return doc


# Note: Done !
@Language.factory(name=SpacyComp.XX_COREF_RESOLVE.custom_name)
class XXCorefResolve(PipeFunc):
    """ crosslingual-coreference package had some dependency issues with other Python packages in this project.
    So it is run in a docker container "ghcr.io/rainergo/img-xx-coref" with host = localhost and port = 80.
    The container returns the doc._.coref_cluster which is a: list[list[list[int]]] with char start and end position of cluster items in doc.
     Depending on the language (either: en or de), either "de_core_news_lg" or "en_core_web_lg" from spacy is used there. """

    def __init__(self, nlp: Language, name: str, natural_language: NaturalLanguage):
        super().__init__(nlp, name)
        self.comp_label: str = "XX-COREF"
        match natural_language:
            case NaturalLanguage.DE:
                self.docker_container_url: str = 'http://127.0.0.1:80/de'
            case NaturalLanguage.EN:
                self.docker_container_url: str = 'http://127.0.0.1:80/en'
        self.excluded_coreferences: list[str] = ["er", "unserer", "uns", "unsere", "wir", "unseren", "unser"]

    def _is_valid_coreference(self, comp_start_char: int, comp_end_char: int, cluster: list[list[int]], doc: Doc, coref_max_words: int = 6) -> bool:
        """ Only if the head of the cluster is already (partly) tagged with a custom extension, the coreferences get tagged as well. """
        head = cluster[0]
        head_start = head[0]
        head_end = head[1]
        head_text_words: list[str] = doc.text[head_start:head_end].split()
        condition_1 = (head_end <= comp_start_char or head_start >= comp_end_char)
        condition_2 = (len(head_text_words) > coref_max_words)
        if condition_1 or condition_2:
            return False
        else:
            return True  # for cluster_item in cluster:  #     cl_item_start = cluster_item[0]  #     cl_item_end = cluster_item[1]  #     if cl_item_end <= comp_start_char or cl_item_start >= comp_end_char:  #         continue  #     else:  #         return True  # return False

    def show_cluster(self, coref_clusters: list[list[list[int]]], doc: Doc):
        print('XX_COREF coref_clusters:', coref_clusters)
        for cluster in coref_clusters:
            cluster_dict: dict = dict()
            for ind, cluster_item in enumerate(cluster):
                cl_item_start_char = cluster_item[0]
                cl_item_end_char = cluster_item[1]
                cl_item_text = doc.text[cl_item_start_char:cl_item_end_char]
                if ind == 0:
                    cluster_dict['head'] = (cl_item_start_char, cl_item_end_char, cl_item_text)
                else:
                    cluster_dict[ind] = (cl_item_start_char, cl_item_end_char, cl_item_text)
            print('cluster_dict:', cluster_dict)

    def spread_comp_ext_to_coref_cluster_spans(self, coref_clusters: list[list[list[int]]], doc: Doc):
        search_matches: list[SearchMatch] = []
        for ent in doc.ents:
            if (comp_name := getattr(ent._, SpacyExt.COMP_NAME.value)) != self.init_mark:
                comp_symbol = getattr(ent._, SpacyExt.COMP_SYMBOL.value)
                comp_start_char: int = ent.start_char
                comp_end_char: int = ent.end_char
                for cluster in coref_clusters:
                    cluster_has_overlap = self._is_valid_coreference(comp_start_char=comp_start_char, comp_end_char=comp_end_char, cluster=cluster, doc=doc)
                    if cluster_has_overlap:
                        for cluster_item in cluster:
                            cl_item_start_char = cluster_item[0]
                            cl_item_end_char = cluster_item[1]
                            cl_item_text = doc.text[cl_item_start_char:cl_item_end_char]
                            # Note: exclude conditions here
                            cl_item_is_excluded: list = [term for term in self.excluded_coreferences if term.lower() in cl_item_text.lower().split()]
                            if not cl_item_is_excluded:
                                search_match: SearchMatch = SearchMatch(comp_name=comp_name, comp_symbol=comp_symbol, text=cl_item_text, label=self.comp_label, start_idx=cl_item_start_char, end_idx=cl_item_end_char, idx_refer_to=IDXReferTo.CHARS)
                                search_matches.append(search_match)
            else:
                continue
        return search_matches

    def __call__(self, doc: Doc) -> Doc:
        # print('container_url:', self.container_url)
        # print('##### ->>>>>>>>>> COREF: PipeFunc.CUST_EXT_VAL_WAS_SET:', PipeFunc.CUST_EXT_VAL_WAS_SET)
        # Note: Only if custom extensions have been set before, coreference resolution shall proceed:
        if PipeFunc.CUST_EXT_VAL_WAS_SET:
            text = doc.text
            request_params: dict = {"text": text}
            resp = requests.get(url=self.docker_container_url, params=request_params)
            if resp.ok and (coref_clusters := resp.json()) is not None:
                ##### DEBUG #######
                self.show_cluster(coref_clusters=coref_clusters, doc=doc)
                ###################
                matches = self.spread_comp_ext_to_coref_cluster_spans(coref_clusters=coref_clusters, doc=doc)
                doc = self.resolve_span_conflicts_and_set_new_ents(doc=doc, matches=matches, set_in=SpacyComp.XX_COREF_RESOLVE, overwrite_own_ext=False)
            # Note: CUST_EXT_VAL_WAS_SET must be set back for the next text to be processed:
            PipeFunc.CUST_EXT_VAL_WAS_SET = False
        return doc


# ToDo: Do this:
@Language.factory(name=SpacyComp.LLM_COREF_RESOLVE.custom_name)
class LLMCorefResolve(PipeFunc):
    """ Get coreference from a Generative LLM model run in a docker container (due to dependency issues).
    So it is run in a docker container "ghcr.io/rainergo/img-llm-extract-coref" with host = localhost and port = 12345
    that is created in the project: LLM-Extract.
    The container returns Cluster instance (see: data_models.py) which is a dictionary with:
    cluster_id, text, cluster_head (a ClusterHead instance), coreferences (a list of Coreference instances). """

    def __init__(self, nlp: Language, name: str):
        super().__init__(nlp, name)
        self.docker_container_url: str = 'http://127.0.0.1:12345'
        self.comp_label: str = "LLM-COREF"

    def _get_cluster_heads(self, doc: Doc) -> list[EntsWithCustExts]:
        """ For all entities that have a custom extension, some of them have the same comp_name and/or comp_symbol.
         Here we need to determine which of them is the cluster head to avoid sending duplicate company names to the LangChain LLM.
          The cluster head is the first of duplicate mentions of a company name and duplicates are removed by the set function. """
        ents_with_cust_exts: list[EntsWithCustExts] = PipeFunc.get_ents_with_custom_extension(ents=doc.ents)
        print('#########################')
        print('ents_with_cust_exts:', ents_with_cust_exts)
        print('############################')
        unique_ents_with_cust_exts: list[EntsWithCustExts] = list(set(ents_with_cust_exts))
        return unique_ents_with_cust_exts

    def create_data_container_of_clusters(self, doc: Doc) -> tuple[DataContainer, list[EntsWithCustExts]]:
        unique_ents_with_cust_exts: list[EntsWithCustExts] = self._get_cluster_heads(doc=doc)
        container = DataContainer()
        container.data_list = [Cluster(cluster_id=ind, text=doc.text, cluster_head=ClusterHead(head_text=ent.ent_text, head_index_start=ent.start_char, head_index_end=ent.end_char)) for ind, ent in enumerate(unique_ents_with_cust_exts)]
        return container, unique_ents_with_cust_exts

    def convert_llm_response_to_matches(self, llm_response: list[dict], unique_ents_with_cust_exts: list[EntsWithCustExts]):
        """ Unfortunately, Generative LLMs do not extract substring indices for their extractions well. So this must be done here. """
        matches: list[SearchMatch] = []
        for cluster, unique_ent in zip(llm_response, unique_ents_with_cust_exts):
            try:
                text: str = cluster['text']
                coreferences: list[dict] = cluster['coreferences']
                for coref in coreferences:
                    coref_with_surroundings: str = coref['coref_with_surroundings']
                    coref_text: str = coref['coref_text']
                    pattern_outer: str = rf"(?:{re.escape(coref_with_surroundings)})"
                    pattern_inner: str = rf"(?:{re.escape(coref_text)})"
                    for m_outer in list(re.finditer(pattern_outer, text)):
                        if m_outer:
                            text_outer: str = m_outer.group(0)
                            start_outer: int = m_outer.start()
                            m_inner: list[re.Match] = list(re.finditer(pattern=pattern_inner, string=text_outer))
                            if m_inner:
                                start_inner = m_inner[0].start()
                                end_inner = m_inner[0].end()
                                start = start_outer + start_inner
                                end = start_outer + end_inner
                                search_match: SearchMatch = SearchMatch(comp_name=unique_ent.comp_name, comp_symbol=unique_ent.comp_symbol, text=coref_text, label=self.comp_label, start_idx=start, end_idx=end, idx_refer_to=IDXReferTo.CHARS)
                                matches.append(search_match)
            except:
                # ToDo: Logger
                print(exc_info_formatter(msg='convert_llm_response_to_matches failed.'))
        print('matches in convert_llm_response_to_matches:', matches)
        return matches

    def __call__(self, doc: Doc) -> Doc:
        # Note: Only if custom extensions have been set before, coreference resolution shall proceed:
        if PipeFunc.CUST_EXT_VAL_WAS_SET:
            data_container, unique_ents_with_cust_exts = self.create_data_container_of_clusters(doc=doc)
            try:
                llm_response = requests.post(url=self.docker_container_url, json=data_container.dict())
            except:
                llm_response = None
                print(exc_info_formatter(msg='url post request failed.'))
            if llm_response and llm_response.ok and isinstance((cluster_list := llm_response.json()), list):
                matches: list[SearchMatch] = self.convert_llm_response_to_matches(llm_response=cluster_list, unique_ents_with_cust_exts=unique_ents_with_cust_exts)
            else:
                matches: list[SearchMatch] = []
            doc = self.resolve_span_conflicts_and_set_new_ents(doc=doc, matches=matches, set_in=SpacyComp.LLM_COREF_RESOLVE, overwrite_own_ext=False)
            # Note: CUST_EXT_VAL_WAS_SET must be set back for the next text to be processed:
            PipeFunc.CUST_EXT_VAL_WAS_SET = False

        return doc


# # Note: Done !
# @Language.factory(name=SpacyComp.ATTACH_EXT_TO_ENT.cust_name)
# class AttachExtToEnt(PipeFunc):
#     """ spaCy requires that the __init__() of a custom class to build a custom pipe component must always get
#         passed (at least): nlp (Language object), name (string) of component. It won't work without these two. """
#
#     def __init__(self, nlp: Language, name: str):
#         super().__init__()
#
#     def __call__(self, doc: Doc) -> Doc:
#         ents = list(doc.ents)
#         print('self.relevant_entity_labels', self.relevant_entity_labels)
#         for ind, ent in enumerate(ents):
#             """Attach entity span to first token of entity"""
#             if ent.label_ in self.relevant_entity_labels:
#                 match, similarity, index = fuzzy_search_one(text=ent.text, choices=comp_name_list)
#                 if similarity > ConfigBasic.threshold_fuzzy_search:
#                     comp_name, comp_symbol = comp_name_symbol_list[index][0], comp_name_symbol_list[index][1]
#                     setattr(ent._, SpacyExt.DOMAIN.ext_name, SpacyExt.COMP_NAME.domain)
#                     setattr(ent._, SpacyExt.COMP_NAME.ext_name, comp_name)
#                     setattr(ent._, SpacyExt.COMP_SYMBOL.ext_name, comp_symbol)
#                     if ent.label_ != 'ORG':
#                         ent_new = Span(doc, ent.start, ent.end, label="ORG")
#                         ents[ind] = ent_new
#         doc.ents = ents
#         return doc


# @Language.factory(name=SpacyComp.ANAPHORA.custom_name)
# class Anaphora(PipeFunc):
#     """ spaCy requires that the __init__() of a custom class to build a custom pipe component must always get
#         passed (at least): nlp (Language object), name (string) of component. It won't work without these two. """
#
#     def __init__(self, nlp: Language, name: str):
#         super().__init__(nlp, name)
#
#     def __call__(self, doc: Doc) -> Doc:
#         """ 'coref_chains' is a token extension set, instantiated and learned by the package 'coreferee'
#         which must be installed by 'python3 -m pip install coreferee' and 'python3 -m coreferee install en'.
#         Please see above and in: https://github.com/richardpaulhudson/coreferee
#         Without the installation of the package, this custom pipe component will not work.
#         In later spaCy versions (>3.5), this won't be necessary anymore as they plan to integrate it.
#         Anaphora resolution of entities. For instance, 'it' in: 'BMW made a profit. It earned Eur 1000 Mio.' """
#
#         if doc._.coref_chains:
#             pass
#     for chain in doc._.coref_chains:
#         root_name = ''
#         comp_name = ''
#         root_ent_label = ''
#         """ Unfortunately, every single coref index in a chain (span) is packed into a list,
#             thus convert it to an integer by traversing over it: """
#         for chain_index_list in chain:
#             token_index = None
#             if len(chain_index_list) > 1:
#                 for chain_index in chain_index_list:
#                     if isinstance(chain_index, list):
#                         token_index = chain_index[0]
#                     else:
#                         token_index = chain_index
#             else:
#                 token_index = chain_index_list[0]
#             """ Get the token for the indexes: """
#             token = doc[token_index]
#             if token._.comp_name != '':
#                 root_name = token._.root_name
#                 comp_name = token._.comp_name
#                 root_ent_label = token._.root_ent_label
#                 """ break if first root_name of a token in the chain is found. """
#                 break
#         """ If any token in the chain has a root_name, then label ALL the tokens
#             in the chain with the root_name and the root_ent_label found above. """
#         if comp_name != '':
#             for chain_index_list in chain:
#                 index_of_token_to_be_labeled = None
#                 if len(chain_index_list) > 1:
#                     for chain_index in chain_index_list:
#                         if isinstance(chain_index, list):
#                             index_of_token_to_be_labeled = chain_index[0]
#                         else:
#                             index_of_token_to_be_labeled = chain_index
#                 else:
#                     index_of_token_to_be_labeled = chain_index_list[0]
#
#                 if index_of_token_to_be_labeled is not None:
#                     token_to_be_labeled = doc[index_of_token_to_be_labeled]
#                     token_to_be_labeled._.root_name = root_name
#                     token_to_be_labeled._.comp_name = comp_name
#                     # print(
#                     #     f'token to be labeled: "{token_to_be_labeled}" with root_name: "{root_name}" and root_ent_label: "{root_ent_label}"')
#                     token_to_be_labeled._.root_ent_label = root_ent_label
#     """ Propagate to incorrectly classified spaCy ents: """
# return PipeCompPropToMis(self.nlp, self.name)(doc)
#     return doc
# else:
#     return doc


# @Language.factory(name=SpacyComp.NORM_ENTS.custom_name)
# class PipeCompNormEntities(PipeFunc):
#     """ spaCy requires that the __init__() of a custom class to build a custom pipe component must always get
#         passed (at least): nlp (Language object), name (string) of component. It won't work without these two. """
#
#     def __init__(self, nlp: Language, name: str):
#         super().__init__(nlp, name)
#
#     def __call__(self, doc: Doc) -> Doc:
#         """ Get rid of leading articles (e.g. 'the' in 'the New York Times')
#             and trailing particles (like 's' in 'BMW's revenue') """
#         ents = []
#         for ent in doc.ents:
#             if ent[0].pos_ == "DET":  # leading article
#                 ent = Span(doc, ent.start + 1, ent.end, label=ent.label)
#             if len(ent) > 0:
#                 if ent[-1].pos_ == "PART":  # trailing particle like 's
#                     ent = Span(doc, ent.start, ent.end - 1, label=ent.label)
#                 ents.append(ent)
#         doc.ents = tuple(ents)
#         return doc


# @Language.factory(name=SpacyComp.PROP_TO_MISCLASS.custom_name)
# class PipeCompPropToMis(PipeFunc):
#     """ spaCy requires that the __init__() of a custom class to build a custom pipe component must always get
#         passed (at least): nlp (Language object), name (string) of component. It won't work without these two. """
#
#     def __init__(self, nlp: Language, name: str):
#         super().__init__()
#
#     def __call__(self, doc: Doc) -> Doc:
#         """ Propagate the new label to mis-classfied labels.
#             This component is used by ALIAS_RESOLVE, NAME_RESOLVE, ANAPHORA """
#         ents = []
#         for ent in doc.ents:
#             if ent[0]._.comp_name != '':  # if ent does not yet have a comp_name-tag
#                 ent = Span(doc, ent.start, ent.end, label=ent[0]._.root_ent_label)
#             ents.append(ent)
#         doc.ents = tuple(ents)
#         return doc


# @Language.factory(name=SpacyComp.ALIAS_RESOLVE.custom_name)
# class AliasResolve(PipeFunc):
#     """ spaCy requires that the __init__() of a custom class to build a custom pipe component must always get
#         passed (at least): nlp (Language object), name (string) of component. It won't work without these two. """
#
#     def __init__(self, nlp: Language, name: str, alias_dict: dict):
#         super().__init__(data=alias_dict)
#         self.nlp = nlp
#         self.name = name
#         self.alias_dict = alias_dict
#
#     def __call__(self, doc: Doc) -> Doc:
#         """ Maps and attaches alias names from the alias_dict to the token extension 'root_name' """
#         for ent in doc.ents:
#             entity_name_in_text = ent[0].text
#             if entity_name_in_text in self.alias_dict:
#                 root_name, comp_name, root_ent_label = self.alias_dict[entity_name_in_text]
#                 ent[0]._.root_name = str(
#                     root_name)  # necessary if root_name is type int such as VBKENN (cast does not help)
#                 ent[0]._.comp_name = comp_name
#                 ent[0]._.root_ent_label = root_ent_label
#
#         """ Propagate to incorrectly classified spaCy ents: """
#         return PipeCompPropToMis(self.nlp, self.name)(doc)


# @Language.factory(name=SpacyComp.NAME_RESOLVE.custom_name)
# class PipeCompNameResolve(PipeFunc):
#     """ spaCy requires that the __init__() of a custom class to build a custom pipe component must always get
#         passed (at least): nlp (Language object), name (string) of component. It won't work without these two. """
#
#     def __init__(self, nlp: Language, name: str):
#         super().__init__()
#         self.nlp = nlp
#         self.name = name
#
#     def __call__(self, doc: Doc) -> Doc:
#         """ Reference second mention of entity in sentence to first mention, e.g. BMW AG (first) -> BMW (second)."""
#         ents = [ent for ent in doc.ents if ent.label_ in self.relevant_labels]
#         for index, first_ent in enumerate(ents):
#             for second_ent in ents[index + 1:]:
#                 if self.name_match(first=first_ent[0]._.comp_name, second=second_ent[0].text):
#                     # print(f'first={first_ent[0]._.root_name}, second={second_ent[0].text}')
#                     second_ent[0]._.root_name = first_ent[0]._.root_name
#                     second_ent[0]._.comp_name = first_ent[0]._.comp_name
#                     second_ent[0]._.root_ent_label = first_ent[0]._.root_ent_label
#         """ Propagate to incorrectly classified spaCy ents: """
#         return PipeCompPropToMis(self.nlp, self.name)(doc)

# def name_match(self, first: str, second: str):
#     """ Search for entities mentioned first in an article to references mentioned
#     thereafter but with a shorter reference name: BMW AG (first) -> BMW (second). """
#     second = re.sub('[+\**\*&\*#\*^\*!\*~\*`\*´\*?\*%\*§\*°\*]', ' ', second)  # added to avoid errors
#     second = re.sub(r'[()\.]', '', second)  # ignore parentheses and dots
#     second = r'\b' + second + r'\b'  # \b marks word boundary
#     second = re.sub(r'\s' + re.escape('+'), r'\\b.*\\b', second)
#     # second = re.sub(r'\s'+re.escape('+'), r'\\b.'+re.escape('*')+r'\\b', second)
#     return re.search(second, first, flags=re.I) is not None


# @Language.factory(name=SpacyComp.TO_SPACY_ENT.custom_name)
# class PipeCompRootEntToEnt(PipeFunc):
#     """ spaCy requires that the __init__() of a custom class to build a custom pipe component must always get
#         passed (at least): nlp (Language object), name (string) of component. It won't work without these two. """
#
#     def __init__(self, nlp: Language, name: str):
#         super().__init__()
#
#     def __call__(self, doc: Doc) -> Doc:
#         """ At the end of the entire pipeline, propagate the 'root_ent_label' to spaCy's 'ent' so that it can be
#             found in the 'doc.ents' and can also be visualized by 'spacy.displacy' """
#         new_entities = []
#         entities = doc.ents  # tuple
#         end = -1  # Important: Avoids that newly added entities span overlap
#         for doc_index, token in enumerate(doc):
#             if end >= doc_index:  # Important: Avoids that newly added entities span overlap
#                 continue
#             if token._.comp_name != '' and token.ent_iob_ in ["O", ""]:  # ""=No entity tag, "O"=Outside entity
#                 start = token.i
#                 end = self.get_root_ent_label_end_index(len_doc=doc.__len__(), token=token)
#                 new_entities.append(Span(doc, start, end + 1, label=token._.root_ent_label))
#         doc.ents = tuple(entities) + tuple(new_entities)
#         return doc

# def get_root_ent_label_end_index(self, len_doc: int, token: Token) -> int:
#     """ If 'root_name' of this token is equal to the 'root_name' of the next token, then recurse until
#     last index of 'root_name'-chain is found. Index of this last token in doc will be returned to build ent-Span."""
#     if (token.i == (len_doc - 1)) or (token.nbor()._.comp_name != token._.comp_name) or (
#             token.nbor().ent_iob_ not in ["O", ""]):
#         return token.i
#     else:
#         return self.get_root_ent_label_end_index(len_doc=len_doc, token=token.nbor())


if __name__ == '__main__':
    pass
