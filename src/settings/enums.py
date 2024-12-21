import re
from enum import Enum, StrEnum, auto
from dataclasses import dataclass


# Enum classes
class UpperStrEnum(StrEnum):
    """ This method returns Enum.name in upper-cased letters. """

    @staticmethod
    def _generate_next_value_(name, start, count, last_values):
        return name.upper()


class Frequency(UpperStrEnum):
    YEARLY = auto()
    MONTHLY = auto()
    DAILY = auto()


@dataclass
class WebsiteVariables:
    id: str
    yaml: dict or None


@dataclass
class DateTimeFormatVariables:
    manformat: str
    pyformat: str


class DateTimeFormat(DateTimeFormatVariables, Enum):
    """ Two format types: first: manformat, second: pyformat (see: DateTimeFormatVariables) """
    yyyy_mm_dd = 'yyyy-mm-dd', '%Y-%m-%d'
    yyyy_mm_dd_hh_mm = 'yyyy-mm-dd hh:mm', '%Y-%m-%d %H:%M'
    yyyy_mm_dd_hh_mm_ss = 'yyyy-mm-dd hh:mm:ss', '%Y-%m-%d %H:%M:%S'
    yyyy_mm = 'yyyy-mm', '%Y-%m'
    dd_m_name_yyyy_hh_mm = 'dd m_name yyyy hh:mm', '%d %B %Y %H:%M'
    dd_mm_yyyy_hh_mm_1 = 'dd mm yyyy hh:mm', '%d %m %Y %H:%M'
    dd_mm_yyyy_hh_mm_2 = 'dd-mm-yyyy hh:mm', '%d-%m-%Y %H:%M'
    dd_mm_hh_mm = 'dd.mm. hh:mm', '%d.%m. %H:%M'
    yyyy = 'yyyy', '%Y'


class BuiltInsByName(StrEnum):
    MAX = 'max'
    MIN = 'min'


# Note: NOT YET IN A_NLP:
@dataclass
class SpacyCompVariables:
    # Note: factory is factory_name of spaCy (fixed), name is custom name (arbitrary)
    factory_name: str
    custom_name: str


class SpacyTask(Enum):
    ALL = 'all'
    COREF = 'coref'
    NER = 'ner'
    POS = 'pos'
    BASIC = 'basic'


class SpacyComp(SpacyCompVariables, Enum):
    # Note: Base components:
    TOK2VEC = 'tok2vec', 'tok2vec'
    TRANSFORMER = 'transformer', 'transformer'
    TAGGER = 'tagger', 'tagger'
    MORPHOLOGIZER = 'morphologizer', 'morphologizer'
    PARSER = 'parser', 'parser'
    LEMMATIZER = 'lemmatizer', 'lemmatizer'
    ATTRIBUTE_RULER = 'attribute-ruler', 'attribute-ruler'
    SENTER = 'senter', 'senter'  # part of all trained pipelines

    # Note: Extra spaCy components
    NER = 'ner', 'ner'
    GLINER = 'gliner_spacy', 'gliner_spacy'
    ENTITY_RULER = 'entity_ruler', 'entity_ruler'
    MERGE_ENTS = 'merge_entities', 'merge_entities'
    COREFEREE = 'coreferee', 'coreferee'
    XX_COREF = 'xx_coref', 'xx_coref'

    # Note: Extra custom component functions as Language.component Decorator
    # USED:
    INIT_EXTENSIONS = '', 'init_extensions'
    OWN_REGEX_SEARCH = '', 'own_regex_search'
    OWN_SENTENCIZER = '', 'own_sentencizer'
    CHECK_SPACY_ENT_WITH_FUZZY_MATCH = '', 'check_spacy_ent_with_fuzzy_match'
    COMP_NAME_TOKEN_REGEX_MATCH = '', 'comp_name_token_regex_match'
    ATTACH_ENT_ID_FROM_ENTITY_RULER_TO_CUSTOM_EXTENSION = '', 'attach_ent_id_from_entity_ruler_to_custom_extension'
    XX_COREF_RESOLVE = 'xx_coref_resolve', 'xx_coref_resolve'
    LLM_COREF_RESOLVE = 'llm_coref_resolve', 'llm_coref_resolve'
    # NOT USED YET:
    NORM_ENTS = '', 'norm_entities'
    PROP_TO_MISCLASS = '', 'prop_to_misclass'
    ALIAS_RESOLVE = '', 'alias_resolver'
    NAME_RESOLVE = '', 'name_resolver'
    ANAPHORA = '', 'anaphora'
    TO_SPACY_ENT = '', 'to_spacy_ent'


# @dataclass
# class SpacyExtensionVariables:
#     value: str


class SpacyExt(Enum):
    """ spacy token extension like ._.comp_name """
    SET_IN = 'set_in'
    COMP_NAME = 'comp_name'
    COMP_SYMBOL = 'comp_symbol'


class IDXReferTo(Enum):
    WORDS = 'words'
    CHARS = 'chars'


class RegexFor(Enum):
    TOKEN = 'token'
    SPAN = 'span'


class ExtractionType(Enum):
    GENERATIVE_LLM = 'generative_llm'
    PRETRAINED = 'pretrained'
    TRADITIONAL = 'traditional'


class NaturalLanguage(StrEnum):
    DE = 'DE'
    EN = 'EN'


class VectorizerType(Enum):
    TFIDF = auto()
    BagOfWords = auto()
    EMBEDDING = auto()
    OneHot = auto()


class ReductionMethod(Enum):
    PCA = auto()
    KernelPCA = auto()
    SVD = auto()
    UMAP = auto()
    TSNE = auto()
    NMF = auto()
    LDA = auto()


class ClusterMethod(Enum):
    KMEANS = auto()
    MEAN_SHIFT = auto()
    HDBSCAN = auto()


if __name__ == '__main__':
    for s in SpacyExt:
        print(s.domain)
