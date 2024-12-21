FROM python:3.10

WORKDIR /code

COPY /img_xx_coref_files/coref_solver.py /code/coref_solver.py
COPY /img_xx_coref_files/models /code/models
COPY /img_xx_coref_files/main /code/main
COPY /requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

RUN python -m spacy download de_core_news_lg
RUN python -m spacy download en_core_web_lg

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]