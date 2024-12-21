"""This is from: https://python.langchain.com/v0.1/docs/use_cases/extraction/how_to/examples/ """
from typing import List
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from data_models import Coreference, ClusterHead, Cluster

""" SAMPLES """
examples = [
    Cluster(cluster_id=101, text='Der Abschwung im PC-Markt erwischt auch den Chipkonzern AMD. Im vergangenen Quartal sank der Umsatz um neun Prozent, wie der Konzern nach US-Boersenschluss am Dienstag mitteilte. Das Unternehmen hatte 2023 ein Restrukturierungsprogramm begonnen.',
        cluster_head=ClusterHead(head_text='Chipkonzern AMD', head_index_start=44, head_index_end=59), coreferences=[Coreference(coref_text='ein fuehrender Anbieter', coref_with_surroundings='MicroVision, Inc., ein fuehrender Anbieter von MEMS'), Coreference(coref_text='Konzern', coref_with_surroundings='wie der Konzern nach US'), Coreference(coref_text='Unternehmen', coref_with_surroundings='mitteilte. Das Unternehmen hatte 2023')]),

    Cluster(cluster_id=22, text='MicroVision, Inc., ein fuehrender Anbieter von MEMS-basierten Solid-State-Lidar- und Fahrerassistenzsystemen fuer die Automobilindustrie, gab heute bekannt, dass das Unternehmen am Dienstag, den 9. Mai 2023 nach Boersenschluss die Ergebnisse des ersten Quartals 2023 veroeffentlichen wird. Das Unternehmen wird anschliessend am Dienstag, den 9. Mai 2023 um 14 Uhr PT 17 Uhr ET eine Telefonkonferenz und einen Webcast mit vorbereiteten Bemerkungen des Managements, einer Folienpraesentation und einer Frage-und-Antwort-Runde abhalten.',
        cluster_head=ClusterHead(head_text='MicroVision, Inc.', head_index_start=0, head_index_end=17), coreferences=[Coreference(coref_text='ein fuehrender Anbieter', coref_with_surroundings='MicroVision, Inc., ein fuehrender Anbieter von MEMS'), Coreference(coref_text='Unternehmen', coref_with_surroundings='dass das Unternehmen am Dienstag'), Coreference(coref_text='Unternehmen', coref_with_surroundings='wird. Das Unternehmen wird anschliessend')]),

    Cluster(cluster_id=303, text='Der Oelkonzern BP hat im ersten Quartal die niedrigeren Oel- und Gaspreise zu spueren bekommen. Der operative Gewinn schrumpfte aber nicht so stark wie befuerchtet. Dank des weiterhin hohen Geldzuflusses kuendigte BP am Dienstag in London auch den Rueckkauf weiterer Aktien an - aber mit gedrosseltem Tempo. Unter diesem Eindruck verlor der Aktienkurs im fruehen Londoner Handel mehr als 5 Prozent. Im ersten Quartal ging der um Sondereffekte bereinigte Gewinn im Jahresvergleich um rund ein Fuenftel auf knapp fuenf Milliarden US-Dollar zurueck, wie der Konzern mitteilte. Damit uebertraf der Konzern die Erwartungen der Experten. Inklusive Sondereffekten betrug der Gewinn 8,2 Milliarden Dollar. Wegen der Abschreibung seiner Beteiligung an dem russischen Oelkonzern Rosneft und des Rueckzugs aus dem Geschaeft in Russland war im Vorjahreszeitraum unter dem Strich ein Verlust in Hoehe von 20,4 Milliarden Dollar angefallen. Unterdessen verlangsamt BP das Tempo bei den Aktienrueckkaeufen. Auch wenn die Gewinne der grossen Oelkonzerne unter den Rekordwerten aus dem Jahr 2022 liegen, sind sie im historischen Vergleich immer noch hoch. Die Unternehmen erwirtschaften immer noch eine Menge zusaetzlicher Barmittel, sodass BP seine Investoren mit dem Rueckkauf von Aktien im Wert von 1,75 Milliarden Dollar bis zur Bekanntgabe der Ergebnisse fuer das zweite Quartal belohnen will. Erst juengst beendete das Unternehmen den Rueckkauf eigener Aktien im Wert von 2,75 Milliarden Dollar, das es Anfang Februar angekuendigt hatte. Seit Anfang des Jahres setzt der Konzern seine Strategie um, in naher Zukunft mehr Oel und Gas zu foerdern und gleichzeitig die Investitionen in kohlenstoffarme Energien zu erhoehen. Im April nahm das Unternehmen eine grosse neue Oelplattform im Golf von Mexiko in Betrieb und kuendigte an, dass es Geschaefte vereinbaren will, um die Produktion fossiler Brennstoffe weiter zu steigern. Dies veraergert Aktivisten und einige Investoren. Andere Aktionaere wollen nach einer mehrjaehrigen Durststrecke fuer die ganze Branche allerdings hoehere Kapitalrueckfluesse sehen. Die BP-Aktien haben sich seit einem Jahr um rund 30 Prozent verteuert.',
        cluster_head=ClusterHead(head_text='Oelkonzern BP', head_index_start=4, head_index_end=17),
        coreferences=[Coreference(coref_text='BP', coref_with_surroundings='Geldzuflusses kuendigte BP am Dienstag'), Coreference(coref_text='BP', coref_with_surroundings='Unterdessen verlangsamt BP das Tempo'), Coreference(coref_text='BP', coref_with_surroundings='Barmittel, sodass BP seine Investoren'), Coreference(coref_text='Konzern', coref_with_surroundings='wie der Konzern mitteilte. Damit'), Coreference(coref_text='Konzern', coref_with_surroundings='uebertraf der Konzern die Erwartungen'),
            Coreference(coref_text='Konzern', coref_with_surroundings='setzt der Konzern seine Strategie'), Coreference(coref_text='seine', coref_with_surroundings='der Konzern seine Strategie um'), Coreference(coref_text='seine', coref_with_surroundings='sodass BP seine Investoren mit'), Coreference(coref_text='seiner', coref_with_surroundings='der Abschreibung seiner Beteiligung an'), Coreference(coref_text='es', coref_with_surroundings='Dollar, das es Anfang Februar'),
            Coreference(coref_text='es', coref_with_surroundings='an, dass es Geschaefte vereinbaren')]),

    Cluster(cluster_id=54, text="Abivax SA, ein Biotechnologieunternehmen mit einem Produkt in der klinischen Phase 3, das Therapien zur Modellierung des koerpereigenen Immunsystems entwickelt, um die Symptome von Patienten, die an chronischen Entzuendungserkrankungen leiden, zu lindern, gibt heute die Veroeffentlichung einer von Experten verfassten Publikation im Journal of Crohn's and Colitis  bekannt. Prof. Dr. med. Hartmut J. Ehrlich, CEO von Abivax, sagte: Wir sind stolz auf die Veroeffentlichung dieser Expertenmeinung, die von international fuehrenden Fachleuten auf dem Gebiet der CED verfasst wurde. Die Schlussfolgerung der Autorenrunde, dass Obefazimod eine vielversprechende neue Therapieoption fuer CU-Patienten darstellt, ist fuer das Abivax-Team sehr motivierend. Wir glauben, dass wir auf dem richtigen Weg sind, um zu belegen, dass unser Produktkandidat die Symptome von an CU leidenden Patienten schnell und dauerhaft lindern kann. Es ermutigt uns, dass die fuehrenden Fachleute sowie unsere Investoren und Partner unsere Einschaetzung zum Potenzial von Obefazimod teilen und dass das Interesse der wissenschaftlichen und medizinischen Fachwelt sowie unserer Investoren an dem Molekuel weiter zunimmt. Wir sind entschlossen, unser laufendes Phase-3-Programm so schnell wie moeglich abzuschliessen, um Obefazimod allen CU-Patienten zur Verfuegung stellen zu koennen, insbesondere denjenigen, die dringend alternative Behandlungsmoeglichkeiten benoetigen. Abivax fuehrt derzeit ein internationales klinisches Phase-3-Programm  durch.",
        cluster_head=ClusterHead(head_text='Abivax SA', head_index_start=0, head_index_end=9),
        coreferences=[Coreference(coref_text='ein Biotechnologieunternehmen', coref_with_surroundings='Abivax SA, ein Biotechnologieunternehmen mit einem'), Coreference(coref_text='das', coref_with_surroundings='Phase 3, das Therapien zur'), Coreference(coref_text='Abivax', coref_with_surroundings='CEO von Abivax, sagte: Wir'), Coreference(coref_text='Abivax', coref_with_surroundings='Behandlungsmoeglichkeiten benoetigen. Abivax fuehrt derzeit'),
            Coreference(coref_text='Wir', coref_with_surroundings='Abivax, sagte: Wir sind stolz'), Coreference(coref_text='Wir', coref_with_surroundings='sehr motivierend. Wir glauben, dass'), Coreference(coref_text='Wir', coref_with_surroundings='weiter zunimmt. Wir sind entschlossen'), Coreference(coref_text='unser', coref_with_surroundings='belegen, dass unser Produktkandidat die'), Coreference(coref_text='unser', coref_with_surroundings='sind entschlossen, unser laufendes Phase'),
            Coreference(coref_text='uns', coref_with_surroundings='Es ermutigt uns, dass die'), Coreference(coref_text='unsere', coref_with_surroundings='Fachleute sowie unsere Investoren und'), Coreference(coref_text='unsere', coref_with_surroundings='Partner unsere Einschaetzung zum'), Coreference(coref_text='unserer', coref_with_surroundings='Fachwelt sowie unserer Investoren an'), ])
    ]


""" PREDICTIONS """
predict_dict: dict = {"text": "Die US-Bank JPMorgan hat die Einstufung fuer Pfizer auf Neutral mit einem Kursziel von 45 US-Dollar belassen. Dank covidbedingter Umsaetze habe der Pharmakonzern die Erwartungen im ersten Quartal insgesamt getoppt, schrieb Analyst Chris Schott in einer am Dienstag vorliegenden Studie. Das Kerngeschaeft habe aber leicht enttaeuscht.",
                      "cluster_head": ClusterHead(head_text='Pfizer', head_index_start=45, head_index_end=51)}


def _convert_example_to_message(cluster: Cluster) -> List[BaseMessage]:
    human_content: str = f"cluster_id: {cluster.cluster_id}, text: {cluster.text}\ncluster_head: {cluster.cluster_head.model_dump_json()}"
    messages: List[BaseMessage] = [HumanMessage(content=human_content), AIMessage(content=cluster.model_dump_json())]
    return messages


def convert_examples_to_messages() -> list[BaseMessage]:
    messages = []
    for cluster in examples:
        messages.extend(
            _convert_example_to_message(cluster=cluster)
        )
    return messages


if __name__ == '__main__':
    from pprint import pprint
    pprint(convert_examples_to_messages())