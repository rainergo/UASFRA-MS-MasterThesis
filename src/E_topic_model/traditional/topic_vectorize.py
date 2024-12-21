import numpy as np
import pandas as pd
from pathlib import Path
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.preprocessing import MultiLabelBinarizer

from src.settings.config import ConfigBasic
from src.settings.enums import NaturalLanguage, VectorizerType

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
pd.options.display.float_format = '{:.2f}'.format


class Vectorizer:

    def __init__(self, df: pd.DataFrame, vocabulary: dict, vectorizer_type: VectorizerType, df_vector_name: str):
        if not (isinstance(df, pd.DataFrame) and isinstance(vocabulary, dict)):
            raise TypeError('text_list must be a TextPreparer instance.')
        self.df: pd.DataFrame = df
        self.vocabulary: dict = vocabulary
        self.vocabulary_path: Path = Path('models/vocabulary.json')
        self.vectorizer_type: VectorizerType = vectorizer_type
        self.df_vector_name: str = df_vector_name
        self.all_vectors: np.ndarray | None = None
        match self.vectorizer_type:
            case VectorizerType.TFIDF:
                self.vectorizer = TfidfVectorizer()
            case VectorizerType.BagOfWords:
                self.vectorizer = CountVectorizer()
            case VectorizerType.EMBEDDING:
                self.vectorizer = SentenceTransformer(model_name_or_path=ConfigBasic.sentence_transformer_model, device="cuda")
            case VectorizerType.OneHot:
                self.vectorizer = MultiLabelBinarizer()
        self.set_params()
        self.fit()

    def set_params(self):
        match self.vectorizer_type:
            # Note: Leave preprocessing task to TextPreparer, do nothing restrictive here
            case VectorizerType.TFIDF | VectorizerType.BagOfWords:
                # Note: Vocabulary from TextPreparer:
                self.vectorizer.vocabulary = self.vocabulary
                self.vectorizer.ngram_range = (1, 1)
                self.vectorizer.max_df = 1.0  # Note: ignores words that appear above this pct in vocab
                self.vectorizer.min_df = 0.00  # Note: ignores words that appear below this pct in vocab
                self.vectorizer.tokenizer = None
                self.vectorizer.analyzer = 'word'
                self.vectorizer.stop_words = None
                self.vectorizer.max_features = None

    def fit(self):
        match self.vectorizer_type:
            case VectorizerType.EMBEDDING:
                pass
            case _:
                self.vectorizer.fit(self.vocabulary)

    def vectorize(self) -> tuple[pd.DataFrame, np.ndarray]:
        match self.vectorizer_type:
            case VectorizerType.OneHot:
                self.df[self.df_vector_name]: np.ndarray = self.df.apply(lambda x: self.vectorizer.transform(x.top_prep_sent_words) if x.top_prep_sent_words is not pd.NA else pd.NA, axis=1)
            case VectorizerType.TFIDF | VectorizerType.BagOfWords:
                self.df[self.df_vector_name]: np.ndarray = self.df.apply(lambda x: self.vectorizer.transform(x.top_prep_sent).toarray() if x.top_prep_sent is not pd.NA else pd.NA, axis=1)
            case VectorizerType.EMBEDDING:
                self.df[self.df_vector_name]: np.ndarray = self.df.apply(lambda x: np.array(self.vectorizer.encode(x.top_sent), ndmin=2) if x.top_sent is not pd.NA else pd.NA, axis=1)

        self.all_vectors: np.ndarray = np.vstack(self.df[self.df_vector_name][~self.df[self.df_vector_name].isna()].values)
        print('Vectorizer.vectorize() was run.')
        return self.df, self.all_vectors


if __name__ == '__main__':
    import json
    # df_data = pd.read_parquet(path='../data/text_samples.parquet')
    # text_list = df_data.pp_art_text.tolist()
    # nat_lang = NaturalLanguage.DE
    # text_vocab = {'great': 7, 'time': 13, 'berlin': 4, 'magnificent': 10, 'paris': 12, 'wonderful': 14, 'london': 8, 'ate': 2, 'apple': 0, 'banana': 3, 'lunch': 9, 'orange': 11, 'diner': 6, 'apricot': 1, 'breakfast': 5}
    text_list = ["I had a great time in Berlin", "I had a magnificent time in Paris", "I had a wonderful time in London", "I ate an apple and a banana for lunch", "I ate a banana and an orange for diner", "I ate an apricot and an orange for breakfast"]
    # with open("text_list.txt", "w") as outfile:
    #     outfile.write("\n".join(text_list))
    # text = "I had a great time in Berlin"
    nat_lang = NaturalLanguage.EN

    tv = Vectorizer(natural_language=nat_lang, prepared_text_list=text_list, vectorizer_type=VectorizerType.OneHot)
    tv.vectorize(rem_stopwords=False)
    vocab = tv.text_vocabulary
    # json.dump(vocab, open('text_vocab.json', 'w'))

    vecs = tv.text_vectors
    print(vecs)
    print(type(vecs))
    print(vecs.shape)
    print('text_vocab:', tv.text_vocabulary)
    # vecs.tofile('text_vectors.txt', sep=', ')
