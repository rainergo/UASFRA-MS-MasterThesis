import requests
import pandas as pd
import numpy as np
from pathlib import Path
import concurrent.futures
import traceback
from typing import Callable, Generator
from functools import reduce
from spacy.language import Language
import time

from src.settings.config import ConfigBasic
from src.settings.enums import NaturalLanguage, SpacyTask, ExtractionType
from src.B_spacy_pipeline.spacy_pipe_process import SpacyPipeProcess
from src.B_spacy_pipeline.spacy_pipe_funcs import PipeFunc
from src.E_topic_model.img_llm_extract_topic.data_models import Frame, TopicExplain
from src.A_data.data_loader import DataLoader


class SpacyProcess:

    def __init__(self, spacy_task: SpacyTask, ner_method: ExtractionType = ExtractionType.PRETRAINED, coref_method: ExtractionType = ExtractionType.PRETRAINED):
        # Note: GPU does not work with multi-threading, use CPU:
        use_gpu = False
        self.nlp_en: Language = SpacyPipeProcess(natural_language=NaturalLanguage.EN, spacy_task=spacy_task, ner_method=ner_method, coref_method=coref_method, use_gpu=use_gpu).nlp
        self.nlp_de: Language = SpacyPipeProcess(natural_language=NaturalLanguage.DE, spacy_task=spacy_task, ner_method=ner_method, coref_method=coref_method, use_gpu=use_gpu).nlp

    def reduce_pipe(self):
        en_pipes_needed = ['transformer', 'tagger', 'parser', 'lemmatizer']
        for pipe in en_pipes_needed:
            if pipe not in self.nlp_en.pipe_names:
                self.nlp_en.enable_pipe(pipe)
        for pipe in self.nlp_en.pipe_names:
            if pipe not in en_pipes_needed:
                self.nlp_en.disable_pipe(pipe)
        de_pipes_needed = ['tok2vec', 'tagger', 'morphologizer', 'parser', 'lemmatizer']
        for pipe in de_pipes_needed:
            if pipe not in self.nlp_de.pipe_names:
                self.nlp_de.enable_pipe(pipe)
        for pipe in self.nlp_de.pipe_names:
            if pipe not in de_pipes_needed:
                self.nlp_de.disable_pipe(pipe)

    def process_text(self, text: str, lang: NaturalLanguage) -> list[dict]:
        if isinstance(text, str):
            if lang == NaturalLanguage.EN:
                doc = self.nlp_en(text)
                return PipeFunc.get_sentences_with_custom_extensions(processed_doc=doc)
            elif lang == NaturalLanguage.DE:
                doc = self.nlp_de(text)
                return PipeFunc.get_sentences_with_custom_extensions(processed_doc=doc)
            else:
                raise ValueError(f'Language {lang} is not supported')

    @staticmethod
    def concurrent_df_apply(df: pd.DataFrame, function: Callable, df_col_name_1: str, df_col_name_2: str, name_new_col: str):
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(df.index)) as executor:
            generator: Generator = executor.map(function,df[df_col_name_1], df[df_col_name_2])
            try:
                df[name_new_col] = list(generator)
            except (Exception, TimeoutError):
                print(f'Fetching concurrent.future failed: {traceback.format_exc()}')
                print('--------------------------------------------------------------')
            return df

    def run_spacy_pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        return SpacyProcess.concurrent_df_apply(df=df, function=self.process_text, df_col_name_1='pp_art_text', df_col_name_2='art_language', name_new_col='ner_coref')

    @staticmethod
    def mask_sent(comp_dict, mask: str = "Comp@Name@Placeholder") -> str:
        sent = pd.NA
        if isinstance(comp_dict, dict):
            replacements: dict = {ent['ent_text']: mask for ent in comp_dict['entities']}
            sent: str = comp_dict['sentence']
            sent = reduce(lambda x, kv: x.replace(*kv), replacements.items(), sent)
        return sent

    @staticmethod
    def convert_nested_ner_coref_dict(df: pd.DataFrame) -> pd.DataFrame:
        df['art_id'] = df.index
        df = df.explode('ner_coref').reset_index(drop=True)
        df['top_sent'] = df['ner_coref'].str['sentence'].astype(object).replace(np.nan, pd.NA)
        df['top_sent_masked'] = df['ner_coref'].apply(SpacyProcess.mask_sent)
        return df


