import os
from pathlib import Path
from importlib.machinery import SourceFileLoader
import pandas as pd
from dotenv import load_dotenv
from neo4j import GraphDatabase, Record
from networkx.classes import nodes

from src.settings.config import ConfigBasic, ConfigGraph
from src.F_knowledge_graph.A_rdf_graph import RDFGraph
from src.F_knowledge_graph.C_embeddings import Embedder


class GraphConstruction:
    """ Constructs a NEO4J Knowledge Graph ("KG"). Methods populate the KG with data from JSON-files (please see:
    README-data.md), with external data from wikidata/dbpedia and with text embeddings of a Node's text property. The
    methods thereby use parameterized cypher queries. """

    ONTO_ATTR_TO_DF_ATTR_MAP: dict = {'art_id': 'art_id', 'art_text': 'pp_art_text', 'art_datetime': 'art_datetime', 'art_source': 'art_source', 'comp_symbol': 'comp_symbol', 'comp_isin': 'comp_isin', 'comp_name': 'comp_name', 'sent_id': 'sent_id', 'sent_text': 'top_sent', 'top_description': 'top_description', 'top_id': 'topic'}

    def __init__(self, neo4j_db_name: str = 'neo4j'):
        self.path_to_onto = ConfigGraph.path_to_onto
        if not self.path_to_onto.is_file():
            raise ValueError(f"Provided path to Ontology '{self.path_to_onto}' does not exist!")
        try:
            load_dotenv(dotenv_path=ConfigBasic.path_to_secrets)  # Load secrets/env variables
        except:
            print('secrets could not be loaded!')
        params = SourceFileLoader('params', Path(self.path_to_onto.parent, 'params.py').as_posix()).load_module()
        self.unique_node_keys: dict[str, list[str]] = params.unique_node_keys
        self.node_value_props: dict[str,str] = params.node_value_props
        self.rdf_graph = RDFGraph(path_to_onto=self.path_to_onto)
        self.neo4j_db_name: str = neo4j_db_name
        self.driver = GraphDatabase.driver(uri="neo4j://localhost:7687", auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PW')))
        self.label_wikidata_id = "wikidataID"
        self.import_wikidata_id_was_run: bool = False

    def init_graph(self, handle_vocab_uris: str = "MAP", handle_mult_vals: str = "ARRAY",
                   multi_val_prop_list: list = None, handle_rdf_types: str = "LABELS",
                   keep_lang_tag: bool = False, keep_cust_dtypes: bool = False, apply_neo4j_naming: bool = False):
        query_init = f"""CALL n10s.graphconfig.init(
            {{  handleVocabUris: '{handle_vocab_uris}',
                handleMultival: '{handle_mult_vals}',
                multivalPropList: {list() if multi_val_prop_list is None else multi_val_prop_list},
                handleRDFTypes: '{handle_rdf_types}',
                keepLangTag: {str(keep_lang_tag).lower()},
                keepCustomDataTypes: {str(keep_cust_dtypes).lower()},
                applyNeo4jNaming: {str(apply_neo4j_naming).lower()},
                classLabel: 'CLASS',
                subClassOfRel: 'IS_A',
                objectPropertyLabel: 'RELATION',
                subPropertyOfRel: 'Sub-Property',
                domainRel: 'FROM',
                rangeRel: 'TO'
              }})"""
        query_constraint = f"""CREATE CONSTRAINT n10s_unique_uri FOR (r:Resource) REQUIRE r.uri IS UNIQUE"""
        self.driver.execute_query(query_=query_init, database_=self.neo4j_db_name)
        self.driver.execute_query(query_=query_constraint, database_=self.neo4j_db_name)

    def delete_graph(self):
        query_delete = f"""MATCH(n) DETACH DELETE n"""
        query_drop_constr = f"""DROP CONSTRAINT n10s_unique_uri IF EXISTS"""
        self.driver.execute_query(query_=query_delete, database_=self.neo4j_db_name)
        self.driver.execute_query(query_=query_drop_constr, database_=self.neo4j_db_name)
        constraints: list[Record] = self.driver.execute_query("SHOW CONSTRAINT", database_=self.neo4j_db_name).records
        for constraint in constraints:
            self.driver.execute_query(query_="DROP CONSTRAINT " + constraint['name'], database_=self.neo4j_db_name)
        indexes: list[Record] = self.driver.execute_query("SHOW INDEXES", database_=self.neo4j_db_name).records
        for index in indexes:
            self.driver.execute_query("DROP INDEX " + index['name'], database_=self.neo4j_db_name)

    def load_onto_or_rdf(self, path: str, path_is_url: bool = False,
                         load_onto_only: bool = True, serialization_type: str = "Turtle"):
        query_load = f"""
        CALL n10s.{'onto' if load_onto_only else 'rdf'}.import.fetch("{("file://" if not path_is_url else "") + path}", 
        "{serialization_type}")
        """
        print(query_load)
        try:
            self.driver.execute_query(query_=query_load, database_=self.neo4j_db_name)
        except:
            print('Did not work!')

    def import_wikidata_id(self, node: str, node_prop: str, node_prop_wikidata_id: str, wikidata_id_is_part_of: str or None = None):
        if wikidata_id_is_part_of:
            predicate = (f'(p:{wikidata_id_is_part_of}/pq:{node_prop_wikidata_id})|'
                         f'(p:{node_prop_wikidata_id}/ps:{node_prop_wikidata_id})')
        else:
            predicate = f'wdt:{node_prop_wikidata_id}'

        query = rf"""
                MATCH (node:{node})
                WITH
                    "SELECT ?{node_prop} ?{self.label_wikidata_id}
                        WHERE {{
                            FILTER (?{node_prop} = \"" + node.{node_prop} + "\")
                            ?{self.label_wikidata_id}   {predicate}   ?{node_prop} .
                      }}"
                AS sparql
                CALL apoc.load.jsonParams(
                    "https://query.wikidata.org/sparql?query=" +
                      apoc.text.urlencode(sparql),
                    {{ Accept: "application/sparql-results+json"}}, null)
                YIELD value
                UNWIND value['results']['bindings'] AS row
                WITH row['{node_prop}']['value'] AS prop_val,
                     row['{self.label_wikidata_id}']['value'] AS new_prop_val
                MERGE (n:{node} {{ {node_prop}: prop_val }})
                SET n.{self.label_wikidata_id} = new_prop_val;
                """
        # print(query)
        self.driver.execute_query(query_=query, database_=self.neo4j_db_name)
        self.import_wikidata_id_was_run = True
        # Note: For Companies that do not have an ISIN (and thus no wikidataID), we must fill the wikidataID attribute with values. Otherwise, there is no attribute at all which later causes problems.
        self._fill_empty_wikidataID_values()

    def _fill_empty_wikidataID_values(self, node: str = 'Company', missing_node_prop: str = 'comp_isin', missing_node_prop_val: str = 'isin_not_found',
                                      wikidataID_default_value: str = 'wikidataID_not_found'):
        query1 = rf"""
        Match (n:{node} {{ {missing_node_prop}: '{missing_node_prop_val}' }})
        SET n.{self.label_wikidata_id} = '{wikidataID_default_value}';
        """
        query2 = rf"""
        MATCH (n:{node}) WHERE n.{self.label_wikidata_id} IS NULL SET n.{self.label_wikidata_id} = '{wikidataID_default_value}';
        """
        self.driver.execute_query(query_=query1, database_=self.neo4j_db_name)
        self.driver.execute_query(query_=query2, database_=self.neo4j_db_name)

    def import_data_from_wikidata(self, node_label: str, prop_name: str, prop_wiki_id: str,
                                  new_prop_name: str, new_prop_wiki_id: str,
                                  use_new_prop_label: bool, new_prop_is_list: bool, prop_wiki_id_is_part_of: str or None):
        """ Please note: In order to import the data, the method "import_wikidata_id()" must be run before."""
        # if not self.import_wikidata_id_was_run:
        #     print("wikidata_id must first be imported: self.import_wikidata_id(node='Company', node_prop='comp_isin', node_prop_wikidata_id='P946') will run now.")
        #     self.import_wikidata_id(node='Company', node_prop='comp_isin', node_prop_wikidata_id='P946')

        if prop_wiki_id_is_part_of:
            predicate = f'(p:{prop_wiki_id_is_part_of}/pq:{prop_wiki_id})|(p:{prop_wiki_id}/ps:{prop_wiki_id})'
        else:
            predicate = f'wdt:{prop_wiki_id}'

        query = rf"""
        MATCH (node:{node_label})
        WITH 
            "SELECT ?{prop_name} ?{new_prop_name}{"Label" if use_new_prop_label else ""}
                WHERE {{
                    FILTER (?{prop_name} = \"" + node.{prop_name} + "\")
                    ?company {predicate} ?{prop_name} ;
                             wdt:{new_prop_wiki_id} ?{new_prop_name} .
                SERVICE wikibase:label {{ bd:serviceParam wikibase:language \"en\". }}
              }}"     
        AS sparql
        CALL apoc.load.jsonParams(
            "https://query.wikidata.org/sparql?query=" + 
              apoc.text.urlencode(sparql),
            {{ Accept: "application/sparql-results+json"}}, null)
        YIELD value
        UNWIND value['results']['bindings'] as row
        WITH row['{prop_name}']['value'] as prop_val, 
             {'collect(' if new_prop_is_list else ''}row['{new_prop_name}{"Label" if use_new_prop_label else ""}']['value']{')' if new_prop_is_list else ''} as new_prop_val
        MERGE (n:{node_label} {{ {prop_name}: prop_val }})
        SET n.{new_prop_name} = new_prop_val;
        """
        print(query)
        self.driver.execute_query(query_=query, database_=self.neo4j_db_name)

    def import_data_from_dbpedia(self, node_label: str, prop_name: str, prop_dbp_id: str,
                                 new_prop_name: str, new_prop_dbp_id: str,
                                 new_prop_is_list: bool):
        # if not self.import_wikidata_id_was_run:
        #     print("wikidata_id must first be imported: self.import_wikidata_id(node='Company', node_prop='comp_isin', node_prop_wikidata_id='P946') will run now.")
        #     self.import_wikidata_id(node='Company', node_prop='comp_isin', node_prop_wikidata_id='P946')
        query = rf"""
        MATCH (node:{node_label})
        WITH
            "PREFIX wd: <http://www.wikidata.org/entity/>
             SELECT ?{prop_name} ?{new_prop_name}
                    WHERE {{
                        BIND(<"+node.{prop_name}+"> AS ?{self.label_wikidata_id})
                        ?dbpcomp   {prop_dbp_id}   ?{self.label_wikidata_id} ;
                                   {new_prop_dbp_id} ?{new_prop_name} .
                    FILTER langMatches( lang(?{new_prop_name}), \"en\" )
                  }}
                  LIMIT 1
                  "   
        AS sparql
        CALL apoc.load.jsonParams(
            "https://dbpedia.org/sparql?query=" + 
              apoc.text.urlencode(sparql),
            {{ Accept: "application/sparql-results+json"}}, null)
        YIELD value
        UNWIND value['results']['bindings'] as row
        WITH row['{prop_name}']['value'] as prop_val,
             {'collect(' if new_prop_is_list else ''}row['{new_prop_name}']['value']{')' if new_prop_is_list else ''} as new_prop_val
        MERGE (n:{node_label} {{ {prop_name}: prop_val }})
        SET n.{new_prop_name} = new_prop_val;
        """
        print(query)
        self.driver.execute_query(query_=query, database_=self.neo4j_db_name)

    def create_text_embedding(self, node_label: str, node_primary_prop_name: str, prop_to_embed: str,
                              vector_size: int = 768,
                              similarity_method: str = "cosine"):
        name_embedded_prop = prop_to_embed + "_embedding"
        query_index = f"""CALL db.index.vector.createNodeIndex('{"NodeIndex" + "_" + node_label + "_" + prop_to_embed}',
                          '{node_label}', '{name_embedded_prop}', {vector_size}, '{similarity_method}' ) ; """
        query_prop_to_embed = f"""
        MATCH (n:{node_label})     
        RETURN n.{node_primary_prop_name} AS {node_primary_prop_name}, n.{prop_to_embed} AS {prop_to_embed}
        """
        session = self.driver.session(database=self.neo4j_db_name)
        try:
            res = self.driver.execute_query(query_=query_index, database_=self.neo4j_db_name)
        except Exception as e:
            print(f'INFO: Index not created again as index already exists: {e}.')
        embed_nodes_and_props: list[dict] = session.run(query=query_prop_to_embed).data()

        embedder = Embedder()
        for item in embed_nodes_and_props:
            embedding = embedder.get_embedding(text=item[f'{prop_to_embed}'])
            query_set_embed_prop = f"""
            MATCH (n:{node_label})
            WHERE n.{node_primary_prop_name} = {item[f'{node_primary_prop_name}']}
            SET n.{name_embedded_prop} = {embedding} ;
            """
            # print(query_set_embed_prop)
            session.run(query=query_set_embed_prop)

    def load_data_into_knowledge_graph(self, df: pd.DataFrame, show_queries: bool = False):

        def check_if_df_and_onto_match(df: pd.DataFrame, nodes_with_attrs: dict, nodes_without_attrs):
            if nodes_without_attrs:
                raise ValueError(f'There are Nodes in the Ontology that do not have any attributes (owl:DatatypeProperty): {nodes_without_attrs}. Please check!')
            df_columns: list = df.columns.tolist()
            node_attributes: list = [self.ONTO_ATTR_TO_DF_ATTR_MAP[col] for cols in nodes_with_attrs.values() for col in cols]
            not_in_df = [col for col in node_attributes if col not in df_columns]
            if not_in_df:
                raise ValueError(f'The following Node attributes are not a column in the DataFrame: {not_in_df}')

        def get_data_from_df(df: pd.DataFrame, nodes: dict[str, list], relationships: list[dict[str, str]], unique_node_keys: dict[str, list[str]]) -> tuple[list, list]:
            nodes_data: list = list()
            relationships_data: list = list()
            for ind, row in df.iterrows():
                for node, attrs in nodes.items():
                    row_template = {node: {attr: row[self.ONTO_ATTR_TO_DF_ATTR_MAP[attr]] for attr in attrs}}
                    if row_template not in nodes_data:
                        nodes_data.append(row_template)
                for rel in relationships:
                    relationship = {rel['SOURCE'] + '_' + rel['REL'] + '_' + rel['TARGET']: {"source": {rel['SOURCE']: {attr: row[self.ONTO_ATTR_TO_DF_ATTR_MAP[attr]] for attr in unique_node_keys[rel['SOURCE']]}}, "target": {rel['TARGET']: {attr: row[self.ONTO_ATTR_TO_DF_ATTR_MAP[attr]] for attr in unique_node_keys[rel['TARGET']]}}}}
                    relationships_data.append(relationship)
            return nodes_data, relationships_data

        # Note: 1. Get graph and data structure from Ontology
        nodes_with_attrs, nodes_without_attrs = self.rdf_graph.get_nodes_and_node_props()
        check_if_df_and_onto_match(df=df, nodes_with_attrs=nodes_with_attrs, nodes_without_attrs=nodes_without_attrs)
        constraint_queries, node_queries, rel_queries, ns_queries = self.rdf_graph.create_query_templates()
        relationships = self.rdf_graph.get_relationships()

        # Note: 2. Get data from pandas dataframe
        nodes_data, rels_data = get_data_from_df(df=df, nodes=nodes_with_attrs, relationships=relationships, unique_node_keys=self.unique_node_keys)

        # Note: 3. Load data into Knowledge Graph
        session = self.driver.session(database=self.neo4j_db_name)

        for ns_query in ns_queries:
            if show_queries:
                print('ns_query:', ns_query)
            session.run(ns_query)

        for constraint_query in constraint_queries:
            if show_queries:
                print('Constraint_Query: ', constraint_query)
            res0 = session.run(constraint_query)

        for node_data in nodes_data:
            node = list(node_data.keys())[0]
            node_query = node_queries[node]
            if show_queries:
                print('node:', node)
                print('Node_Query:', node_query)
            res1 = session.run(node_query, parameters={'node_data': node_data})

        for rel_data in rels_data:
            rel = list(rel_data.keys())[0]
            rel_query = rel_queries[rel]
            if show_queries:
                print('rel:', rel)
                print('Rels_Query: ', rel_query)
            res2 = session.run(rel_query, parameters={'rel_data': rel_data})

        session.close()


if __name__ == '__main__':

    # df = pd.DataFrame(data={
    #     'art_id': ['id1', 'id2', 'id3'], 'art_text': ['text 1', 'text 2', 'text 3'], 'art_datetime': ['2008/12/1', '2008/12/2', '2008/12/3'], 'art_source': ['Reuters', 'Bloomberg', 'DPA'],
    #     'comp_name': ['Gecina', 'Adidas', 'Gecina'], 'comp_isin': ['FR0010040865', 'DE000A1EWWW0', 'FR0010040865'],
    #     'sent_id': ['sen1', 'sen2', 'sen3'], 'sent_text': ['topic 1 sent text', 'topic 2 sent text', 'topic 3 sent text'],
    #     'top_id': ['top1', 'top2', 'top1'], 'top_description': ['top1 description', 'top2 description', 'top1 description'], })
    from pandas import Timestamp
    from numpy import array
    df = pd.DataFrame.from_dict({'index': {11: 11, 12: 12, 13: 13},
 'art_source': {11: 'dpa-afx-compact',
  12: 'dpa-afx-compact',
  13: 'dpa-afx-compact'},
 'art_url': {11: 'https://mobile.traderfox.com/news/dpa-compact/679071-eqs-news-netfonds-ag-erwerb-eigener-aktien-24-zwischenmeldung-deutsch/',
  12: 'https://mobile.traderfox.com/news/dpa-compact/679460-diepost-erwaegt-schritte-zur-vorzeitigen-erhoehung-des-briefportos/',
  13: 'https://mobile.traderfox.com/news/dpa-compact/679460-diepost-erwaegt-schritte-zur-vorzeitigen-erhoehung-des-briefportos/'},
 'art_type': {11: 'unt', 12: 'unt', 13: 'unt'},
 'art_datetime': {11: Timestamp('2023-05-02 10:56:00+0200', tz='Europe/Berlin'),
  12: Timestamp('2023-05-03 13:14:00+0200', tz='Europe/Berlin'),
  13: Timestamp('2023-05-03 13:14:00+0200', tz='Europe/Berlin')},
 'art_language': {11: 'DE', 12: 'DE', 13: 'DE'},
 'art_isin': {11: 'DE000A1MME74', 12: 'DE0005552004', 13: 'DE0005552004'},
 'art_company_name': {11: 'Netfonds AG',
  12: 'Deutsche Post AG',
  13: 'Deutsche Post AG'},
 'art_title': {11: 'EQS-News: Netfonds AG: Erwerb eigener Aktien - 24. Zwischenmeldung (deutsch)',
  12: 'Die\xa0Post erwägt Schritte zur vorzeitigen Erhöhung des Briefportos',
  13: 'Die\xa0Post erwägt Schritte zur vorzeitigen Erhöhung des Briefportos'},
 'art_text': {11: 'Netfonds AG: Erwerb eigener Aktien - 24. Zwischenmeldung\n\n^\nEQS-News: Netfonds AG / Schlagwort(e): Aktienrückkauf\nNetfonds AG: Erwerb eigener Aktien - 24. Zwischenmeldung\n\n02.05.2023 / 10:55 CET/CEST\nFür den Inhalt der Mitteilung ist der Emittent / Herausgeber verantwortlich.\n\n---------------------------------------------------------------------------\n\nNetfonds AG: Erwerb eigener Aktien - 24. Zwischenmeldung\n\nHamburg, 02. Mai 2023 - Im Zeitraum vom 24. April 2023 bis einschließlich\n28. April 2023 hat die Netfonds AG insgesamt 429 Aktien im Rahmen ihres\nlaufenden Aktienrückkaufprogramms gekauft, das mit der Bekanntmachung vom\n11. Oktober 2022 gemäß Art. 5 Abs. 1 lit. a) der Verordnung (EU) Nr.\n596/2014 und Art. 2 Abs. 1 der Delegierten Verordnung (EU) Nr. 2016/1052\nangekündigt wurde.\n\nDabei wurden jeweils folgende Stückzahlen gekauft:\n\nMo., 24. Apr. 23 93 39,89 3.709,60\nDi., 25. Apr. 23 103 39,60 4.078,80\nMi., 26. Apr. 23 65 39,40 2.561,00\nDo., 27. Apr. 23 87 39,60 3.445,20\nFr., 28. Apr. 23 81 39,80 3.223,80\n\nDie Gesamtzahl der im Rahmen des Aktienrückkaufprogramms seit dem 07.\nNovember 2022 bis einschließlich 28. April 2023 gekauften Aktien beläuft\nsich damit auf 11.352 Aktien mit einem Gesamtvolumen von 466.342,60 EUR.\n\nDer Erwerb der Aktien der Netfonds AG erfolgt ausschließlich über die Börse\ndurch ein von der Netfonds AG beauftragtes Kreditinstitut.\n\nDetaillierte Informationen über die Transaktionen gemäß Art. 2 Abs. 3\nDelegierte Verordnung (EU) Nr. 2016/1052 sind auf der Internetseite der\nNetfonds AG im Bereich "Investor Relations" veröffentlicht.\n\n---\n\nKontakt\nNetfonds AG\nHeidenkampsweg 73\n20097 Hamburg\n\nInvestor Relations\nPhilip Angrabeit\nTel.: +49 40 822 267 142\nE-Mail: pangrabeit@netfonds.de\n\n---\n\nÜber die Netfonds Gruppe\nDie Netfonds Gruppe ist eine führende Plattform für Administration, Beratung\nund Regulierung für die deutsche Finanzindustrie. Unter der Marke finfire\nstellt das Unternehmen seinen Kunden und Partnern eine cloudbasierte\nTechnologieplattform zur kompletten Abwicklung und Administration der\nGeschäftsvorgänge zur Verfügung. Kunden von Netfonds profitieren somit von\neiner der modernsten Softwarelösungen am Markt, die den Beratungsprozess\ndeutlich vereinfacht, sicher gestaltet und zielgruppengenaue Beratung\nermöglicht. Die Aktie der Netfonds AG ist im m:access der Börse München\ngelistet und über XETRA handelbar.\n\n---------------------------------------------------------------------------\n\n02.05.2023 CET/CEST Veröffentlichung einer Corporate News/Finanznachricht,\nübermittelt durch EQS News - ein Service der EQS Group AG.\nFür den Inhalt der Mitteilung ist der Emittent / Herausgeber verantwortlich.\n\nDie EQS Distributionsservices umfassen gesetzliche Meldepflichten, Corporate\nNews/Finanznachrichten und Pressemitteilungen.\nMedienarchiv unter https://eqs-news.com\n\n---------------------------------------------------------------------------\n\nSprache: Deutsch\nUnternehmen: Netfonds AG\nHeidenkampsweg 73\n20097 Hamburg\nDeutschland\nTelefon: +49 40 822267 0\nE-Mail: info@netfonds.de\nInternet: www.netfonds.de\nISIN: DE000A1MME74\nWKN: A1MME7\nBörsen: Freiverkehr in Berlin, Düsseldorf, Frankfurt, München\n(m:access)\nEQS News ID: 1621957\n\nEnde der Mitteilung EQS News-Service\n---------------------------------------------------------------------------\n\n1621957 02.05.2023 CET/CEST\n\n°',
  12: 'BONN (dpa-AFX) - Die Deutsche Post\nerwägt wegen deutlich gestiegener Kosten, ein Verfahren zur vorzeitigen Erhöhung des Briefportos anzustoßen. Man prüfe, ob gewisse Parameter erfüllt seien und werde dann entscheiden, sagte Post-Vorstand Tobias Meyer am Mittwoch in Bonn. "Natürlich werden wir uns genau anschauen, welche Möglichkeiten es gibt." Allerdings seien die Hürden für den entsprechenden verwaltungsrechtlichen Akt "nicht niedrig", gab er zu bedenken. Die Post darf das Porto nicht selbst festlegen. Stattdessen macht die Bundesnetzagentur als zuständige Behörde Vorgaben, anhand derer die Post an der Preisschraube drehen darf.\n\nNormalweise geschieht dies alle drei Jahre. Das jetzige Porto gilt seit Anfang 2022, damals verteuerte sich der Inlands-Standardbrief von 80 auf 85 Cent. Andere Brief-Arten wurden ebenfalls teurer. Das jetzige Porto läuft planmäßig Ende 2024 aus.\n\nEs wurde in einer Zeit festgelegt, als die Inflation noch sehr niedrig war. Dass die Regulierungsbehörde bei der damaligen Berechnung des Preiserhöhungskorridors von einer weiterhin recht niedrigen Teuerung ausging, sieht Meyer kritisch. "Das hat das letzte Mal nicht gut funktioniert, dass man bei dem Verfahren eine viel zu niedrige Inflationen angenommen hat."\n\nDer Bonner Logistiker argumentiert, dass seine Kosten zum Betrieb des Brief-Versandnetzes seither stark gestiegen seien. Die Post ist als sogenannter Universaldienstleister das einzige Unternehmen, das überall in Deutschland Briefe zustellen muss - also nicht nur in Städten, wo die Zustellkosten relativ niedrig sind, sondern auch auf dem Land. Außerdem muss sie Pflichten zum Filialnetz, zur Briefkasten-Erreichbarkeit und zur Geschwindigkeit des Briefversands erfüllen./wdw/DP/mis',
  13: 'BONN (dpa-AFX) - Die Deutsche Post\nerwägt wegen deutlich gestiegener Kosten, ein Verfahren zur vorzeitigen Erhöhung des Briefportos anzustoßen. Man prüfe, ob gewisse Parameter erfüllt seien und werde dann entscheiden, sagte Post-Vorstand Tobias Meyer am Mittwoch in Bonn. "Natürlich werden wir uns genau anschauen, welche Möglichkeiten es gibt." Allerdings seien die Hürden für den entsprechenden verwaltungsrechtlichen Akt "nicht niedrig", gab er zu bedenken. Die Post darf das Porto nicht selbst festlegen. Stattdessen macht die Bundesnetzagentur als zuständige Behörde Vorgaben, anhand derer die Post an der Preisschraube drehen darf.\n\nNormalweise geschieht dies alle drei Jahre. Das jetzige Porto gilt seit Anfang 2022, damals verteuerte sich der Inlands-Standardbrief von 80 auf 85 Cent. Andere Brief-Arten wurden ebenfalls teurer. Das jetzige Porto läuft planmäßig Ende 2024 aus.\n\nEs wurde in einer Zeit festgelegt, als die Inflation noch sehr niedrig war. Dass die Regulierungsbehörde bei der damaligen Berechnung des Preiserhöhungskorridors von einer weiterhin recht niedrigen Teuerung ausging, sieht Meyer kritisch. "Das hat das letzte Mal nicht gut funktioniert, dass man bei dem Verfahren eine viel zu niedrige Inflationen angenommen hat."\n\nDer Bonner Logistiker argumentiert, dass seine Kosten zum Betrieb des Brief-Versandnetzes seither stark gestiegen seien. Die Post ist als sogenannter Universaldienstleister das einzige Unternehmen, das überall in Deutschland Briefe zustellen muss - also nicht nur in Städten, wo die Zustellkosten relativ niedrig sind, sondern auch auf dem Land. Außerdem muss sie Pflichten zum Filialnetz, zur Briefkasten-Erreichbarkeit und zur Geschwindigkeit des Briefversands erfüllen./wdw/DP/mis'},
 'art_author': {11: None, 12: None, 13: None},
 'art_abstract': {11: None, 12: None, 13: None},
 'art_video_url': {11: None, 12: None, 13: None},
 'pp_art_text': {11: 'Netfonds AG: Erwerb eigener Aktien - 24. Zwischenmeldung.  Netfonds AG: Erwerb eigener Aktien - 24. Zwischenmeldung.  Im Zeitraum vom 24. April 2023 bis einschliesslich 28. April 2023 hat die Netfonds AG insgesamt 429 Aktien im Rahmen ihres laufenden Aktienrueckkaufprogramms gekauft, das mit der Bekanntmachung vom 11. Oktober 2022 gemaess Art. 5 Abs. 1 lit. a der Verordnung Nr. 596 2014 und Art. 2 Abs. 1 der Delegierten Verordnung Nr. 2016 1052 angekuendigt wurde. Dabei wurden jeweils folgende Stueckzahlen gekauft: Mo. 24. Apr. 23 93 39,89 3.709,60.  Di. 25. Apr. 23 103 39,60 4.078,80.  Mi. 26. Apr. 23 65 39,40 2.561,00.  Do. 27. Apr. 23 87 39,60 3.445,20.  Fr., 28. Apr. 23 81 39,80 3.223,80.  Die Gesamtzahl der im Rahmen des Aktienrueckkaufprogramms seit dem 07. November 2022 bis einschliesslich 28. April 2023 gekauften Aktien belaeuft sich damit auf 11.352 Aktien mit einem Gesamtvolumen von 466.342,60 EUR. Der Erwerb der Aktien der Netfonds AG erfolgt ausschliesslich ueber die Boerse durch ein von der Netfonds AG beauftragtes Kreditinstitut. Detaillierte Informationen ueber die Transaktionen gemaess Art. 2 Abs. 3 Delegierte Verordnung Nr. 2016 1052 sind auf der Internetseite der Netfonds AG im Bereich Investor Relations veroeffentlicht.',
  12: 'Die Deutsche Post erwaegt wegen deutlich gestiegener Kosten, ein Verfahren zur vorzeitigen Erhoehung des Briefportos anzustossen. Man pruefe, ob gewisse Parameter erfuellt seien und werde dann entscheiden, sagte Post-Vorstand Tobias Meyer am Mittwoch in Bonn. Natuerlich werden wir uns genau anschauen, welche Moeglichkeiten es gibt. Allerdings seien die Huerden fuer den entsprechenden verwaltungsrechtlichen Akt nicht niedrig, gab er zu bedenken. Die Post darf das Porto nicht selbst festlegen. Stattdessen macht die Bundesnetzagentur als zustaendige Behoerde Vorgaben, anhand derer die Post an der Preisschraube drehen darf. Normalweise geschieht dies alle drei Jahre. Das jetzige Porto gilt seit Anfang 2022, damals verteuerte sich der Inlands-Standardbrief von 80 auf 85 Cent. Andere Brief-Arten wurden ebenfalls teurer. Das jetzige Porto laeuft planmaessig Ende 2024 aus. Es wurde in einer Zeit festgelegt, als die Inflation noch sehr niedrig war. Dass die Regulierungsbehoerde bei der damaligen Berechnung des Preiserhoehungskorridors von einer weiterhin recht niedrigen Teuerung ausging, sieht Meyer kritisch. Das hat das letzte Mal nicht gut funktioniert, dass man bei dem Verfahren eine viel zu niedrige Inflationen angenommen hat. Der Bonner Logistiker argumentiert, dass seine Kosten zum Betrieb des Brief-Versandnetzes seither stark gestiegen seien. Die Post ist als sogenannter Universaldienstleister das einzige Unternehmen, das ueberall in Deutschland Briefe zustellen muss - also nicht nur in Staedten, wo die Zustellkosten relativ niedrig sind, sondern auch auf dem Land. Ausserdem muss sie Pflichten zum Filialnetz, zur Briefkasten-Erreichbarkeit und zur Geschwindigkeit des Briefversands erfuellen.',
  13: 'Die Deutsche Post erwaegt wegen deutlich gestiegener Kosten, ein Verfahren zur vorzeitigen Erhoehung des Briefportos anzustossen. Man pruefe, ob gewisse Parameter erfuellt seien und werde dann entscheiden, sagte Post-Vorstand Tobias Meyer am Mittwoch in Bonn. Natuerlich werden wir uns genau anschauen, welche Moeglichkeiten es gibt. Allerdings seien die Huerden fuer den entsprechenden verwaltungsrechtlichen Akt nicht niedrig, gab er zu bedenken. Die Post darf das Porto nicht selbst festlegen. Stattdessen macht die Bundesnetzagentur als zustaendige Behoerde Vorgaben, anhand derer die Post an der Preisschraube drehen darf. Normalweise geschieht dies alle drei Jahre. Das jetzige Porto gilt seit Anfang 2022, damals verteuerte sich der Inlands-Standardbrief von 80 auf 85 Cent. Andere Brief-Arten wurden ebenfalls teurer. Das jetzige Porto laeuft planmaessig Ende 2024 aus. Es wurde in einer Zeit festgelegt, als die Inflation noch sehr niedrig war. Dass die Regulierungsbehoerde bei der damaligen Berechnung des Preiserhoehungskorridors von einer weiterhin recht niedrigen Teuerung ausging, sieht Meyer kritisch. Das hat das letzte Mal nicht gut funktioniert, dass man bei dem Verfahren eine viel zu niedrige Inflationen angenommen hat. Der Bonner Logistiker argumentiert, dass seine Kosten zum Betrieb des Brief-Versandnetzes seither stark gestiegen seien. Die Post ist als sogenannter Universaldienstleister das einzige Unternehmen, das ueberall in Deutschland Briefe zustellen muss - also nicht nur in Staedten, wo die Zustellkosten relativ niedrig sind, sondern auch auf dem Land. Ausserdem muss sie Pflichten zum Filialnetz, zur Briefkasten-Erreichbarkeit und zur Geschwindigkeit des Briefversands erfuellen.'},
 'ner_coref': {11: {'sentence': 'Delegierte Verordnung Nr. 2016 1052 sind auf der Internetseite der Netfonds AG im Bereich Investor Relations veroeffentlicht.',
   'entities': [{'start_char': 1200,
     'end_char': 1211,
     'ent_text': 'Netfonds AG',
     'comp_name': 'Netfonds AG',
     'comp_symbol': 'NF4.DE',
     'set_in': 'own_regex_search',
     'df_index': None}]},
  12: {'sentence': 'Die Deutsche Post erwaegt wegen deutlich gestiegener Kosten, ein Verfahren zur vorzeitigen Erhoehung des Briefportos anzustossen.',
   'entities': [{'start_char': 4,
     'end_char': 17,
     'ent_text': 'Deutsche Post',
     'comp_name': 'Deutsche Post AG',
     'comp_symbol': 'DHL.DE',
     'set_in': 'own_regex_search',
     'df_index': None}]},
  13: {'sentence': 'Man pruefe, ob gewisse Parameter erfuellt seien und werde dann entscheiden, sagte Post-Vorstand Tobias Meyer am Mittwoch in Bonn.',
   'entities': [{'start_char': 130,
     'end_char': 133,
     'ent_text': 'Man',
     'comp_name': 'Deutsche Post AG',
     'comp_symbol': 'DHL.DE',
     'set_in': 'xx_coref_resolve',
     'df_index': None}]}},
 'art_id': {11: 19, 12: 39, 13: 39},
 'top_sent': {11: 'Delegierte Verordnung Nr. 2016 1052 sind auf der Internetseite der Netfonds AG im Bereich Investor Relations veroeffentlicht.',
  12: 'Die Deutsche Post erwaegt wegen deutlich gestiegener Kosten, ein Verfahren zur vorzeitigen Erhoehung des Briefportos anzustossen.',
  13: 'Man pruefe, ob gewisse Parameter erfuellt seien und werde dann entscheiden, sagte Post-Vorstand Tobias Meyer am Mittwoch in Bonn.'},
 'top_sent_masked': {11: 'Delegierte Verordnung Nr. 2016 1052 sind auf der Internetseite der Comp@Name@Placeholder im Bereich Investor Relations veroeffentlicht.',
  12: 'Die Comp@Name@Placeholder erwaegt wegen deutlich gestiegener Kosten, ein Verfahren zur vorzeitigen Erhoehung des Briefportos anzustossen.',
  13: 'Comp@Name@Placeholder pruefe, ob gewisse Parameter erfuellt seien und werde dann entscheiden, sagte Post-Vorstand Tobias Meyer am Mittwoch in Bonn.'},
 'topic': {11: 'topic17', 12: 'topic13', 13: 'topic13'},
 'ner_coref_entities': {11: {'start_char': 1200,
   'end_char': 1211,
   'ent_text': 'Netfonds AG',
   'comp_name': 'Netfonds AG',
   'comp_symbol': 'NF4.DE',
   'set_in': 'own_regex_search',
   'df_index': None},
  12: {'start_char': 4,
   'end_char': 17,
   'ent_text': 'Deutsche Post',
   'comp_name': 'Deutsche Post AG',
   'comp_symbol': 'DHL.DE',
   'set_in': 'own_regex_search',
   'df_index': None},
  13: {'start_char': 130,
   'end_char': 133,
   'ent_text': 'Man',
   'comp_name': 'Deutsche Post AG',
   'comp_symbol': 'DHL.DE',
   'set_in': 'xx_coref_resolve',
   'df_index': None}},
 'comp_symbol': {11: 'NF4.DE', 12: 'DBK.DE', 13: 'DHL.DE'},
 'comp_name': {11: 'Netfonds AG',
  12: 'Deutsche Bank AG',
  13: 'Deutsche Post AG'},
'comp_isin': {11: 'isin_not_found', 12: 'DE0005552004', 13: 'DE0005552004'},
 'top_description': {11: 'Alle anderen topics, die den oben genannten 16 topics nicht zugeordnet werden können.',
  12: 'Einflüsse von Aussen auf die Erfolgsaussichten von Unternehmen etwa durch Subventionen, Staatliche Eingriffe, Umbrüche im Markt, politische Veränderungen, Umwelteinflüsse, etc.',
  13: 'Einflüsse von Aussen auf die Erfolgsaussichten von Unternehmen etwa durch Subventionen, Staatliche Eingriffe, Umbrüche im Markt, politische Veränderungen, Umwelteinflüsse, etc.'},
 'sent_id': {11: 11, 12: 12, 13: 13}})

    # print(df)

    ########################### Load ontology and show schema of knowledge graph  ####################################

    kg = GraphConstruction()
    # kg.delete_graph()
    # kg.init_graph(handle_vocab_uris="IGNORE", handle_mult_vals="OVERWRITE")
    # kg.load_onto_or_rdf(path=path_to_onto, path_is_url=False, load_onto_only=True)
    # print('Done!')
    ################################### Load data into Konwledge Graph ###############################################

    # all_jsons = ["data/JSONs/Puma_2022.json", 'data/JSONs/Puma_2023.json']
    # n_data, r_data = get_data_dicts(all_json_paths=all_jsons)

    # kg.load_data_into_knowledge_graph(df=df)
    # print("Done!")
    #################################### Load additional data from wikidata ###########################################
    # """IMPORTANT: This must be run ONLY AFTER a knowledge graph has been created and filled with data !!! """
    # path_to_onto: str = path_base.as_posix() + "/src/models/Ontologies/onto4/Ontology4.ttl"
    # print(path_to_onto)
    # kg = GraphConstruction(path_to_onto=path_to_onto)
    # kg.delete_graph()

    # Get data from wikidata:
    kg.import_wikidata_id(node='Company', node_prop='comp_isin', node_prop_wikidata_id='P946')
    # ################ SET industries #######################
    # industry = {"node_label": "Company",
    #             "prop_name": "comp_isin",
    #             "prop_wiki_id": "P946",
    #             "new_prop_name": "industries",
    #             "new_prop_wiki_id": "P452",
    #             "use_new_prop_label": True,
    #             # new_prop usually is an id such as Q12345 -> True: prop label ("Name") is used
    #             "new_prop_is_list": True,
    #             "prop_wiki_id_is_part_of": None
    # }
    # ################ SET country ############################
    # country = {"node_label": "Company",
    #             "prop_name": "comp_isin",
    #             "prop_wiki_id": "P946",
    #            "new_prop_name": "country",
    #            "new_prop_wiki_id": "P17",
    #            "use_new_prop_label": True,
    #            # new_prop usually is an id such as Q12345 -> True: prop label ("Name") is used
    #            "new_prop_is_list": False,
    # "prop_wiki_id_is_part_of": None}
    # ##############################################################
    # wiki_data = [industry, country]
    # for d in wiki_data:
    #     kg.import_data_from_wikidata(**d)
    #################  Load DBPedia data #########################
    # node_label = "Company"
    # prop_name = "wikidataID"
    # prop_dbp_id = "owl:sameAs"
    # new_prop_name = "abstract"
    # new_prop_dbp_id = "dbo:abstract"
    # new_prop_is_list: bool = False
    # kg.import_data_from_dbpedia(node_label=node_label, prop_name=prop_name, prop_dbp_id=prop_dbp_id,
    #                             new_prop_name=new_prop_name, new_prop_dbp_id=new_prop_dbp_id,
    #                             new_prop_is_list=new_prop_is_list)
    # print("Done!")
    ################# Create text embedding  ####################
    # kg.create_text_embedding(node_label="Sentence", node_primary_prop_name="sent_id", prop_to_embed="sent_text")
    # print("Done!")
