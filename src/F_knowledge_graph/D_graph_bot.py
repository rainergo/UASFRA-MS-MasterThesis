import os
import pathlib
from dotenv import load_dotenv

from langchain.chains import GraphCypherQAChain
from langchain_openai.chat_models import ChatOpenAI
from langchain_core.prompts.prompt import PromptTemplate
from langchain_community.graphs import Neo4jGraph

from src.settings.config import ConfigBasic


class GraphBot:
    rels_explanation = """
    # Relationship 1: (:Sentence)-[:is_about {{top_id}}]->(:Topic)
    # Relationship 1 explanation: A Sentence is about a particular Topic that has a Topic identification number or "top_id".
    # Relationship 2: (:Sentence)-[:is_part_of {{art_id}}]->(:Article)
    # Relationship 2 explanation: A Sentence is contained in and part of an Article that has an Article identification number or "art_id".
    # Relationship 3: (:Sentence)-[:mentions {{comp_symbol}}]->(:Company)
    # Relationship 3 explanation: A Sentence mentions the name of a Company that has a stock exchange ticker symbol ("comp_symbol").
    """
    nodes_and_their_attributes = """
    Node "Article": [{{art_id: "The id of the article"}}, {{art_datetime: "The date and time the article was published"}}, {{art_text: "The content of the article"}}, {{art_source: "The media company that published the article"}}]
    Node "Company": [{{comp_symbol: "The stock ticker symbol for that company on a stock exchange"}}, {{comp_isin: "The security identifier number 'ISIN' for that company on a stock exchange"}}, {{comp_name: "The name of the company"}}]
    Node "Sentence": [{{sent_id: "The sentence identification number"}}, {{sent_text: "The sentence text"}}]
    Node "Topic": [{{top_id: "The topic identification number"}}, {{top_description: "The description the topic is all about"}}]
    """
    examples = """
    # Example question 1: Show me all the companies that were mentioned in articles published on 2023-05-03?
    # Cypher statement to question 1:
    MATCH (s:Sentence)-[:is_part_of]->(a:Article)
    WITH s as sent, a as article, Date(a.art_datetime) as date
    MATCH (sent)-[:mentions]->(c:Company)
    WHERE date = Date({{year: 2023, month: 5, day: 3}})
    RETURN DISTINCT c.comp_name
    
    # Example question 2: Show me all articles with company mentions published on 2023-05-03 and the text of the articles?
    # Cypher statement to question 2:
    MATCH (s:Sentence)-[:is_part_of]->(a:Article)
    WITH s as sent, a as article, Date(a.art_datetime) as date
    MATCH (sent)-[:mentions]->(c:Company)
    WHERE date = Date({{year: 2023, month: 5, day: 3}})
    RETURN DISTINCT article.art_text
    
    # Example question 3: Show me all the companies that were mentioned in articles published on 2023-05-03 and the sentences in which they were mentioned?
    # Cypher statement to question 3:
    MATCH (s:Sentence)-[:is_part_of]->(a:Article)
    WITH s as sent, a as article, Date(a.art_datetime) as date
    MATCH (sent)-[:mentions]->(c:Company)
    WHERE date = Date({{year: 2023, month: 5, day: 3}})
    RETURN DISTINCT c.comp_name, sent.sent_text
    
    # Example question 4: Show me all the sentences and their topic IDs of articles that were published on 2023-05-03?
    # Cypher statement to question 4:
    MATCH (s:Sentence)-[:is_part_of]->(a:Article)
    WITH s as sent, a as article, Date(a.art_datetime) as date
    MATCH (sent)-[:is_about]->(t:Topic)
    WHERE date = Date({{year: 2023, month: 5, day: 3}})
    RETURN DISTINCT t.top_id, sent.sent_text
    
    # Example question 4: Show me all the companies and the sentences they were mentioned of articles that were published between 2023-05-02 and 2023-05-03?
    # Cypher statement to question 4:
    MATCH (s:Sentence)-[:is_part_of]->(a:Article)
    WITH s as sent, a as article, Date(a.art_datetime) as art_date
    MATCH (sent)-[:mentions]->(c:Company)
    WHERE Date({{year: 2023, month: 5, day: 2}}) <=  art_date <= Date({{year: 2023, month: 5, day: 3}})
    RETURN DISTINCT c.comp_name, sent.sent_text
    """

    def __init__(self):
        path_to_secrets: pathlib.Path = ConfigBasic.path_to_secrets
        try:
            load_dotenv(dotenv_path=path_to_secrets)  # Load secrets/env variables
        except:
            print('secrets could not be loaded!')
        uri = "neo4j://localhost:7687"
        neo4j_user = os.getenv('NEO4J_USER')
        neo4j_pw = os.getenv('NEO4J_PW')
        openai_key = os.getenv("OPENAI_API_KEY")
        self.graph = Neo4jGraph(url=uri, username=neo4j_user, password=neo4j_pw)
        self.graph.refresh_schema()
        self.chat_llm = ChatOpenAI(temperature=0, openai_api_key=openai_key, model='gpt-4o')

    def get_schema(self):
        return self.graph.schema

    def create_prompt(self):
        """ IMPORTANT: The PromptTemplate is optimized for graphs and only accepts TWO input_variables (schema, question).
        Additional variables need to be inserted via f-string variables, such as 'self.rels_explanation' and
        'self.examples' in this prompt.
        """
        cypher_prompt = f"""
        Task: Generate pure Cypher statement to query a Neo4j graph database.
        Instructions:
        Use only the provided relationship types and properties in the schema.
        Do not use any other relationship types or properties that are not provided.
        Do not insert any comment in the query.
        The following are all the relationships with their property being an attribute of the target Node:
        {self.rels_explanation}
        Do also take into consideration that Nodes can only have the following attributes (with their "explanations in quotation marks") respectively:
        {self.nodes_and_their_attributes}
        Other labels for Nodes are not allowed.
        Do take into account that an attribute of the target Node is always stored as the property value of the
        relationship. For instance, given the Relationship pattern "(:source Node)-[Relationship:property]->(:target Node):",
        the quantity or property value of the target Node is given as the property of the Relationship.
        Schema:
        {{schema}}
        Note: Do not include any explanations or apologies in your responses.
        Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.
        Do not include any text except the generated Cypher statement.
        Examples: Here are a few examples of generated Cypher statements for particular questions:
        {self.examples}
        
        Now, the question is:
        {{question}}
        """
        CYPHER_GENERATION_PROMPT = PromptTemplate(
            input_variables=["schema", "question"], template=cypher_prompt
        )
        return CYPHER_GENERATION_PROMPT

    def create_chain(self, prompt: PromptTemplate):
        return GraphCypherQAChain.from_llm(llm=self.chat_llm, graph=self.graph,
                                           cypher_prompt=prompt, verbose=True,
                                           return_intermediate_steps=True)

    def ask_question(self, question: str):
        prompt = self.create_prompt()
        chain = self.create_chain(prompt=prompt)
        answer = chain.invoke(question)['result']
        return answer


if __name__ == '__main__':
    qa = GraphBot()
    question = ("Show me all company names (comp_name) and the sentence text of the articles in which they were mentioned and "
                "that were published between 2023-05-02 and 2023-05-04")
    print('Question:\n', question)
    ans = qa.ask_question(question=question)
    print('Answer:\n', ans)

    # qa = GraphBot()
    # print(qa.get_schema())
    # question = "Show me all the companies and the sentences they were mentioned of articles that were published between 2023-05-02 and 2023-05-03"
    # # question = "Show me all the sentences and their topic IDs of articles that were published on 2023-05-03?"
    # # question = "Show me all the companies that were mentioned in articles published on 2023-05-03?"
    # print('Question:\n', question)
    # ans = qa.ask_question(question=question)
    # from pprint import pprint
    #
    # print('Answer:\n')
    # pprint(ans)
