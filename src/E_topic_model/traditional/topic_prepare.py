import re
import string
import json
from pathlib import Path

import pandas as pd
import spacy
from spacy.language import Tokenizer, Language
from pprint import pprint

from src.settings.enums import NaturalLanguage
from src.settings.config import ConfigBasic

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
pd.options.display.float_format = '{:.2f}'.format


class TextPreparer:
    SPACY_TOKEN_EXTS: dict = {'index': 'i', 'text': 'text', 'lemma': 'lemma_', 'tag': 'tag_', 'pos_tag': 'pos_', 'is_stop': 'is_stop', 'is_punct': 'is_punct', 'is_alpha': 'is_alpha', 'is_digit': 'is_digit'}

    # CONTENT_WORD_POS_TAG: list[str] = ['NOUN', 'VERB', 'ADJ', 'ADV']
    # CONTENT_WORD_POS_TAG: list[str] = ['NOUN', 'ADJ', 'ADV']
    CONTENT_WORD_POS_TAG: list[str] = ['NOUN', 'VERB']
    # CONTENT_WORD_POS_TAG: list[str] = ['NOUN']
    NOUN_TAGS: dict = {'plural': ['NNS', 'NNPS'], 'singular': ['NN', 'NNP']}

    def __init__(self, df: pd.DataFrame, nlp_en: Language, nlp_de: Language, use_comp_mask: bool = True, save_vocabulary: bool = False):
        condition = all(col for col in ['index', 'art_language', 'top_sent', 'top_sent_masked'] if col not in df.columns)
        if not condition:
            raise TypeError('language_text_list must be: list[tuple[NaturalLanguage,str]]')
        self.df: pd.DataFrame = df
        self.vocabulary: dict | None = None
        self.save_vocab: bool = save_vocabulary
        self.vocabulary_path: Path = Path(ConfigBasic.path_to_traditional_topic_models, 'vocabulary.json')
        self.vocabulary_path_new: Path = Path(ConfigBasic.path_to_traditional_topic_models_new, 'vocabulary.json')
        spacy.require_gpu()
        print('GPU is used:', spacy.prefer_gpu())  # ToDo: Logging here
        self.nlp_en = nlp_en
        self.nlp_de = nlp_de
        self.use_comp_mask = use_comp_mask
        self._set_custom_tokenizer()

    def _set_custom_tokenizer(self):
        # ToDo: Create patterns
        prefix_re = re.compile(r"")
        infix_re = re.compile(r"[-;,]")
        suffix_re = re.compile(r"[.]")
        self.nlp_en.tokenizer = Tokenizer(vocab=self.nlp_en.vocab,infix_finditer=infix_re.finditer, suffix_search=suffix_re.search)     #  prefix_search=prefix_re.search,
        self.nlp_de.tokenizer = Tokenizer(vocab=self.nlp_de.vocab, infix_finditer=infix_re.finditer, suffix_search=suffix_re.search)    # prefix_search=prefix_re.search
        self.custom_tokenizer_is_set = True

    def add_custom_stopwords(self, stop_words_en: list = None, stop_words_de: list = None):
        if stop_words_en is not None:
            stop_words_en = self.clean_custom_stopwords(stop_words=stop_words_en, nlp=self.nlp_en)
            self.nlp_en.Defaults.stop_words |= stop_words_en
            print('Stopwords added to nlp_en.')
        if stop_words_de is not None:
            stop_words_de = self.clean_custom_stopwords(stop_words=stop_words_de, nlp=self.nlp_de)
            self.nlp_de.Defaults.stop_words |= stop_words_de
            print('Stopwords added to nlp_de.')

    def clean_custom_stopwords(self, stop_words: list, nlp: Language, lemmatize: bool = True, lower: bool = True, words_only: bool = True):
        if lemmatize:
            stop_words = set([t.lemma_ for t in nlp(' '.join(stop_words))])
        if words_only:
            stop_words = set([t.text for t in nlp(' '.join(stop_words)) if t.is_alpha])
        if lower:
            stop_words = set([word.lower() for word in stop_words])
        return stop_words

    def save_vocabulary(self):
        with open(self.vocabulary_path, 'w') as f:
            json.dump(self.vocabulary, f)

    def load_vocabulary(self):
        if self.vocabulary_path.is_file():
            with open(self.vocabulary_path, 'r') as f:
                self.vocabulary = json.load(f)
        else:
            raise FileNotFoundError('vocabulary file not found')

    def split_text_to_word_list(self, text: str, natural_language: NaturalLanguage) -> list[str]:
        match natural_language:
            case NaturalLanguage.DE:
                nlp = self.nlp_de
            case NaturalLanguage.EN:
                nlp = self.nlp_en
        return [tok.text for tok in nlp(text) if tok.text not in string.punctuation]

    def make_word_info_list(self, natural_language: NaturalLanguage, text: str) -> list[tuple]:
        word_info_list: list[tuple] = list()
        if text is not None:
            match natural_language:
                case NaturalLanguage.DE:
                    nlp = self.nlp_de
                case NaturalLanguage.EN:
                    nlp = self.nlp_en
                case _:
                    raise ValueError(f'natural_language "{natural_language}" is unknown!')
            doc = nlp(text)
            for token in doc:
                token_info_spacy: tuple = tuple(getattr(token, attr) for attr in TextPreparer.SPACY_TOKEN_EXTS.values())
                token_info_word_position: tuple = tuple((token.idx, token.idx + len(token.text)))
                token_info = token_info_spacy + token_info_word_position
                word_info_list.append(token_info)
        return word_info_list

    def filter_text(self, word_info_list: list[tuple], rem_stopwords: bool = True, rem_punctuation: bool = True, rem_non_words: bool = True, rem_non_content_words: bool = True, lemmatize: bool = True, lower_case: bool = False, ):
        spacy_exts: dict = {str(key): int(id) for id, key in enumerate(TextPreparer.SPACY_TOKEN_EXTS.keys())}
        remove_index: set[int] = set()
        replacements: dict = dict()
        for tup in word_info_list:
            ind = tup[spacy_exts['index']]
            # Note: REMOVE index first
            if rem_stopwords:
                if tup[spacy_exts['is_stop']] is True: remove_index.add(ind)
            if rem_punctuation:
                if tup[spacy_exts['is_punct']] is True: remove_index.add(ind)
            if rem_non_words:
                if tup[spacy_exts['is_alpha']] is False: remove_index.add(ind)
            if rem_non_content_words:
                if tup[spacy_exts['pos_tag']] not in self.CONTENT_WORD_POS_TAG: remove_index.add(ind)

            # Note: REPLACE index second
            if ind not in remove_index:
                if lemmatize:
                    lemma = tup[spacy_exts['lemma']]
                    text = tup[spacy_exts['text']]
                    is_punct = tup[spacy_exts['is_punct']]
                    if lemma != text and not is_punct:
                        replacements.update({tup[spacy_exts['index']]: tup[spacy_exts['lemma']]})
        word_info_dict: dict = {tp[spacy_exts['index']]: tp[spacy_exts['text']] for tp in word_info_list if int(tp[spacy_exts['index']]) not in remove_index}
        word_info_dict.update(replacements)
        filtered_word_info_list = list(word_info_dict.values()) if len(word_info_dict) > 0 else pd.NA
        if lower_case and len(word_info_dict) > 0:
            filtered_word_info_list = [word.lower() for word in filtered_word_info_list]
        return filtered_word_info_list

    def get_list_of_sents(self, sentence_words_list: list[str]):
        return [' '.join(s for s in sentence_words_list if s)]

    def make_vocabulary(self) -> dict:
        unique_words: set = set([s for l in [li for li in self.df.top_prep_sent_words.tolist() if li is not pd.NA] for s in l])
        return {word: index for index, word in enumerate(sorted(unique_words))}

    def prepare(self, rem_stopwords: bool = True, rem_punctuation: bool = True, rem_non_words: bool = True, rem_non_content_words: bool = True, lemmatize: bool = True, lower_case: bool = True) -> tuple[pd.DataFrame, dict]:
        text_column: str = 'top_sent_masked' if self.use_comp_mask else 'top_sent'
        top_word_info_list: pd.Series = self.df.apply(lambda x: self.make_word_info_list(natural_language=x.art_language, text=x[text_column]) if x[text_column] is not pd.NA else pd.NA, axis=1)
        self.df['top_prep_sent_words'] = top_word_info_list.apply(lambda x: self.filter_text(x, rem_stopwords=rem_stopwords, rem_punctuation=rem_punctuation, rem_non_words=rem_non_words, rem_non_content_words=rem_non_content_words, lemmatize=lemmatize, lower_case=lower_case) if x is not pd.NA else pd.NA)
        self.df['top_prep_sent'] = self.df.apply(lambda x: self.get_list_of_sents(x.top_prep_sent_words) if x.top_prep_sent_words is not pd.NA else pd.NA, axis=1)
        if self.vocabulary is None:
            self.vocabulary = self.make_vocabulary()
        if self.save_vocab:
            self.save_vocabulary()
        return self.df, self.vocabulary


