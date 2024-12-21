import warnings

import pandas as pd
import spacy
from spacy.language import Language

from src.settings.config import ConfigBasic
from src.settings.enums import NaturalLanguage, SpacyTask, SpacyComp, ExtractionType

pd.set_option('display.max_columns', 50)
warnings.filterwarnings("ignore")


class SpacyPipeBuild:
    # Note: Custom funcs must be imported:
    # noinspection PyUnresolvedReferences
    from src.B_spacy_pipeline import spacy_pipe_funcs
    # noinspection PyUnresolvedReferences
    from gliner_spacy.pipeline import GlinerSpacy

    def __init__(self, natural_language: NaturalLanguage, spacy_task: SpacyTask, ner_method: ExtractionType = ExtractionType.PRETRAINED,
            coref_method: ExtractionType = ExtractionType.PRETRAINED, use_gpu: bool = True):
        self.natural_language = natural_language
        self.spacy_task = spacy_task
        self.ner_method = ner_method
        self.coref_method = coref_method
        self.use_gpu = use_gpu
        self.entity_ruler = None
        self.default_pipe_components: list | None = None
        self.nlp, self.vectorizer = self.set_nlp(natural_language=natural_language, spacy_task=spacy_task)
        self.build_pipe()

    def set_nlp(self, natural_language: NaturalLanguage, spacy_task: SpacyTask) -> tuple[Language, SpacyComp]:
        if self.use_gpu:
            spacy.require_gpu()
            print('GPU is used:', spacy.prefer_gpu())  # ToDo: Logging here
        else:
            print('CPU is used!')  # ToDo: Logging here
        nlp = None
        vectorizer = None
        match natural_language, spacy_task:
            # Note: Currently neither NER nor COREF can be run on German trf-models but this might change in the future.
            #  Change here then:
            case NaturalLanguage.DE, SpacyTask.NER | SpacyTask.COREF | SpacyTask.ALL | SpacyTask.POS:
                nlp = spacy.load('de_core_news_lg')
                self.default_pipe_components = [SpacyComp.TOK2VEC, SpacyComp.TAGGER, SpacyComp.MORPHOLOGIZER, SpacyComp.PARSER, SpacyComp.LEMMATIZER, SpacyComp.SENTER, SpacyComp.ATTRIBUTE_RULER, SpacyComp.NER]
                vectorizer = SpacyComp.TOK2VEC
            case NaturalLanguage.EN, SpacyTask.NER | SpacyTask.COREF | SpacyTask.ALL | SpacyTask.POS:
                nlp = spacy.load('en_core_web_trf')
                self.default_pipe_components = [SpacyComp.TRANSFORMER, SpacyComp.TAGGER, SpacyComp.PARSER, SpacyComp.ATTRIBUTE_RULER, SpacyComp.LEMMATIZER, SpacyComp.NER]
                vectorizer = SpacyComp.TRANSFORMER
            case NaturalLanguage.DE, SpacyTask.BASIC:
                self.default_pipe_components = [SpacyComp.TOK2VEC, SpacyComp.TAGGER, SpacyComp.MORPHOLOGIZER, SpacyComp.PARSER, SpacyComp.LEMMATIZER]
                nlp = spacy.load('de_core_news_lg', enable=[comp.factory_name for comp in self.default_pipe_components])
                vectorizer = SpacyComp.TOK2VEC
            case NaturalLanguage.EN, SpacyTask.BASIC:
                self.default_pipe_components = [SpacyComp.TRANSFORMER, SpacyComp.TAGGER, SpacyComp.PARSER, SpacyComp.LEMMATIZER]
                nlp = spacy.load('en_core_web_trf', enable=[comp.factory_name for comp in self.default_pipe_components])
                vectorizer = SpacyComp.TRANSFORMER
            case _, _:
                raise ValueError(f'spaCy model for Natural language "{natural_language}" and task "{spacy_task}" could not be loaded.')
        return nlp, vectorizer

    def build_pipe(self):
        if self.spacy_task != SpacyTask.BASIC:
            self.func_init_extensions()
        match self.spacy_task:
            case SpacyTask.ALL:
                self.nlp.select_pipes(enable=[self.vectorizer.factory_name])
                self.api_parser()
                match self.ner_method:
                    case ExtractionType.TRADITIONAL:
                        self.func_own_regex_search()
                        # self.api_entity_ruler()
                        # self.func_comp_name_token_regex_match()
                    case ExtractionType.PRETRAINED:
                        self.api_ner()
                match self.coref_method:
                    case ExtractionType.PRETRAINED:
                        self.func_coref_resolve_pretrained()
                    case ExtractionType.GENERATIVE_LLM:
                        self.func_coref_resolve_generative()
                    case _:
                        raise ValueError('Cases other than ExtractionType.PRETRAINED and ExtractionType.GENERATIVE_LLM are not supported yet.')
                self.func_sentencizer()  # Must be in for correct sentence splitting

            case SpacyTask.COREF:
                self.nlp.select_pipes(enable=[self.vectorizer.factory_name, SpacyComp.MORPHOLOGIZER])
                self.func_own_regex_search()
                self.func_comp_name_token_regex_match()
                match self.coref_method:
                    case ExtractionType.PRETRAINED:
                        self.func_coref_resolve_pretrained()
                    case ExtractionType.GENERATIVE_LLM:
                        self.func_coref_resolve_generative()
                    case _:
                        raise ValueError('Cases other than ExtractionType.PRETRAINED and ExtractionType.GENERATIVE_LLM are not supported yet.')

            case SpacyTask.NER:
                match self.ner_method:
                    case ExtractionType.TRADITIONAL:
                        self.nlp.select_pipes(enable=[self.vectorizer.factory_name, SpacyComp.MORPHOLOGIZER])
                        # self.api_parser()
                        self.func_own_regex_search()
                        # self.api_entity_ruler()
                        self.func_comp_name_token_regex_match()
                        # self.func_check_spacy_ent_with_fuzzy_match()
                    case ExtractionType.PRETRAINED:
                        self.nlp.select_pipes(enable=[self.vectorizer.factory_name])
                        self.api_gliner()
                    case ExtractionType.GENERATIVE_LLM:
                        pass
                self.func_sentencizer()  # Must be in for correct sentence splitting

            case SpacyTask.POS:
                self.nlp.select_pipes(enable=[self.vectorizer.factory_name, SpacyComp.MORPHOLOGIZER.factory_name, SpacyComp.PARSER.factory_name, ])
                self.func_sentencizer()  # Must be in for correct sentence splitting

    def func_sentencizer(self, spacy_comp: SpacyComp = SpacyComp.OWN_SENTENCIZER):
        try:
            if self.nlp.has_pipe(spacy_comp.custom_name):
                self.nlp.remove_pipe(spacy_comp.custom_name)
            # Note: custom_sentencizer must come first, according to this: https://github.com/explosion/spaCy/discussions/6963
            self.nlp.add_pipe(spacy_comp.custom_name, first=True)
            print(f'custom extensions "{spacy_comp.custom_name}" initialized')
        except Exception as e:
            print(f'custom extensions not initialized: {e}')

    def func_init_extensions(self, spacy_comp: SpacyComp = SpacyComp.INIT_EXTENSIONS):
        """ Initialize spacy token extensions """
        try:
            if self.nlp.has_pipe(spacy_comp.custom_name):
                self.nlp.remove_pipe(spacy_comp.custom_name)
            self.nlp.add_pipe(spacy_comp.custom_name)
            print(f'custom extensions "{spacy_comp.custom_name}" initialized')
        except Exception as e:
            print(f'custom extensions not initialized: {e}')

    def api_ner(self, spacy_comp: SpacyComp = SpacyComp.NER):
        if spacy_comp.factory_name in self.nlp.disabled:
            self.nlp.enable_pipe(name=spacy_comp.factory_name)
        else:
            if self.nlp.has_pipe(spacy_comp.custom_name):
                print('api ner has pipe ner')
                self.nlp.remove_pipe(spacy_comp.custom_name)
            self.nlp.add_pipe(spacy_comp.custom_name)
        print(f'Built-In "NER" initialized')

    def api_gliner(self, spacy_comp: SpacyComp = SpacyComp.GLINER):
        config = {"labels": ["organization"], "gliner_model": "urchade/gliner_multi"}
        if spacy_comp.factory_name in self.nlp.disabled:
            self.nlp.enable_pipe(name=spacy_comp.factory_name)
        else:
            if self.nlp.has_pipe(spacy_comp.custom_name):
                print('api gliner already has pipe gliner')
                self.nlp.remove_pipe(spacy_comp.custom_name)
            self.nlp.add_pipe(spacy_comp.custom_name, config=config)
        print(f'"GLINER" api initialized')

    def func_check_spacy_ent_with_fuzzy_match(self, spacy_comp: SpacyComp = SpacyComp.CHECK_SPACY_ENT_WITH_FUZZY_MATCH):
        """ ToDo: Description """
        if SpacyComp.NER.factory_name not in self.nlp.pipe_names:
            print('NER api must be in pipeline for func_check_spacy_ent_with_fuzzy_match to work. Will be added now!')
            self.api_ner()
        if self.nlp.has_pipe(spacy_comp.custom_name):
            self.nlp.remove_pipe(spacy_comp.custom_name)
        self.nlp.add_pipe(spacy_comp.custom_name)
        print(f'Function "func_check_spacy_ent_with_fuzzy_match" initialized')

    def api_parser(self, spacy_comp: SpacyComp = SpacyComp.PARSER):
        if spacy_comp.factory_name in self.nlp.disabled:
            self.nlp.enable_pipe(name=spacy_comp.factory_name)
        else:
            if self.nlp.has_pipe(spacy_comp.custom_name):
                self.nlp.remove_pipe(spacy_comp.custom_name)
            self.nlp.add_pipe(spacy_comp.custom_name)
        print(f'Built-In "PARSER" initialized')

    def api_senter(self, spacy_comp: SpacyComp = SpacyComp.SENTER):
        if spacy_comp.factory_name in self.nlp.disabled and spacy_comp in self.default_pipe_components:
            self.nlp.enable_pipe(name=spacy_comp.factory_name)
        elif self.vectorizer == SpacyComp.TRANSFORMER:
            print('INFO: TRANSFORMER pipelines need the parser for sentence-related tasks. Thus, the parser component will be set now.')
            self.api_parser()
        else:
            if self.nlp.has_pipe(spacy_comp.custom_name):
                self.nlp.remove_pipe(spacy_comp.custom_name)
            self.nlp.add_pipe(spacy_comp.custom_name)
        print(f'Built-In "SENTER" initialized')

    def func_own_regex_search(self, spacy_comp: SpacyComp = SpacyComp.OWN_REGEX_SEARCH):
        if self.nlp.has_pipe(spacy_comp.custom_name):
            self.nlp.remove_pipe(spacy_comp.custom_name)
        self.nlp.add_pipe(spacy_comp.custom_name)
        print(f'Function "own_regex_search" initialized')

    def func_coref_resolve_generative(self, spacy_comp: SpacyComp = SpacyComp.LLM_COREF_RESOLVE):
        if self.nlp.has_pipe(spacy_comp.custom_name):
            self.nlp.remove_pipe(spacy_comp.custom_name)
        self.nlp.add_pipe(spacy_comp.custom_name)
        print(f'Function "own_coref_resolve_generative" initialized')

    def func_coref_resolve_pretrained(self, spacy_comp: SpacyComp = SpacyComp.XX_COREF_RESOLVE):
        if self.nlp.has_pipe(spacy_comp.custom_name):
            self.nlp.remove_pipe(spacy_comp.custom_name)
        config = {"natural_language": self.natural_language}
        self.nlp.add_pipe(spacy_comp.custom_name, config=config)
        print(f'Function "own_coref_resolve_pretrained" initialized')

    def func_comp_name_token_regex_match(self, spacy_comp: SpacyComp = SpacyComp.COMP_NAME_TOKEN_REGEX_MATCH):
        """ ToDo: Description """
        # if (SpacyComp.MORPHOLOGIZER.factory_name not in self.nlp.pipe_names or
        #         SpacyComp.PARSER.factory_name not in self.nlp.pipe_names):
        #     raise ValueError('MORPHOLOGIZER and PARSER apis must be in pipeline for func_comp_name_token_regex_match to work !')
        if self.nlp.has_pipe(spacy_comp.custom_name):
            self.nlp.remove_pipe(spacy_comp.custom_name)
        self.nlp.add_pipe(spacy_comp.custom_name)
        print(f'Function "func_comp_name_token_regex_match" initialized')

    def api_entity_ruler(self, spacy_comp: SpacyComp = SpacyComp.ENTITY_RULER):
        """ Create entity_specialchar_ruler api ('EntityRuler', see: https://spacy.io/usage/rule-based-matching#entityruler)
                    and add patterns from SpacyInput instance ('entity_patterns' and 'alias_dict'):
                    Multiple EntiyRuler-Instances are allowed, but only the name must differ!
                    """
        if self.nlp.has_pipe(spacy_comp.custom_name):
            self.nlp.remove_pipe(spacy_comp.custom_name)
        config = {"overwrite_ents": False, "validate": True}
        self.entity_ruler = self.nlp.add_pipe(factory_name=spacy_comp.factory_name, name=spacy_comp.custom_name, last=True, config=config)
        # Note: The entity_ruler tries to match patterns from "entity_ruler_patterns.jsonl". If a match occurs,
        #  it attaches the pattern_key (company name) to the "span.ent_id_"-extension:
        self.entity_ruler.from_disk(ConfigBasic.path_to_entity_ruler_patterns)
        print('Patterns for "Entity-Ruler loaded from file."')

        # Note: Now that the company names are attached to the Spacy default "span.ent_id_"-extension, they also must be attached
        #   to the custom extensions. This should only be done once, i.e. if other functions attach company names
        #   to the "span.ent_id_"-extension, then run "self._func_attach_custom_extension_to_spacy_orgs()" at the end:
        self._func_attach_custom_extension_to_spacy_orgs()
        print(f'Built-In "Entity-Ruler" initialized')

    def _func_attach_custom_extension_to_spacy_orgs(self, spacy_comp: SpacyComp = SpacyComp.ATTACH_ENT_ID_FROM_ENTITY_RULER_TO_CUSTOM_EXTENSION):
        """ Attach custom extensions to already existing entity labels if entity is in fuzzy_searched companies """
        if self.nlp.has_pipe(spacy_comp.custom_name):
            self.nlp.remove_pipe(spacy_comp.custom_name)
        self.nlp.add_pipe(spacy_comp.custom_name)

    def api_coreference(self, spacy_comp: SpacyComp = SpacyComp.COREFEREE):
        """ Python package 'coreferee' (pip installation, see above) that in later spaCy versions (>3.5) will be
                   replaced by spaCy's proprietary CoreferenceResolver API (see: https://spacy.io/api/coref).
                    Here it must be used like a spaCy Language.component, i.e. just by: 'add_pipe(name_of_package)'
                    The package attaches the extension 'coref_chains' to those tokens where it finds co-references. """
        try:
            if self.nlp.has_pipe(spacy_comp.factory_name):
                self.nlp.remove_pipe(spacy_comp.factory_name)
            self.nlp.add_pipe(spacy_comp.factory_name)
            print(f'Api "{spacy_comp.custom_name}" initialized')
            self._func_anaphora()
        except:
            print(f'spacy api "{spacy_comp.custom_name}" could not be initialized!')

    def _func_anaphora(self, spacy_comp: SpacyComp = SpacyComp.ANAPHORA):
        """ Anaphora resolution of entities. For instance, 'it' in: 'BMW made a profit. It earned Eur 1000 Mio.' """
        try:
            if self.nlp.has_pipe(spacy_comp.custom_name):
                self.nlp.remove_pipe(spacy_comp.custom_name)
            self.nlp.add_pipe(spacy_comp.custom_name)
            print(f'spacy custom function "{spacy_comp.custom_name}" initialized')
        except:
            print(f'spacy custom function "{spacy_comp.custom_name}" could not be initialized!')

    # def save_trained_model(self, model_name_suffix: str):  #     model_custom_name = self.nlp.meta['lang'] + '_' + self.nlp.meta['name'] + '_' + self.nlp.meta[  #         'version'] + '_' + model_name_suffix  #     path = os.path.join(self.save_model_path, model_custom_name)  #     self.nlp.to_disk(path=path)  #     print('Done! New model was saved.')


if __name__ == '__main__':
    pipe = SpacyPipeBuild(natural_language=NaturalLanguage.DE, spacy_task=SpacyTask.ALL, ner_method=ExtractionType.TRADITIONAL, coref_method=ExtractionType.PRETRAINED)
    print(pipe.entity_ruler.patterns)
