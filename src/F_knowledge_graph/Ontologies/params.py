""" Please also read the README-models.md-file. """

"""
Parameters for NewsArticles.ttl:
:param: unique_node_keys: unique_node_keys are comparable to primary keys in relational databases and are the
        node properties that must be unique. They must be provided for each node as a dictionary in the form:
        {"node_label":["node_property_name"]}. Example: {"Company":["LEI"]}
:param: node_value_props: Of the datatype properties of target nodes (i.e. Nodes that have an incoming relationship
        from a source node), one such property is used for the property of the relationship. Example in cypher:
        MATCH (s:SourceNode)-[r:Relationship]->[t:TargetNode]. If the TargetNode 't' has a quantity property 'EUR' to
        express the value of the TargetNode 't', then this property is the quantity property of the Relationship 'r'. In
        the example here, 'EUR' would be the quantity property of the Relationship 'r', if 'EUR' would be set in the
        node_value_props dictionary like so: node_value_props = {'TargetNode':'EUR'}
"""

unique_node_keys = {"Article": ["art_id"],
                    "Company": ["comp_symbol"],
                    "Sentence": ["sent_id"],
                    "Topic": ["top_id"],
                    }

node_value_props = {"Article": "art_id",
                    "Company": "comp_symbol",
                    "Topic": "top_id",
                    }

# df = pd.DataFrame(data=
#     {
#
#         'art_id': ['text 1', 'text 2', 'text 3'],
#         'art_text': ['text 1', 'text 2', 'text 3'],
#         'art_datetime': ['2008/12/1', '2008/12/2', '2008/12/3'],
#
#         'comp_name': ['comp1', 'comp2', 'comp3'],
#         'comp_symbol': ['aaa.F', 'bbb.D', 'ccc.GB'],
#
#         'sent_id': ['sen1', 'sen2', 'sen3'],
#         'sent_text': ['topic 1 sent text', 'topic 2 sent text', 'topic 3 sent text'],
#
#         'top_id': ['top1', 'top2', 'top3'],
#         'top_description': ['top1 description', 'top2 description', 'top3 description'],
#     })