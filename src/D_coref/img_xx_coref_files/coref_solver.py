import torch
import spacy
from enum import Enum

spacy.require_cpu()


class NaturalLanguage(Enum):
    DE = 'de'
    EN = 'en'


class CorefResolver:

    def __init__(self, natural_language: NaturalLanguage, model_name: str = "minilm"):
        match natural_language:
            case NaturalLanguage.EN:
                self.nlp = spacy.load("en_core_web_lg")
            case NaturalLanguage.DE:
                self.nlp = spacy.load("de_core_news_lg")
        self.nlp.add_pipe("xx_coref", config={"chunk_size": 2500, "chunk_overlap": 2, "model_name": model_name})

    def get_cluster(self, text: str) -> dict[dict[str:int, str:int, str:str]]:
        doc = self.nlp(text=text)
        return doc._.coref_clusters


if __name__ == '__main__':
    cr = CorefResolver(natural_language=NaturalLanguage.DE, model_name="minilm")
    text = """Cewe macht tolle Bilder. Die Firma ist grossartig."""
    search_terms = ["konzern", "dienstleister", "firma"]
    print(cr.get_cluster(text=text))
