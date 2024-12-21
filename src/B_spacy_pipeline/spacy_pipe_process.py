import re
import string
import warnings
import pandas as pd
import spacy
from spacy.attrs import ORTH
from spacy.language import Language, Tokenizer
from spacy.tokens import Doc

from src.settings.enums import NaturalLanguage, SpacyTask, SpacyExt, ExtractionType
from src.B_spacy_pipeline.spacy_pipe_build import SpacyPipeBuild
from src.G_utils.re_patterns import make_pattern_from_raw_str_iterable

pd.set_option('display.max_columns', 50)
warnings.filterwarnings("ignore")


class SpacyPipeProcess(SpacyPipeBuild):
    def __init__(self, natural_language: NaturalLanguage, spacy_task: SpacyTask, ner_method: ExtractionType = ExtractionType.PRETRAINED, coref_method: ExtractionType = ExtractionType.PRETRAINED, use_gpu: bool = True):
        super().__init__(natural_language=natural_language, spacy_task=spacy_task, use_gpu=use_gpu, ner_method=ner_method, coref_method=coref_method)

    def set_custom_tokenizer(self, special_tokens: list[str] = None, extra_prefixes: list[str] = None, extra_infixes: list[str] = None, extra_suffixes: list[str] = None):
        if special_tokens is None:
            token_match = None
        else:
            token_pattern = make_pattern_from_raw_str_iterable(raw_str_iterable=special_tokens, as_group=True)
            token_match = re.compile(pattern=token_pattern, flags=re.IGNORECASE).match
        # ToDo: Create patterns
        prefixes: list[str] = self.nlp.Defaults.prefixes if extra_prefixes is None else self.nlp.Defaults.prefixes + extra_prefixes
        infixes: list[str] = self.nlp.Defaults.infixes if extra_infixes is None else self.nlp.Defaults.infixes + extra_infixes
        suffixes: list[str] = self.nlp.Defaults.suffixes if extra_suffixes is None else self.nlp.Defaults.suffixes + extra_suffixes
        prefix_re = spacy.util.compile_prefix_regex(prefixes)
        infix_re = spacy.util.compile_infix_regex(infixes)
        suffix_re = spacy.util.compile_suffix_regex(suffixes)
        self.nlp.tokenizer = Tokenizer(vocab=self.nlp.vocab, prefix_search=prefix_re.search, infix_finditer=infix_re.finditer, suffix_search=suffix_re.search, token_match=token_match)

    def add_special_cases_to_tokenizer(self, special_cases: list[str]):
        """ All special cases are case-sensitive, i.e. "Ltd." only matches "Ltd." but not "ltd.".
         For case-insensitive cases, use "special_tokens" in "set_custom_tokenizer()". """
        for special_case in special_cases:
            special_case_list: list[dict] = [{ORTH: special_case}]
            self.nlp.tokenizer.add_special_case(special_case, special_case_list)

    def add_custom_stopwords(self, stop_words: list) -> None:
        stop_words_set = set(stop_words)
        self.nlp.Defaults.stop_words |= stop_words_set

    def split_text_to_word_list(self, text: str, use_custom_tokenizer: bool = True, return_word_separators: bool = False) -> list[str]:
        if use_custom_tokenizer:
            self.set_custom_tokenizer()
        doc = self.nlp(text)
        words_raw = [tok.text for tok in doc]
        if return_word_separators:
            words = words_raw
        else:
            words = [exp for exp in words_raw if exp not in string.punctuation]
        return words

    def show_ents(self, doc, column_val_filter: str = 'ent_type', include_punct: bool = False):
        """Generate a_extract_conf frame for visualization of spaCy doc with custom attributes."""
        rows = []
        for index, token in enumerate(doc):
            if not token.is_punct or include_punct:
                row = {'token': index, 'token_text': token.text, 'lemma': token.lemma_, 'pos': token.pos_, 'dep': token.dep_, 'ent_type': token.ent_type_, 'ent_iob_': token.ent_iob_}

                # if doc.has_extension('has_coref'):
                #     if doc._.coref_clusters is not None and \
                #             token.has_extension('in_coref') and token._.in_coref:  # neuralcoref attributes
                #         row['in_coref'] = token._.in_coref
                #         row['main_coref'] = token._.coref_clusters[0].main.text
                #     else:
                #         row['in_coref'] = None
                #         row['main_coref'] = None
                if token.has_extension(SpacyExt.COMP_NAME.value):  # referent attribute
                    row[SpacyExt.SET_IN.value] = getattr(token._, SpacyExt.SET_IN.value)
                    row[SpacyExt.COMP_NAME.value] = getattr(token._, SpacyExt.COMP_NAME.value)
                    row[SpacyExt.COMP_SYMBOL.value] = getattr(token._, SpacyExt.COMP_SYMBOL.value)
                rows.append(row)

        match column_val_filter:
            case SpacyExt.COMP_NAME.value:
                col_filter = ['token_text', 'ent_type', 'root_name', 'root_ent_label']
            case 'ent_type':
                col_filter = ['token_text', 'ent_type']
            case _:
                column_val_filter = 'ent_type'
                col_filter = ['token_text', 'lemma', 'pos', 'dep', 'ent_type', 'ent_iob_', 'root_name', 'root_ent_label']

        df = pd.DataFrame(rows).set_index('token')
        df.index.custom_name = 'token_index_in_text'
        df_filtered = df.query(f"`{column_val_filter}` != ''")[col_filter]
        return df_filtered

    def process_text(self, text: str, build_pipe: bool = False) -> spacy.tokens.Doc:
        if build_pipe:
            self.build_pipe()
        doc = self.nlp(text=text)
        return doc


if __name__ == '__main__':
    pipe = SpacyPipeBuild(natural_language=NaturalLanguage.DE, spacy_task=SpacyTask.ALL, )
    print(pipe.entity_ruler.patterns)
