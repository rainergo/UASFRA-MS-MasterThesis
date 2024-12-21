import re

from src.B_spacy_pipeline.data_models import SearchMatch, EntsWithCustExts
from src.B_spacy_pipeline.spacy_utils import IDXReferTo

clusters = [{'cluster_id': 11,
    'text': 'GK Software SE: Abschluss eines Delisting-Vertrages mit Fujitsu Delisting-Erwerbsangebot von Fujitsu zu EUR 190,00 je Aktie angekuendigt.  GK Software SE: Abschluss eines Delisting-Vertrages mit Fujitsu  Delisting-Erwerbsangebot von Fujitsu zu EUR 190,00 je Aktie angekuendigt.  Veroeffentlichung einer Insiderinformation nach Artikel 17 der Verordnung  Nr. 596 2014, uebermittelt durch EQS News - ein Service der EQS Group AG.  Die GK Software SE hat heute einen Delisting-Vertrag mit der Fujitsu Ltd. sowie mit deren 100%iger Tochtergesellschaft, der Fujitsu ND Solutions AG, abgeschlossen. Auf Grundlage dieses Vertrages soll die Stellung eines Antrags auf Widerruf der Zulassung der GK-Aktien am regulierten Markt erfolgen; zudem sollen wirtschaftlich angemessene Massnahmen getroffen werden, die erforderlich und fuer die Gesellschaft moeglich sind, um die Einbeziehung der GK-Aktien in den Handel im Freiverkehr zu beenden. Gemaess den Bestimmungen des Delisting-Vertrages wird die Bieterin heute die Entscheidung veroeffentlichen, den Aktionaeren der GK ein oeffentliches Delisting-Erwerbsangebot in Form eines Barangebots zum Erwerb saemtlicher Aktien der GK, die nicht bereits direkt von der Bieterin gehalten werden, gegen Zahlung einer Gegenleistung in bar in Hoehe von EUR 190,00 je GK-Aktie zu unterbreiten. Die Hoehe des Delisting-Erwerbsangebots wird somit der Hoehe der Gegenleistung des freiwilligen oeffentlichen Uebernahmeangebots aufgrund der Angebotsunterlage der Bieterin vom 23. Maerz 2023 entsprechen. Das Uebernahmeangebot wurde gemaess Meldung der Bieterin vom 25. April 2023 bislang fuer insgesamt 1.490.328 GK-Aktien angenommen; dies entspricht einem Anteil von etwa 65,57 % der bestehenden Stimmrechte der GK. Die weitere Annahmefrist zum freiwilligen oeffentlichen Uebernahmeangebot laeuft noch bis zum 9. Mai 2023, 24.00 Uhr. Der Vorstand und der Aufsichtsrat von GK, die beide dem Abschluss des Delisting-Vertrages zugestimmt haben, begruessen und unterstuetzen das angekuendigte Delisting-Erwerbsangebot von Fujitsu. Vorbehaltlich der sorgfaeltigen Pruefung der Angebotsunterlage zum oeffentlichen Delisting-Erwerbsangebot und der Wahrnehmung ihrer gesetzlichen Verpflichtungen beabsichtigen der Vorstand und der Aufsichtsrat von GK, in ihrer gemaess § 27 des Wertpapiererwerbs- und Uebernahmegesetz zu veroeffentlichenden gemeinsamen begruendeten Stellungnahme den Aktionaeren des Unternehmens zu empfehlen, das Angebot anzunehmen. Der weitere Prozess wird im Delisting-Vertrag konkretisiert. Dieser enthaelt zudem Bestimmungen zur Sicherung der Finanzierung der Gesellschaft nach Beendigung der Boersennotierung und damit auch Schutzmassnahmen zugunsten der GK-Gruppe nach Widerruf der Boersenzulassung. Nach Wirksamwerden des Widerrufs der Boersenzulassung werden die Aktien der GK nicht mehr an einem inlaendischen regulierten Markt oder einem vergleichbaren Markt im Ausland zum Handel zugelassen sein und gehandelt werden. GK Software SE.  Waldstrasse 7.  08261 Schoeneck.    WKN 757142.  ISIN DE0007571424.',
    'cluster_head': {'head_text': 'GK Software', 'head_index_start': 0, 'head_index_end': 11},
    'coreferences': [{'coref_text': 'GK Software SE', 'coref_with_surroundings': 'GK Software SE: Abschluss eines'}, {'coref_text': 'GK Software SE', 'coref_with_surroundings': 'Die GK Software SE hat heute'}, {'coref_text': 'GK', 'coref_with_surroundings': 'den Aktionaeren der GK ein'}, {'coref_text': 'GK', 'coref_with_surroundings': 'saemtlicher Aktien der GK, die'}, {'coref_text': 'GK', 'coref_with_surroundings': 'Stimmrechte der GK. Die weitere'},
        {'coref_text': 'GK', 'coref_with_surroundings': 'Vorstand und der Aufsichtsrat von GK, die'}, {'coref_text': 'GK', 'coref_with_surroundings': 'Vorstand und der Aufsichtsrat von GK, in'}, {'coref_text': 'GK', 'coref_with_surroundings': 'zugunsten der GK-Gruppe nach Widerruf'}, {'coref_text': 'GK', 'coref_with_surroundings': 'GK Software SE.  Waldstrasse'}]}]