class Process:
    def __init__(self):
        self.topic_gen_llm_docker_container_url: str = 'http://127.0.0.1:54321'

    def prepare_df_for_kg(self, df: pd.DataFrame) -> pd.DataFrame:
        # df = df[df.duplicated(subset=['ner_coref'])]
        df['ner_coref_entities'] = df.ner_coref.str['entities']
        df = df.explode('ner_coref_entities').reset_index(drop=True)
        df['comp_symbol'] = df.ner_coref_entities.str['comp_symbol']
        df['comp_name'] = df.ner_coref_entities.str['comp_name']
        df['top_description'] = df.topic.apply(lambda x: TopicExplain[x].value)
        df.drop_duplicates(subset=['top_sent', 'comp_symbol', 'comp_name'], keep='last', inplace=True)
        df = self._drop_nans(df)
        df = self._get_isin(df)
        # df = df[~df.duplicated(subset=['ner_coref_entities'])]
        return df

    def _drop_nans(self, df: pd.DataFrame) -> pd.DataFrame:
        df.dropna(subset=['ner_coref', 'top_sent', 'topic'], inplace=True)
        df.reset_index(drop=False, inplace=True)
        df['sent_id'] = df.index.tolist()
        return df

    def _load_comp_isin_df(self) -> pd.DataFrame:
        dl = DataLoader()
        path = Path(ConfigBasic.path_to_comp_symbol_isin_data)
        df_symb_isin = dl.load_df(path=path, dtype={'CompanyName': 'string', 'ISIN': 'string'}, columns=['ISIN', 'Symbol'])
        df_symb_isin = df_symb_isin.rename(columns={'Symbol': 'comp_symbol_raw', 'ISIN':'comp_isin'})
        return df_symb_isin

    def _get_isin(self, df: pd.DataFrame) -> pd.DataFrame:
        df[['comp_symbol_raw', 'comp_symbol_country']] = df.comp_symbol.str.split('.').apply(pd.Series).fillna(pd.NA)
        df_symb_isin = self._load_comp_isin_df()
        df_merged = pd.merge(df, df_symb_isin[['comp_symbol_raw', 'comp_isin']], on='comp_symbol_raw', how='left')
        df_merged.fillna(value={'comp_isin': 'isin_not_found'}, inplace=True)
        return df_merged

    def get_topics_from_gen_llm(self, df: pd.DataFrame, chunk_size: int = 30, df_col_name: str = 'topic') -> pd.DataFrame:
        if 'top_sent' not in df.columns:
            raise ValueError('No "top_sent" columns')
        indexes = []
        topics = []
        for idx_start in range(0, len(df.index), chunk_size):
            df_chunk = df.iloc[idx_start:idx_start + chunk_size]
            print('df_chunk.index.tolist():', df_chunk.index.tolist())
            frame = Frame.df_to_instance(df_chunk)
            print('frame.indexes', frame.indexes)
            try:
                resp = requests.post(url=self.topic_gen_llm_docker_container_url, json=frame.dict(exclude_none=True))
                if resp.ok:
                    chunk_indexes = resp.json()['indexes']
                    print('chunk_indexes:', chunk_indexes)
                    indexes.extend(chunk_indexes)
                    chunk_topics = resp.json()['topics']
                    print('chunk_topics:', chunk_topics)
                    topics.extend(chunk_topics)
                else:
                    print(f'Error occurred. Will try again... ')
                    time.sleep(2)
                    resp = requests.post(url=self.topic_gen_llm_docker_container_url, json=frame.dict(exclude_none=True))
                    if resp.ok:
                        chunk_indexes = resp.json()['indexes']
                        print('chunk_indexes (2):', chunk_indexes)
                        indexes.extend(chunk_indexes)
                        chunk_topics = resp.json()['topics']
                        print('chunk_topics (2):', chunk_topics)
                        topics.extend(chunk_topics)
                    else:
                        print(f'Error occured the second time, could not be cured: {resp.text}')
                        indexes.extend([i for i in range(idx_start, idx_start + chunk_size)])
                        topics.extend(['topic17' for _ in range(idx_start, idx_start + chunk_size)])
                print('DEBUG INFO:', topics)
            except:
                print(f'Error occured: {traceback.format_exc()}')
                indexes.extend([i for i in range(idx_start, idx_start + chunk_size)])
                topics.extend(['topic17' for _ in range(idx_start, idx_start + chunk_size)])

            time.sleep(1)

        df[df_col_name] = topics
        return df


if __name__ == '__main__':
    data = {'indexes': [1,2], 'top_sent': ['Insgesamt machte das Unternehmen im Geschaeftsjahr 2022 23 ein operatives Minus von 1,04 Milliarden Pfund und riss damit auch das Ergebnis des Mutterkonzerns Comp@Name@Placeholder tief in die roten Zahlen.', pd.NA]}
    df = pd.DataFrame(data)
    p = Process()
    print(p.get_topics_from_gen_llm(df))


