import os
import uuid
from dotenv import load_dotenv
import asyncio
import nest_asyncio
from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain.globals import set_verbose, set_debug

from data_models import Cluster, ClusterHead, DataContainer
from examples import convert_examples_to_messages

load_dotenv('../secrets.env')


class CorefLangchain:
    def __init__(self, prompt_template: str, model_name: str = "gpt-4o"):
        nest_asyncio.apply()
        self.prompt = PromptTemplate(template=prompt_template,
                                     input_variables=["text", "cluster_id", "cluster_head"])
        self.llm = ChatOpenAI(temperature=0, model=model_name, openai_api_key=os.getenv('OPENAI_API_KEY'))
        self.llm = self.llm.with_structured_output(schema=Cluster)
        self.chain = self.prompt | self.llm
        self.examples: list[BaseMessage] = convert_examples_to_messages()

    async def _run_chain(self, text: str, cluster_id: int, cluster_head: dict):
        return await self.chain.ainvoke({"text": text, "cluster_id": cluster_id, "cluster_head": cluster_head, "examples": self.examples})

    # Define a function to run multiple chains concurrently
    async def _run_multiple_chains(self, container: DataContainer) -> list[Cluster]:
        data_list: list[Cluster] = container.data_list
        tasks = [self._run_chain(text=cluster.text, cluster_head=cluster.cluster_head.model_dump(), cluster_id=cluster.cluster_id) for cluster in data_list]
        results = await asyncio.gather(*tasks)
        return results

    def get_coreferences(self, container: DataContainer) -> list[Cluster]:
        return asyncio.run(self._run_multiple_chains(container=container))


if __name__ == '__main__':
    from pprint import pprint
    set_debug(True)
    set_verbose(True)
    from examples import predict_dict
    from prompts import prompt_template_langchain
    cl = CorefLangchain(prompt_template=prompt_template_langchain)
    data1 = Cluster(cluster_id=113, text=predict_dict['text'], cluster_head=predict_dict['cluster_head'])
    text = """"Der Foto-Dienstleister Cewe ist in den ersten neun Monaten des Jahres gewachsen. Damit sieht sich das Management auf Kurs zu seinen Jahreszielen und gut geruestet fuer das wichtige Weihnachtsgeschaeft. Das teilte der SDax -Konzern am Freitag in Oldenburg mit."""
    cluster_head = ClusterHead(head_text="Foto-Dienstleister Cewe", head_index_start=4, head_index_end=26)
    data2 = Cluster(cluster_id=209, text=text, cluster_head=cluster_head)
    container = DataContainer()
    container.data_list.append(data1)
    container.data_list.append(data2)
    cd = container.data_list
    results = cl.get_coreferences(container=container)
    for result in results:
        pprint(result)
        print(type(result))
        print('######################################################################################')