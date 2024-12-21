import json
from importlib.machinery import SourceFileLoader
from pathlib import Path
from rdflib import Graph
from rdflib.namespace import RDFS, RDF, OWL

from src.settings.config import ConfigGraph


class RDFGraph:
    """ This class creates cypher query templates based on a given ontology and based on Node properties as described by
    two Python dictionaries:
        - unique_node_keys
        - node_value_props
    """

    def __init__(self, path_to_onto: Path, rdf_format: str = "ttl"):
        self.rdf_graph: Graph = Graph()
        self.nodes_data_needed = dict()
        self.rels_data_needed = dict()
        self.path_to_onto: Path = path_to_onto
        try:
            self.rdf_graph.parse(self.path_to_onto, format=rdf_format)
        except:
            print('ERROR: rdf_graph could not be parsed!')
        params = SourceFileLoader('params', Path(path_to_onto.parent, 'params.py').as_posix()).load_module()
        self.unique_node_keys: dict[str, list[str]] = params.unique_node_keys
        self.node_value_props: dict[str, str] = params.node_value_props

    def get_local_part(self, uri: str):
        pos = -1
        pos = uri.rfind('#')
        if pos < 0:
            pos = uri.rfind('/')
        if pos < 0:
            pos = uri.rindex(':')
        return uri[pos + 1:]

    def get_namespace_part(self, uri: str):
        pos = -1
        pos = uri.rfind('#')
        if pos < 0:
            pos = uri.rfind('/')
        if pos < 0:
            pos = uri.rindex(':')
        return uri[0:pos + 1]

    def get_nodes_and_node_props(self) -> tuple[dict, list]:
        # Get classes and their DatatypeProperties
        nodes_with_props = dict()
        all_nodes = list()
        for (subj1, pred1, obj1) in self.rdf_graph.triples((None, RDF.type, OWL.Class)):
            all_nodes.append(self.get_local_part(subj1))
            for (subj2, pred2, obj2) in self.rdf_graph.triples((None, RDFS.domain, subj1)):
                for (subj3, pred3, obj3) in self.rdf_graph.triples((subj2, RDF.type, OWL.DatatypeProperty)):
                    node = self.get_local_part(subj1)
                    if not node in nodes_with_props:
                        nodes_with_props[node] = list()
                    nodes_with_props[node].append(self.get_local_part(subj3))
        nodes_without_props = [key for key in all_nodes if key not in nodes_with_props]
        return nodes_with_props, nodes_without_props

    def get_relationships(self) -> list:
        # Get ObjectProperties (Relationships) for each Class:
        relationships = list()
        for (subj1, pred1, obj1) in self.rdf_graph.triples((None, RDF.type, OWL.ObjectProperty)):
            for (subj2, pred2, obj2) in self.rdf_graph.triples((subj1, RDFS.domain, None)):
                for (subj3, pred3, obj3) in self.rdf_graph.triples((subj1, RDFS.range, None)):
                    relationships.append({'SOURCE': self.get_local_part(obj2), 'TARGET': self.get_local_part(obj3),
                                          'REL': self.get_local_part(subj1)})
        return relationships

    def get_namespaces(self) -> set:
        namespaces = set()
        for (subj1, pred1, obj1) in self.rdf_graph.triples((None, RDF.type, OWL.Class)):
            for (subj2, pred2, obj2) in self.rdf_graph.triples((None, RDFS.domain, subj1)):
                for (subj3, pred3, obj3) in self.rdf_graph.triples((subj2, RDF.type, OWL.DatatypeProperty)):
                    namespaces.add(subj1)
                    namespaces.add(subj3)
        for (subj11, pred11, obj11) in self.rdf_graph.triples((None, RDF.type, OWL.ObjectProperty)):
            namespaces.add(subj11)
        return namespaces

    def create_query_templates(self):
        """ Creates four types of queries: constraint queries, nodes_and_props queries, node_relationship queries and
        namespace_queries.
        """
        if self.unique_node_keys is None or self.node_value_props is None:
            raise ValueError("Either 'unique_node_keys' or 'node_value_props' or both are not provided!")

        def check_if_class_keys_are_set():
            nodes_and_nodes_props, nodes_without_props = self.get_nodes_and_node_props()
            error_messages = list()
            for node, node_props in nodes_and_nodes_props.items():
                if node in self.unique_node_keys:
                    if not self.unique_node_keys[node]:
                        error_messages.append(f'No key property provided for Node "{node}" in unique_node_keys.')
                    for prop in self.unique_node_keys[node]:
                        if prop in nodes_and_nodes_props[node]:
                            pass
                        else:
                            error_messages.append(
                                f'Provided key property "{prop}" is not a correct (key) property for Node "{node}"!')
                else:
                    error_messages.append(f'No key property provided for Node "{node}"!')
            if error_messages:
                raise ValueError(f'These errors must be corrected first: {error_messages}')

        def check_if_node_value_props_are_set():
            # Get target Nodes:
            targets: list = [rel["TARGET"] for rel in self.get_relationships()]
            node_and_node_props, nodes_without_props = self.get_nodes_and_node_props()
            nodes_without_props_in_targets = [item for item in targets if item in nodes_without_props]
            if nodes_without_props_in_targets:
                raise ValueError(
                    f'These target Nodes have no properties. Thus relation values cannot be set: {nodes_without_props_in_targets}')

            node_value_props_missing = [item for item in targets if item not in self.node_value_props]
            if node_value_props_missing:
                raise ValueError(f'node_value_props not set for these target Nodes: {node_value_props_missing}')

            node_value_props_incorrect = list()
            for node in targets:
                node_props: list = node_and_node_props[node]
                node_prop = self.node_value_props[node]
                if node_prop not in node_props:
                    node_value_props_incorrect.append(
                        f"Provided Node property '{node_prop}' is not valid for Node '{node}'!")
            if node_value_props_incorrect:
                raise ValueError(f'Please check these errors: {node_value_props_incorrect}')

        def create_node_property_constraint_queries():
            contraint_queries = list()
            for node, prop_list in self.unique_node_keys.items():
                if prop_list:
                    query = f"""
                    CREATE CONSTRAINT constraint_for_node_{node} IF NOT EXISTS
                    FOR (node:{node}) REQUIRE ({', '.join(['node.' + prop for prop in prop_list])}) IS UNIQUE;
                    """
                    contraint_queries.append(query)
            return contraint_queries

        def create_query_template_for_classes_and_their_props() -> (list[str], set):
            # Get nodes_and_nodes_props for each Class
            nodes_and_nodes_props, nodes_without_props = self.get_nodes_and_node_props()
            node_queries = dict()
            for node, node_props in nodes_and_nodes_props.items():
                key_properties: list = self.unique_node_keys[node]
                if node in self.node_value_props:
                    value_properties: list = self.node_value_props[node]
                else:
                    value_properties: list = list()
                props_queries = list()
                nodes_datapoint_needed = dict()
                for prop in node_props:
                    if prop not in value_properties:
                        nodes_datapoint_needed[prop] = f"<HERE_{prop}_VALUE>"
                        if prop not in key_properties:
                            props_queries.append(f'SET n.{prop} = node_data["{node}"]["{prop}"]')
                self.nodes_data_needed[node] = nodes_datapoint_needed
                props_queries.append("RETURN count(*) as total")
                query_part_2 = ' \n\t\t\t\t'.join(props_queries)
                additional_query_part_1 = ' { ' + ', '.join(
                    [f"{key_prop}: node_data['{node}']['{key_prop}']" for key_prop in
                     key_properties]) + ' } ' if key_properties else ''
                query_part_1 = f"""
                WITH $node_data AS node_data 
                MERGE (n:{node}{additional_query_part_1})
                """
                node_queries[node] = str(query_part_1 + query_part_2)
            return node_queries

        def create_query_template_for_class_relationships() -> dict[str:str]:
            # Get ObjectProperties (Relationships) for each Class:
            relationships = self.get_relationships()
            # Build the queries:
            relationship_queries = dict()
            for rel in relationships:
                source = rel['SOURCE']
                target = rel['TARGET']
                relation_only = rel['REL']
                relation = f"{source}_{rel['REL']}_{target}"
                rels_datapoint_needed = {"source": {f"{source}": dict()}, "target": {f"{target}": dict()}}
                # Data for source:
                if source in self.unique_node_keys and self.unique_node_keys[source]:
                    source_keys: list = self.unique_node_keys[source]
                    source_properties = list()
                    for source_key in source_keys:
                        source_property = f'{source_key}: rel_data["{relation}"]["source"]["{source}"]["{source_key}"]'
                        source_properties.append(source_property)
                        rels_datapoint_needed['source'][source][source_key] = f"<HERE_{source_key}_VALUE>"
                    source_properties = " { " + ", ".join(source_properties) + " } "
                else:
                    source_properties = ''
                # Data for target:
                relation_property = None
                if target in self.unique_node_keys and self.unique_node_keys[target]:
                    target_keys: list = self.unique_node_keys[target]
                    target_properties = list()
                    for target_key in target_keys:
                        target_property = f'{target_key}: rel_data["{relation}"]["target"]["{target}"]["{target_key}"]'
                        target_properties.append(target_property)
                        rels_datapoint_needed['target'][target][target_key] = f"<HERE_{target_key}_VALUE>"
                    target_properties = " { " + ", ".join(target_properties) + " } "
                else:
                    target_properties = ''

                """
                IMPORTANT:
                Data for relationship: Please note, that the values for the target will be stored in the relationship.
                """
                # Data for relationship:
                if target in self.node_value_props:
                    value_prop = self.node_value_props[target]
                    relation_property = f' {{ {value_prop}: rel_data["{relation}"]["target"]["{target}"]["{value_prop}"] }}'
                    rels_datapoint_needed["target"][target][value_prop] = f"<HERE_{value_prop}_VALUE>"
                self.rels_data_needed[relation] = rels_datapoint_needed
                query = f"""
                WITH $rel_data AS rel_data
                MATCH (source:{source}{source_properties})
                MATCH (target:{target}{target_properties})
                MERGE (source)-[r:{relation_only}{relation_property}]->(target)
                RETURN count(*) as total
                """
                relationship_queries[relation] = query
            return relationship_queries

        def create_namespace_queries(namespaces: set) -> list:
            queries = list()
            namespace_prefixes = {self.get_namespace_part(uri=uri) for uri in namespaces}
            counter = 0
            for ns_prefix in namespace_prefixes:
                query_prefix = f"CALL n10s.nsprefixes.add('ns{counter}','{ns_prefix}');"
                queries.append(query_prefix)
                counter += 1
            for ns in namespaces:
                query = f"CALL n10s.mapping.add('{ns}', '{self.get_local_part(ns)}');"
                queries.append(query)
            return queries

        check_if_class_keys_are_set()
        check_if_node_value_props_are_set()
        constraint_queries: list = create_node_property_constraint_queries()
        node_queries: dict[str:str] = create_query_template_for_classes_and_their_props()
        relationship_queries: dict[str:str] = create_query_template_for_class_relationships()
        namespaces: set = self.get_namespaces()
        namespace_queries: list = create_namespace_queries(namespaces=namespaces)

        return constraint_queries, node_queries, relationship_queries, namespace_queries

    def create_json_files_for_data_needed(self):
        # if len(self.nodes_data_needed) == 0 or len(self.rels_data_needed):
        #     raise ValueError("Please run 'create_query_templates()'-method first !")
        path_to_data_needed: Path = self.path_to_onto.parent / "data_needed"
        for k1, v1 in self.nodes_data_needed.items():
            path_nodes: Path = path_to_data_needed / f'{k1}.json'
            with open(path_nodes, 'w') as file:
                d1 = {k1: v1}
                json.dump(d1, file)
        for k2, v2 in self.rels_data_needed.items():
            path_rels: Path = path_to_data_needed / f'{k2}.json'
            with open(path_rels, 'w') as file:
                d2 = {k2: v2}
                json.dump(d2, file)