ents = [EntsWithCustExts(start_char=0, end_char=11, ent_text='GK Software', comp_name='GK Software SE', comp_symbol='GKS.HM', set_in='own_regex_search', df_index=0)]


def convert_llm_response_to_matches(clusters: list[dict], ents: list[EntsWithCustExts]):
    """ Unfortunately, LLMs are not able to extract substring indices for their extractions well. So this must be done here. """
    matches: list[SearchMatch] = []
    for cluster, ent in zip(clusters, ents):
        text: str = cluster['text']
        coreferences: list[dict] = cluster['coreferences']
        for coref in coreferences:
            coref_with_surroundings: dict[str, str] = coref['coref_with_surroundings']
            coref_text: str = coref['coref_text']
            pattern_outer: str = rf"(?:{coref_with_surroundings})"
            pattern_inner: str = rf"(?:{coref_text})"
            # cluster_matches = [((inner_match := re.match(pattern=pattern_inner, string=m.group(0))), inner_match.group(0), (m.start() + inner_match.start()), (m.start() + inner_match.end())) for m in list(re.finditer(pattern_outer, text))]
            # print(cluster_matches)
            for m_outer in list(re.finditer(pattern_outer, text)):
                if m_outer:
                    text_outer = m_outer.group(0)
                    print('text_outer:', text_outer)
                    start_outer = m_outer.start()
                    print('pattern_inner:', pattern_inner)
                    m_inner = list(re.finditer(pattern=pattern_inner, string=text_outer))[0]
                    if m_inner:
                        print('m_inner:', m_inner)
                        start_inner = m_inner.start()
                        end_inner = m_inner.end()
                        start = start_outer + start_inner
                        end = start_outer + end_inner
                        search_match: SearchMatch = SearchMatch(comp_name=ent.comp_name, comp_symbol=ent.comp_symbol, text=coref_text, label='LLM-COREF', start_idx=start, end_idx=end, idx_refer_to=IDXReferTo.CHARS)
                        matches.append(search_match)
                print('-----------------------')
    print(matches)

"""
class SearchMatch:
    comp_name: str
    comp_symbol: str
    text: str
    label: str
    start_idx: int
    end_idx: int
    idx_refer_to: IDXReferTo

"""

if __name__ == '__main__':
    convert_llm_response_to_matches(clusters=clusters, ents=ents)
    # from pprint import pprint
    # corefs = g[0]['coreferences']
    # text = g[0]['text']
    # # pprint(corefs)
    # # print('---------------------------')
    # first_coref = corefs[0]
    # pprint(first_coref)
    # print('###############################')
    # pattern_outer = rf"(?:{first_coref['coref_with_surroundings']})"
    # # matches = list(re.finditer(pattern_outer, text))
    # pattern_inner = rf"(?:{first_coref['coref_text']})"
    # for m_outer in list(re.finditer(pattern_outer, text)):
    #     text_outer = m_outer.group(0)
    #     start_outer = m_outer.start()
    #     end_outer = m_outer.end()
    #     m_inner = re.match(pattern=pattern_inner, string=text_outer)
    #     text_inner = m_inner.group(0)
    #     start_inner = m_inner.start()
    #     end_inner = m_inner.end()
    #     match = ()
    #
    #
    # matches = [((inner_match := re.match(pattern=pattern_inner, string=m.group(0))), inner_match.group(0),(m.start() + inner_match.start()), (m.start() + inner_match.end())) for m in list(re.finditer(pattern_outer, text))]
    # print(matches)
    # print(text[0:14])
    # print(text[139:153])
