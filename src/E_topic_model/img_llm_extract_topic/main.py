import pandas as pd
from fastapi import FastAPI, Depends, Query

from topic_langchain import TopicLangchain
from prompts import prompt_template_langchain
from data_models import Frame

# Initialize FastAPI app
app = FastAPI()


topic_langchain: TopicLangchain = TopicLangchain(prompt_template=prompt_template_langchain)


# Define FastAPI endpoints
@app.post("/", response_model_exclude_none=True)
async def get_topic(frame: Frame):
    df = pd.DataFrame(data=frame.model_dump(exclude_none=True))
    return topic_langchain.get_topics(df=df)