if __name__ == '__main__':
    # Data
    # df_all = pd.read_parquet(path='../../src/data/comp_sentences.parquet')
    # n_samples = 10
    # indexes = random.choices(population=range(len(df_all.index)), k=n_samples)
    # df_reduced = df_all.iloc[indexes]
    # text_list = df_reduced.comp_sents.tolist()
    import torch
    torch.cuda.empty_cache()
    # text_list = [("EN", "I had a great time in Berlin"), ("EN", "I had a magnificent time in Paris"), ("EN", "I had a wonderful time in London"), ("EN", "I ate an apple and a banana for lunch"), ("EN", "I ate a banana and an orange for diner"), ("EN", "I ate an apricot and an orange for breakfast")]
    #
    # # Prepare
    # nat_lang = NaturalLanguage.EN
    import pandas as pd

    df = pd.read_parquet('df_new.parquet')
    print(df.columns)
    sp = TextPreparer(df=df)
    sp.prepare()
    print(sp.df_prepare.head(5))
    print(sp.vocabulary)
    # sp.prepare(rem_stopwords=True, rem_punctuation=True, rem_non_words=True, rem_non_content_words=True, lemmatize=True, lower_case=True)
    # print('sp.prepared_list_of_text_lists:', sp.prepared_list_of_text_lists)
    # print('sp.prepared_text_list:', sp.prepared_text_list)
    # print('sp.lang_text_list:', sp.lang_text_list)
    # print('sp.text_list:', sp.text_list)