if __name__ == '__main__':

    g = RDFGraph(path_to_onto=ConfigGraph.path_to_onto)

    nodes_w_props, nodes_wo_props = g.get_nodes_and_node_props()
    print('nodes_w_props:', nodes_w_props, '- nodes_wo_props:', nodes_wo_props)
    print(g.get_relationships())

    # # # Create query templates:
    # constr_queries, node_queries, rel_queries, ns_queries, = g.create_query_templates()
    # #  Show all the query templates:
    # print('CONSTRAINT_QUERIES:')
    # for constr in constr_queries:
    #     print(constr)
    # print('-----')
    # print('NAMESPACE_QUERIES:')
    # for ns in ns_queries:
    #     print(ns)
    # print('-----')
    # print('NODE_QUERIES:')
    # for node_key, node_val in node_queries.items():
    #     print(node_key, node_val)
    #     print('-----')
    # print('RELATIONSHIP_QUERIES:')
    # for rel_key, rel_val in rel_queries.items():
    #     print(rel_key)
    #     print(rel_val)
    # print('-----')
    # print('NODES_DATA_NEEDED:')
    # print(g.nodes_data_needed)
    # print('------')
    # print('RELS_DATA_NEEDED:')
    # print(g.rels_data_needed)
    # # Create the "data_needed" JSON-files and store them in "data_needed"-folder
    # g.create_json_files_for_data_needed()
