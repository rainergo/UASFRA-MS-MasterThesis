import torch
import spacy
import gc

from spacy.language import Doc

# noinspection PyUnresolvedReferences
from fastcoref import spacy_component

from src.settings.enums import NaturalLanguage


class CorefResolver:

    def __init__(self, natural_language: NaturalLanguage,
                 use_trf: bool = True,
                 coref_module: str = 'fastcoref') -> None:
        self.natural_language = natural_language
        self.use_trf = use_trf
        self.coref_module = coref_module
        self.nlp: spacy.Language | None = None
        self.doc_conf: dict | None = None
        self.doc: Doc | None = None
        self.cluster_extension: str | None = None
        self.resolve_extension: str | None = None
        self.set_nlp()
        self.set_coref()

    def set_nlp(self):
        spacy.require_gpu()
        print('GPU is used:', spacy.prefer_gpu())  # ToDo: Logging here
        match self.natural_language, self.use_trf:
            case NaturalLanguage.EN, True:
                self.nlp = spacy.load('en_core_web_trf')
            case NaturalLanguage.EN, False:
                self.nlp = spacy.load('en_core_web_lg')
            case NaturalLanguage.DE, True:
                self.nlp = spacy.load('de_dep_news_trf')
            case NaturalLanguage.DE, False:
                self.nlp = spacy.load('de_core_news_lg')
            case _:
                raise ValueError(f'spaCy model for Natural language {self.natural_language} could not be loaded.')

    def set_coref(self):
        match self.coref_module:
            case 'fastcoref':
                self.nlp.select_pipes(enable=['transformer', 'tagger'])
                config = dict(model_architecture='LingMessCoref', model_path='biu-nlp/lingmess-coref', device='cuda')
                self.nlp.add_pipe('fastcoref', config=config)
                self.doc_conf = dict(fastcoref={'resolve_text': True})
                self.cluster_extension = 'coref_clusters'
                self.resolve_extension = 'resolved_text'
            case 'coreferee':
                self.nlp.add_pipe('coreferee')
                # self.doc_conf = dict(fastcoref={'resolve_text': True})
                self.cluster_extension = 'coref_chains'
                # self.resolve_extension = 'resolved_text'

    def create_doc(self, text: str):
        self.doc = self.nlp(text, component_cfg=self.doc_conf)

    def _get_ext_val(self, extension_name: str) -> list | str:
        return getattr(self.doc._, extension_name)

    def get_clusters(self):
        clusters = self._get_ext_val(extension_name=self.cluster_extension)
        match self.coref_module:
            case 'fastcoref':
                return clusters
            case 'coreferee':
                return clusters

    def get_resolved_text(self):
        return self._get_ext_val(extension_name=self.resolve_extension)

    def clear_gpu(self):
        gc.collect()
        torch.cuda.empty_cache()


