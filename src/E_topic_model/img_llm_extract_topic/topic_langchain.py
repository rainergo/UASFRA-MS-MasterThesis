import os
import re
import pandas as pd
import uuid
from dotenv import load_dotenv
import nest_asyncio
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.globals import set_verbose, set_debug


from data_models import Frame, TopicExplain
from examples import convert_examples_to_messages
from prompts import prompt_template_langchain

load_dotenv('../../../secrets.env')


class TopicLangchain:
    def __init__(self, prompt_template: str, model_name: str = "gpt-4o"):
        nest_asyncio.apply()
        self.prompt = PromptTemplate(template=prompt_template, input_variables=["user_data", "topics"]).partial(pattern=re.compile(r"\`\`\`\n\`\`\`"))
        self.llm = ChatOpenAI(temperature=0, model=model_name, openai_api_key=os.getenv('OPENAI_API_KEY'))
        self.llm = self.llm.with_structured_output(schema=Frame)
        self.chain = self.prompt | self.llm
        self.examples: list[BaseMessage] = convert_examples_to_messages()
        self.topics: str = str({i.name: i.value for i in TopicExplain})

    def make_frame(self, df: pd.DataFrame) -> Frame:
        return Frame(indexes=df.index.values, sentences=df.sentences.values)

    def format_prompt_template(self, df: pd.DataFrame):
        frame = self.make_frame(df)
        prompt_template = self.prompt.template.format(user_data=frame, topics=self.topics, examples=self.examples)
        return prompt_template

    def get_topics(self, df: pd.DataFrame):
        frame = self.make_frame(df)
        return self.chain.invoke({"user_data": frame, "topics": self.topics, "examples": self.examples})


