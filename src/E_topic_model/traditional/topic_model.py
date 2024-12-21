import pandas as pd
import numpy as np
from copy import deepcopy

from src.settings.config import ConfigTopic
from src.E_topic_model.traditional.topic_vectorize import Vectorizer

from src.settings.enums import VectorizerType


class TopicModel:
    def __init__(self, df: pd.DataFrame, vocabulary: dict, cluster_vectorizer_type: VectorizerType = VectorizerType.TFIDF, most_common_n_words: int = 10):
        if not isinstance(df, pd.DataFrame):
            raise TypeError('df must be a pandas DataFrame.')
        self.vocabulary: dict = vocabulary
        self.df_data: pd.DataFrame = deepcopy(df[['top_sent', 'top_prep_sent', 'top_prep_sent_words', 'cluster_label', 'top_red_viz_vector']])
        self.df_cluster: pd.DataFrame | None = None
        self.df_cluster_doc_term_matrix: pd.DataFrame | None = None
        self.cluster_vectorizer_type = cluster_vectorizer_type
        self.most_common_n_words = most_common_n_words

    def create_topics(self):
        self.df_data = self.df_data.dropna(subset=['top_sent', 'top_prep_sent', 'top_prep_sent_words', 'cluster_label', 'top_red_viz_vector'])
        self.df_data[["x", "y", "z"]] = self.df_data.apply(lambda x: np.squeeze(x.top_red_viz_vector).tolist(), axis=1, result_type='expand')
        self.df_cluster = self.df_data.groupby('cluster_label').agg({'x': 'mean', 'y': 'mean', 'z': 'mean', 'top_sent': ' '.join, 'top_prep_sent': lambda x: [' '.join(x.apply(' '.join))], 'top_prep_sent_words': lambda val: [x for xs in val for x in xs]}).reset_index()
        ######### CHECK ###########
        col1 = 'top_sent'
        col2 = 'top_prep_sent_words'
        col3 = 'top_prep_sent'
        condition1 = type(self.df_data[col1].iloc[0]) == type(self.df_cluster[col1].iloc[0]) and type(self.df_data[col1].iloc[0][0]) == type(self.df_cluster[col1].iloc[0][0])
        condition2 = type(self.df_data[col2].iloc[0]) == type(self.df_cluster[col2].iloc[0]) and type(self.df_data[col2].iloc[0][0]) == type(self.df_cluster[col2].iloc[0][0])
        condition3 = type(self.df_data[col3].iloc[0]) == type(self.df_cluster[col3].iloc[0]) and type(self.df_data[col3].iloc[0][0]) == type(self.df_cluster[col3].iloc[0][0]) and len(self.df_data[col3].iloc[0]) == len(self.df_cluster[col3].iloc[0])
        if not (condition1 and condition2 and condition3):
            raise TypeError('Mismatch in type and len for columns in df and df_cluster. This leads to incorrect df_cluster vectors. Check column types and len!')
        cluster_vectorizer = Vectorizer(df=self.df_cluster, vocabulary=self.vocabulary, vectorizer_type=self.cluster_vectorizer_type, df_vector_name=ConfigTopic.cluster_vector_col_name)
        self.df_cluster, all_cluster_vectors = cluster_vectorizer.vectorize()
        print('Dimension of all_cluster_vectors:', all_cluster_vectors.shape)
        # cluster_text_vocabulary = dict(sorted(cluster_vectorizer.vectorizer.vocabulary_.items(), key=lambda item: item[1]))
        self.df_cluster_doc_term_matrix = pd.DataFrame(data=all_cluster_vectors, columns=self.vocabulary)
        n_most_frequent_words = self.most_common_n_words
        self.df_cluster['most_frequent_words'] = self.df_cluster_doc_term_matrix.apply(lambda x: list(zip(x.nlargest(n_most_frequent_words).index.values, x.nlargest(n_most_frequent_words).values)), axis=1)


if __name__ == '__main__':
    text_list = [("EN", "I had a great time in Berlin"), ("EN", "I had a magnificent time in Paris"), ("EN", "I had a wonderful time in London"), ("EN", "I ate an apple and a banana for lunch"), ("EN", "I ate a banana and an orange for diner"), ("EN", "I ate an apricot and an orange for breakfast")]
    top = TopicModel(language_text_list=text_list)
    top.run()
    # print(top.vectorizer.text_vectors)
    # print(top.vectorizer.text_vectors.shape)
    # print(type(top.vectorizer.text_vectors))
    # print(top.vectorizer.text_vocabulary)
    # print(top.dim_reducer.text_vectors.shape)
    # print(top.dim_reducer.text_vectors)
    # print(top.clusterer.cluster_labels)
    # print(top.clusterer.cluster_centroids)
    # df1, df2, df3 = top.make_dfs()
    # print(df1)
    # print(df2)