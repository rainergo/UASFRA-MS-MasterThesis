from fastapi import FastAPI, Depends, Query
from pydantic import BaseModel, Field
from fastapi.encoders import jsonable_encoder

from coref_langchain import CorefLangchain
from prompts import prompt_template_langchain
from data_models import Cluster, DataContainer

# Initialize FastAPI app
app = FastAPI()


coref_langchain: CorefLangchain = CorefLangchain(prompt_template=prompt_template_langchain)


# Define FastAPI endpoints
@app.post("/")
async def get_cluster(container: DataContainer):
    return coref_langchain.get_coreferences(container=container)



