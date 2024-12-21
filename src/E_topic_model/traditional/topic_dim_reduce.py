import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from sklearn.preprocessing import MinMaxScaler, QuantileTransformer
from sklearn.manifold import TSNE
from sklearn.decomposition import PCA, KernelPCA, NMF, LatentDirichletAllocation, TruncatedSVD
from umap import UMAP

from src.settings.config import ConfigBasic
from src.settings.enums import ReductionMethod
from src.E_topic_model.traditional.topic_vectorize import VectorizerType


class DimReducer:
    def __init__(self, df: pd.DataFrame, training_data: np.ndarray, vectorizer_type: VectorizerType, df_vector_name: str, df_red_vector_name: str,
            reduction_method: ReductionMethod, reduced_dim: int = 3, model_name: str = 'reduction_model.pkl', scaler_name: str = 'reduction_model_scaler.pkl',):
        self.df: pd.DataFrame = df
        self.training_data: np.ndarray = training_data
        self.text_vectorizer_type: VectorizerType = vectorizer_type
        self.reduction_method: ReductionMethod = reduction_method
        self.df_vector_name: str = df_vector_name
        self.df_red_vector_name: str = df_red_vector_name
        self.reduced_dim: int = reduced_dim
        self.scaler = None
        self.scaled_training_data = None
        self.reduction_model = None
        self.all_red_vectors: np.ndarray | None = None
        self.reduction_model_path: Path = Path(ConfigBasic.path_to_traditional_topic_models, self.reduction_method.name + '_' + model_name)
        self.reduction_model_scaler_path: Path = Path(ConfigBasic.path_to_traditional_topic_models, self.reduction_method.name + '_' + scaler_name)
        self.reduction_model_path_new: Path = Path(ConfigBasic.path_to_traditional_topic_models_new, self.reduction_method.name + '_' + model_name)
        self.reduction_model_scaler_path_new: Path = Path(ConfigBasic.path_to_traditional_topic_models_new, self.reduction_method.name + '_' + scaler_name)

    def config_model(self):
        n_samples = len(self.training_data)
        match self.reduction_method:
            case ReductionMethod.PCA:
                self.reduction_model = PCA(n_components=self.reduced_dim, svd_solver='auto')
            case ReductionMethod.KernelPCA:
                self.reduction_model = KernelPCA(n_components=self.reduced_dim, kernel='cosine')
            case ReductionMethod.SVD:
                self.reduction_model = TruncatedSVD(n_components=self.reduced_dim)
            case ReductionMethod.TSNE:
                if self.reduced_dim > 3:
                    raise TypeError('It is not recommended to use tsne for dimensionality reduction other than visualization due to computational complexity.')
                perplexity: float = min(max(5, int(n_samples / self.reduced_dim)), 50)
                self.reduction_model = TSNE(n_components=self.reduced_dim, perplexity=perplexity, init='random')
            case ReductionMethod.UMAP:
                n_neighbors: int = min(max(2, int(n_samples / self.reduced_dim)), 100)
                # n_neighbors_knn: int = max(n_neighbors, n_samples)
                # precomputed_knn = nearest_neighbors(self.training_data, n_neighbors=n_neighbors_knn, metric="euclidean", metric_kwds=None, angular=False, random_state=1)
                # self.reduction_model = UMAP(n_neighbors=n_neighbors, n_components=self.reduced_dim, metric='cosine', precomputed_knn=precomputed_knn)
                self.reduction_model = UMAP(n_neighbors=n_neighbors, n_components=self.reduced_dim, metric='cosine')
            case ReductionMethod.NMF:
                self.reduction_model = NMF(n_components=self.reduced_dim, init='random', random_state=0)
            case ReductionMethod.LDA:
                self.reduction_model = LatentDirichletAllocation(n_components=self.reduced_dim, random_state=0)

    def fit(self, save_model: bool = True):
        self.config_model()
        match self.reduction_method:
            case ReductionMethod.TSNE:
                self.reduction_model.fit_transform(self.training_data)
            case ReductionMethod.PCA | ReductionMethod.KernelPCA:
                self.scaler = QuantileTransformer()
                scaled_training_data = self.scaler.fit_transform(self.training_data)
                self.reduction_model = self.reduction_model.fit(scaled_training_data)
            case ReductionMethod.LDA | ReductionMethod.NMF:
                self.scaler = MinMaxScaler()
                scaled_training_data = self.scaler.fit_transform(self.training_data)
                self.reduction_model = self.reduction_model.fit(scaled_training_data)
            case ReductionMethod.UMAP:
                self.scaler = QuantileTransformer()
                scaled_training_data = self.scaler.fit_transform(self.training_data)
                self.reduction_model = self.reduction_model.fit(scaled_training_data)
            case _:
                self.reduction_model.fit(self.training_data)
        if save_model:
            self.save_model()

    def save_model(self):
        joblib.dump(self.reduction_model, filename=self.reduction_model_path_new)
        match self.reduction_method:
            case ReductionMethod.PCA | ReductionMethod.KernelPCA:
                joblib.dump(self.scaler, filename=self.reduction_model_scaler_path_new)

    def load_model(self):
        self.reduction_model = joblib.load(filename=self.reduction_model_path)
        match self.reduction_method:
            case ReductionMethod.PCA | ReductionMethod.KernelPCA:
                self.scaler = joblib.load(filename=self.reduction_model_scaler_path)

    @staticmethod
    def continue_question(reduction_method: ReductionMethod):
        msg = f'The "{reduction_method}" reduction method takes a very long time to run, potentially many hours. Are you sure you want to use "{reduction_method}"? (yes/no): '
        user_input = input(msg).lower()
        run_program = False
        while True:
            if user_input in ["yes", "y"]:
                print("Continuing...")
                run_program = True
                break
            elif user_input in ["no", "n"]:
                print("Exiting...")
                break
            else:
                print("Invalid input. Please enter yes/no.")
        if not run_program:
            raise TimeoutError('Program interrupted as desired!')

    def reduce(self) -> tuple[pd.DataFrame, np.ndarray]:
        # if self.reduction_method == ReductionMethod.UMAP:
        #     DimReducer.continue_question(self.reduction_method)
        col_name_scaled_vector = 'scaled_' + self.df_vector_name
        match self.reduction_method:
            case ReductionMethod.PCA | ReductionMethod.KernelPCA:
                self.df[col_name_scaled_vector] = self.df.apply(lambda x: self.scaler.transform(x[self.df_vector_name]) if x[self.df_vector_name] is not pd.NA else pd.NA, axis=1)
                self.df[self.df_red_vector_name] = self.df.apply(lambda x: self.reduction_model.transform(x[col_name_scaled_vector]) if x[col_name_scaled_vector] is not pd.NA else pd.NA, axis=1)
            case ReductionMethod.TSNE:
                data = np.vstack([[0.0 for _ in range(self.training_data.shape[1])] if x is pd.NA else x for x in self.df[self.df_vector_name]])
                self.df[self.df_red_vector_name] = self.reduction_model.fit_transform(data).tolist()
            case _:
                self.df[self.df_red_vector_name] = self.df.apply(lambda x: self.reduction_model.transform(x[self.df_vector_name]) if x[self.df_vector_name] is not pd.NA else pd.NA, axis=1)

        self.all_red_vectors: np.ndarray = np.vstack(self.df[self.df_red_vector_name][~self.df[self.df_red_vector_name].isna()].values)

        print('DimReducer.reduce() was run!')
        return self.df, self.all_red_vectors


if __name__ == '__main__':
    text_vectors = np.fromfile('text_vectors.txt', sep=', ').reshape((6, 16))
    dimred = DimReducer(text_vectors, ReductionMethod.LDA)
    dimred.reduce()
    print(dimred.text_vectors)
    print(dimred.reduction_model)
