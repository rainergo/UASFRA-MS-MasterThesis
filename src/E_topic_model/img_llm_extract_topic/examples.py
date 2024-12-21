"""This is from: https://python.langchain.com/v0.1/docs/use_cases/extraction/how_to/examples/ """
from typing import List
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from data_models import Topic, Frame
from topics import top1, top2, top3, top4, top5, top6, top7, top8, top9, top10, top11, top12, top13, top14, top15, top16


""" SAMPLES """
examples = []

tops = [top1, top2, top3, top4, top5, top6, top7, top8, top9, top10, top11, top12, top13, top14, top15, top16]
top_enums = [Topic.topic1, Topic.topic2, Topic.topic3, Topic.topic4, Topic.topic5, Topic.topic6, Topic.topic7, Topic.topic8, Topic.topic9, Topic.topic10,
    Topic.topic11, Topic.topic12, Topic.topic13, Topic.topic14, Topic.topic15, Topic.topic16, Topic.topic17]

for top, en in zip(tops, top_enums):
    sentences = [sent for sent in top]
    indexes = [i for i in range(len(sentences))]
    topics = [en for _ in range(len(sentences))]
    examples.append(Frame(indexes=indexes, sentences=sentences, topics=topics))


def _convert_example_to_message(frame: Frame) -> List[BaseMessage]:
    human_content: str = f"indexes: {frame.indexes}, sentences: {frame.sentences}"
    ai_content: str = f"indexes: {frame.indexes}, topics: {frame.topics}"
    messages: List[BaseMessage] = [HumanMessage(content=human_content), AIMessage(content=ai_content)]
    return messages


def convert_examples_to_messages() -> list[BaseMessage]:
    messages = []
    for example in examples:
        messages.extend(
            _convert_example_to_message(frame=example)
        )
    return messages


if __name__ == '__main__':
    from pprint import pprint
    pprint(convert_examples_to_messages())