from pathlib import Path
import numpy as np
import pandas as pd
import joblib
from sklearn.preprocessing import MinMaxScaler, QuantileTransformer
from sklearn.cluster import KMeans, MeanShift, estimate_bandwidth, HDBSCAN
import hdbscan

from src.settings.enums import VectorizerType, ClusterMethod
from src.settings.config import ConfigBasic


class Clusterer:

    def __init__(self, df: pd.DataFrame, dim_reduced_training_data: np.ndarray, cluster_method: ClusterMethod, model_name: str = 'cluster_model.pkl',
            n_clusters: int = 15):
        self.df: pd.DataFrame = df
        self.dim_reduced_training_data: np.ndarray = dim_reduced_training_data
        self.cluster_method: ClusterMethod = cluster_method
        self.n_clusters: int = n_clusters
        self.cluster_labels: np.ndarray | None = None
        self.cluster_centroids: np.ndarray | None = None
        self.cluster_model = None
        self.scaler = None
        self.model_path: Path = Path(ConfigBasic.path_to_traditional_topic_models, self.cluster_method.name + '_' + model_name)
        self.model_path_new: Path = Path(ConfigBasic.path_to_traditional_topic_models_new, self.cluster_method.name + '_' + model_name)

    def save_model(self):
        joblib.dump(self.cluster_model, filename=self.model_path_new)

    def load_model(self):
        self.cluster_model = joblib.load(filename=self.model_path)

    def config_model(self):
        match self.cluster_method:
            case ClusterMethod.KMEANS:
                self.cluster_model: KMeans = KMeans(n_clusters=self.n_clusters, init="k-means++", max_iter=1000, n_init=100)
            case ClusterMethod.MEAN_SHIFT:
                bandwidth = max(0.001, estimate_bandwidth(self.dim_reduced_training_data, quantile=0.2, n_samples=self.dim_reduced_training_data.shape[0]))
                self.cluster_model: MeanShift = MeanShift(bandwidth=bandwidth, bin_seeding=True)
            case ClusterMethod.HDBSCAN:
                # self.cluster_model = HDBSCAN(min_cluster_size=5, min_samples=None, cluster_selection_epsilon=0.7, max_cluster_size=None, metric='euclidean', metric_params=None, alpha=1.0, algorithm='auto', leaf_size=40, n_jobs=None, cluster_selection_method='eom', allow_single_cluster=False, store_centers=None, copy=False)
                self.scaler = QuantileTransformer()      # necessary due to some extreme outliers
                self.dim_reduced_training_data = self.scaler.fit_transform(self.dim_reduced_training_data)
                self.cluster_model: hdbscan.HDBSCAN = hdbscan.HDBSCAN(min_cluster_size=5, min_samples=5, alpha=1.3, cluster_selection_epsilon=0.7, prediction_data=True)

    def fit(self, save_model: bool = True):
        self.config_model()
        self.cluster_model = self.cluster_model.fit(self.dim_reduced_training_data)
        self.cluster_labels = self.cluster_model.labels_
        match self.cluster_method:
            case ClusterMethod.HDBSCAN:
                self.cluster_centroids = None
            case _:
                self.cluster_centroids = self.cluster_model.cluster_centers_
        if save_model:
            self.save_model()

    def predict(self):
        match self.cluster_method:
            case ClusterMethod.HDBSCAN:
                col_name_scaled_vector = 'scaled_top_red_vector'
                self.df[col_name_scaled_vector] = self.df.apply(lambda x: self.scaler.transform(x.top_red_vector) if x.top_red_vector is not pd.NA else pd.NA, axis=1)
                self.df['cluster_label'] = self.df.apply(lambda x: hdbscan.approximate_predict(self.cluster_model, x[col_name_scaled_vector])[0][0] if x[col_name_scaled_vector] is not pd.NA else pd.NA, axis=1)
            case _:
                self.df['cluster_label'] = self.df.apply(lambda x: self.cluster_model.predict(x.top_red_vector)[0] if x.top_red_vector is not pd.NA else pd.NA, axis=1)

        print('Clusterer.cluster() was run!')


if __name__ == '__main__':
    with open("text_list.txt", "r") as outfile:
        text_list = outfile.readlines()

    print(text_list)
    import json
    with open('text_vocab.json', 'r') as infile:
        text_vocab = json.load(infile)
    print(text_vocab)
    text_vectors = np.fromfile('text_vectors.txt', sep=', ').reshape((6, 16))
    print(text_vectors)
    tc = Clusterer(text_vectors=text_vectors, text_vocabulary=text_vocab, cluster_method=ClusterMethod.KMEANS, vectorizer_type=VectorizerType.BagOfWords, n_clusters=2)
    tc.predict(n_most_common_words=5)
    print(tc.cluster_labels)
    print(tc.cluster_centroids)
    # print(tc.cluster_centroids.shape)
    # print(tc.cluster_centroids_most_common_words)
