from enum import Enum, auto
from typing import Optional
from typing_extensions import Self

import pandas as pd
from pydantic.v1 import BaseModel, Field # model_validator


class TopicExplain(str, Enum):
    """ The Topic of the sentence. Topics can only be one of the following: """
    topic1 = ("Sätze mit konkreten Zahlenangaben aus Quartals- oder Jahresberichten. Die genannten Zahlen beziehen sich auf die Bilanz, den Umsatz- oder die Gewinn- und Verlustrechnung (GuV). "
              "Beispiele dafür sind EBIT, EBITDA, Gewinn oder Verlust vor Steuern, Gewinn- oder Verlustmargen, der Umsatz, Veränderungen der Größen über einen Zeitraum, etc.")
    topic2 = "Sätze mit allgemeinen Aussagen und Einschätzungen zu Unternehmensergebnissen, die Bilanzerung und den Umsatz. Dies sind Wertungen, oft von Verantwortlichen im Unternehmen, die keine konkreten Zahlen beinhalten. "
    topic3 = ("Sätze, die sich auf eine bevorstehende oder vergangene Hauptversammlung oder die Veröffentlichung von Unternehmensergebnissen beziehen, ohne dass dabei konkrete Zahlen genannt werden. "
              "Beispiele dafür sind die Ankündigung einer Veröffentlichung von Quartals- oder Jahresberichten oder Informationen zu bzw. über eine Hauptversammlung.")
    topic4 = "Zukunftsgerichteter Ausblick, Prognosen, Ziele, Strategie und Pläne der Unternehmensleitung."
    topic5 = "Sätze, die Kennzahlen zu Unternehmensergebnissen beinhalten, ohne dass dabei ganze Sätze gebildet werden oder die Zahlen beschrieben und erläutert werden. Beispiele dafür sind tabellenartige Angaben von Kennzahlenvariablen und deren Werte wie: 'EBITDA EUR 23 Mio.'"
    topic6 = "Sätze, in denen die Aktivitäten und das Profil des Unternehmens dargestellt wird. Oft dienen die Sätze der positiven Selbstdarstellung seitens des Managements, dem Brand-Marketing oder einer allgemeinen Unternehmensbeschreibung."
    topic7 = "Stimmrechte, Kapitalveränderungen, Dividenden, Finanzierung, Listing an Börsen, Marktkapitalisierung."
    topic8 = "Sätze, in denen das vom Unternehmen angebotene Produkt, eine Produktentwicklung oder ein neue Neuerung im Hinblick auf ein Produkt des Unternehmens beschrieben wird."
    topic9 = "Sätze, in denen die Herstellung des Produkts, der Produkt-Forschung, die Exploration vn Bodenschätzen, Produkt- oder Medikamenten-Zulassungen, dem Finden neuer Resourcen oder anderen dem Herstellungsprozess nahen Themen geht."
    topic10 = "Konzernumbau, wichtige organisatorische Veränderungen, Restrukturierung, Werksstilllegung, strategische Partnerschaften, Übernahmen"
    topic11 = "Personalveränderungen im Vorstand, Aufsichtsrat, Betriebsrat oder anderer Organe im Unternehmen, Personal, Gewerkschaftem, Streiks"
    topic12 = "Kunden, Marktanteile, Absatzmärkte, Umsätze, Absatzpreise"
    topic13 = "Einflüsse von Aussen auf die Erfolgsaussichten von Unternehmen etwa durch Subventionen, Staatliche Eingriffe, Umbrüche im Markt, politische Veränderungen, Umwelteinflüsse, etc."
    topic14 = "Einschätzungen Unternehmensfremder/Analysten zu einem Unternehmen"
    topic15 = "Unfälle, Gewalt, Katastrophen"
    topic16 = "Unvollständige Sätze mit einzelnen, nicht-zusammenhängenen Worten, ohne Kontext, die wahrscheinlich falsch formattiert oder im vorangehenden Text-Reinigungsprozess falsch gesplittet wurden. "
    topic17 = "Alle anderen topics, die den oben genannten 16 topics nicht zugeordnet werden können."


class Topic(Enum):
    """ The Topic of the sentence. Topics can only be one of the following: """
    topic1 = 'topic1'
    topic2 = 'topic2'
    topic3 = 'topic3'
    topic4 = 'topic4'
    topic5 = 'topic5'
    topic6 = 'topic6'
    topic7 = 'topic7'
    topic8 = 'topic8'
    topic9 = 'topic9'
    topic10 = 'topic10'
    topic11 = 'topic11'
    topic12 = 'topic12'
    topic13 = 'topic13'
    topic14 = 'topic14'
    topic15 = 'topic15'
    topic16 = 'topic16'
    topic17 = 'topic17'


class Frame(BaseModel):
    """ DataFrame that contains the index of the DataFrame and the column "top_sent" which contains the sentences for which a topic shall be determined. """
    indexes: list[int] = Field(description='The indexes of the rows in the pandas DataFrame')
    sentences: list[str] = Field(default=None, description='List of sentences each for which the Topic shall be determined.')
    topics: list[Topic] = Field(default=None, description='List of Topic enums for each sentence in "sentences". List must be of same length as "sentences" list.')

    # @model_validator(mode='after')
    # def verify_same_len(self) -> Self:
    #     if self.topics is None:
    #         if len(self.indexes) != len(self.sentences):
    #             raise ValueError(f'"indexes" (len: {len(self.indexes)}) and "sentences" (len: {len(self.sentences)}) must have the same length')
    #     else:
    #         if len(self.indexes) != len(self.topics):
    #             raise ValueError(f'"indexes" (len: {len(self.indexes)}) and "topics" (len: {len(self.topics)}) must have the same length')
    #     return Self

    @staticmethod
    def df_to_instance(df: pd.DataFrame):
        indexes = df.index.tolist()
        sentences = [item if isinstance(item, str) else str(item) for item in df.top_sent.tolist()]
        return Frame(indexes=indexes, sentences=sentences)


if __name__ == '__main__':
    frame = Frame(indexes=[0,1,2,3], sentences= ['bal', 'balla', 'bababb', 'nanan'])
    # frame = Frame(indexes=[0, 1, 2, 3], topics=['topic1', 'topic2', 'topic3', 'topic4'])
    print(frame)