if __name__ == '__main__':
    from pprint import pprint
    set_debug(True)
    set_verbose(True)
    data = {'indexes': [i for i in range(34)], 'sentences': [
'Insgesamt machte das Unternehmen im Geschaeftsjahr 2022 23 ein operatives Minus von 1,04 Milliarden Pfund und riss damit auch das Ergebnis des Mutterkonzerns Comp@Name@Placeholder tief in die roten Zahlen.',
'Im groessten Einzelmarkt Deutschland steigerte das Unternehmen Umsatz und Ergebnis.',
'Der weltweit taetige Automobil- und Industriezulieferer Comp@Name@Placeholder hat seine Zahlen fuer die ersten drei Monate des Jahres 2023 veroeffentlicht.',
'Seit Anfang des Jahres setzt der Konzern seine Strategie um, in naher Zukunft mehr Oel und Gas zu foerdern und gleichzeitig die Investitionen in kohlenstoffarme Energien zu erhoehen.',
'Plastics Adjusted EBITDA 2,9 5,5 -46,8 % Adjusted EBITDA-Marge in % 7,3 13,0 -570 BP Adjusted EBIT 0,7 3,3 -79,2 % Adjusted EBIT-Marge',
'Die Comp@Name@Placeholder ist aufgrund ihrer zwei Jahrzehnte langen Erfahrung im Hanfanbau optimal in der Lage, Privatpersonen und gemeinschaftliche Anbauvereinigungen zu beliefern.',
'Dank des weiterhin hohen Geldzuflusses kuendigte Comp@Name@Placeholder am Dienstag in London auch den Rueckkauf weiterer Aktien an - aber mit gedrosseltem Tempo.',
'Mit unvergleichlich schnellen Verarbeitungszeiten, die bis zu 20-mal schneller sind als bei jeder anderen Analytics-Datenbank, bietet Comp@Name@Placeholder ein einzigartiges Preis-Leistungs-Verhaeltnis und ermoeglicht Kunden einen bis zu 320% schnelleren ROI durch geringere Lizenz- Implementierungs- Wartungs- Optimierungs- und Schulungskosten.',
'Das Konzessionsgebiet CLR grenzt an das bekannte Projekt Lake North von F3 Comp@Name@Placeholder.',
'Comp@Name@Placeholder verwies auf die Schliessung eines Comp@Name@Placeholder-Werks in Bridgend sowie die Verlegung der Produktion nach China.',
'Der Plan sieht vor, dass Hans Schmidt ab der naechsten Jahreshauptversammlung von Comp@Name@Placeholder Anfang des dritten Quartals 2023 alleiniger CEO von Comp@Name@Placeholder wird, um das operative Tagesgeschaeft und die anstehende Serienproduktion von Comp@Name@Placeholder zu leiten, waehrend der derzeitige Co-CEO, Michael Schulz, vorbehaltlich der Zustimmung der Aktionaere in den Aufsichtsrat von Comp@Name@Placeholder wechseln soll, damit er sein umfangreiches Netzwerk in der Branche noch effizienter zum Nutzen des Unternehmens einsetzen kann.',
'Im Segment Plastics macht sich der bereits antizipierte diesjaehrige Ausfall eines grossen Kunden bei Comp@Name@Placeholder bemerkbar.',
'Der Oelkonzern Comp@Name@Placeholder hat im ersten Quartal die niedrigeren Oel- und Gaspreise zu spueren bekommen.',
'Damit uebertraf der Konzern die Erwartungen der Experten.',
'Der mutmassliche Todesschuetze von Waiblingen, der im Werk von Comp@Name@Placeholder auf zwei Kollegen gefeuert haben soll, hat sich bisher nicht zu der Tat geaeussert.',
'Name: Comp@Name@Placeholder.  ',
'Heute gibt es wunderschöne Blumen im Angebot für EUR 3,99. Ein toller Preis.', 'Insgesamt machte das Unternehmen im Geschaeftsjahr 2022 23 ein operatives Minus von 1,04 Milliarden Pfund und riss damit auch das Ergebnis des Mutterkonzerns Comp@Name@Placeholder tief in die roten Zahlen.', 'Im groessten Einzelmarkt Deutschland steigerte das Unternehmen Umsatz und Ergebnis.',
'Der weltweit taetige Automobil- und Industriezulieferer Comp@Name@Placeholder hat seine Zahlen fuer die ersten drei Monate des Jahres 2023 veroeffentlicht.', 'Seit Anfang des Jahres setzt der Konzern seine Strategie um, in naher Zukunft mehr Oel und Gas zu foerdern und gleichzeitig die Investitionen in kohlenstoffarme Energien zu erhoehen.', 'Plastics Adjusted EBITDA 2,9 5,5 -46,8 % Adjusted EBITDA-Marge in % 7,3 13,0 -570 BP Adjusted EBIT 0,7 3,3 -79,2 % Adjusted EBIT-Marge',
'Die Comp@Name@Placeholder ist aufgrund ihrer zwei Jahrzehnte langen Erfahrung im Hanfanbau optimal in der Lage, Privatpersonen und gemeinschaftliche Anbauvereinigungen zu beliefern.', 'Dank des weiterhin hohen Geldzuflusses kuendigte Comp@Name@Placeholder am Dienstag in London auch den Rueckkauf weiterer Aktien an - aber mit gedrosseltem Tempo.',
'Mit unvergleichlich schnellen Verarbeitungszeiten, die bis zu 20-mal schneller sind als bei jeder anderen Analytics-Datenbank, bietet Comp@Name@Placeholder ein einzigartiges Preis-Leistungs-Verhaeltnis und ermoeglicht Kunden einen bis zu 320% schnelleren ROI durch geringere Lizenz- Implementierungs- Wartungs- Optimierungs- und Schulungskosten.', 'Das Konzessionsgebiet CLR grenzt an das bekannte Projekt Lake North von F3 Comp@Name@Placeholder.',
'Comp@Name@Placeholder verwies auf die Schliessung eines Comp@Name@Placeholder-Werks in Bridgend sowie die Verlegung der Produktion nach China.',
'Der Plan sieht vor, dass Hans Schmidt ab der naechsten Jahreshauptversammlung von Comp@Name@Placeholder Anfang des dritten Quartals 2023 alleiniger CEO von Comp@Name@Placeholder wird, um das operative Tagesgeschaeft und die anstehende Serienproduktion von Comp@Name@Placeholder zu leiten, waehrend der derzeitige Co-CEO, Michael Schulz, vorbehaltlich der Zustimmung der Aktionaere in den Aufsichtsrat von Comp@Name@Placeholder wechseln soll, damit er sein umfangreiches Netzwerk in der Branche noch effizienter zum Nutzen des Unternehmens einsetzen kann.',
'Im Segment Plastics macht sich der bereits antizipierte diesjaehrige Ausfall eines grossen Kunden bei Comp@Name@Placeholder bemerkbar.', 'Der Oelkonzern Comp@Name@Placeholder hat im ersten Quartal die niedrigeren Oel- und Gaspreise zu spueren bekommen.', 'Damit uebertraf der Konzern die Erwartungen der Experten.', 'Der mutmassliche Todesschuetze von Waiblingen, der im Werk von Comp@Name@Placeholder auf zwei Kollegen gefeuert haben soll, hat sich bisher nicht zu der Tat geaeussert.',
'Name: Comp@Name@Placeholder.  ', 'Heute gibt es wunderschöne Blumen im Angebot für EUR 3,99. Ein toller Preis.',

]}
    df = pd.DataFrame(data=data)
    # print(df)
    tl = TopicLangchain(prompt_template=prompt_template_langchain)
    # print(tl.format_prompt_template(df=df))
    # response = tl.get_topics(df=df)
    # print(response)
    # pprint(tl.examples)
    pprint(tl.topics)
