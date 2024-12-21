from fastapi import FastAPI, Depends
from pydantic import BaseModel

from coref_solver import CorefResolver, NaturalLanguage

# Initialize FastAPI app
app = FastAPI()

coref_res_de = CorefResolver(natural_language=NaturalLanguage.DE)
coref_res_en = CorefResolver(natural_language=NaturalLanguage.EN)


class Entity(BaseModel, frozen=True):
    text: str

    __hash__ = object.__hash__


# Define FastAPI endpoints
@app.get("/en")
async def get_cluster(entity: Entity = Depends()):
    return coref_res_en.get_cluster(text=entity.text)


@app.get("/de")
async def get_cluster(entity: Entity = Depends()):
    return coref_res_de.get_cluster(text=entity.text)
