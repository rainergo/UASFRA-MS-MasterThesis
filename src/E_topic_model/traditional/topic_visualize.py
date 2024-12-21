import pandas as pd
import plotly.graph_objects as go

from src.settings.enums import VectorizerType, ClusterMethod, ReductionMethod


class Visualizer:
    def __init__(self, df_data: pd.DataFrame, df_cluster: pd.DataFrame, vocabulary: dict, vectorizer_type: VectorizerType, dimension_reduction_method: ReductionMethod,reduced_vector_dimension: int, cluster_method: ClusterMethod, number_of_clusters: int):
        self.df_data: pd.DataFrame = df_data
        self.df_cluster: pd.DataFrame = df_cluster
        self.vocabulary: dict = vocabulary
        self.vectorizer_type = vectorizer_type
        self.dimension_reduction_method = dimension_reduction_method
        self.reduced_vector_dimension = reduced_vector_dimension
        self.cluster_method = cluster_method
        self.number_of_clusters = number_of_clusters

    def plot(self, hide_text: bool = True, point_size: int = 3, cluster_cross_size: int = 6, template: str = 'seaborn'):
        fig = go.Figure()
        centroid_text = [''.join(str([(w[0], f"{w[1]:.2f}") for w in l])) for l in self.df_cluster.most_frequent_words.tolist()]
        data = go.Scatter3d(x=self.df_data.x, y=self.df_data.y, z=self.df_data.z, text=self.df_data.top_prep_sent_words.tolist(), name='name', marker=dict(size=point_size,color=self.df_data.cluster_label))
        fig.add_trace(trace=data)
        centroids = go.Scatter3d(x=self.df_cluster.x, y=self.df_cluster.y, z=self.df_cluster.z, name='Centroids', text=centroid_text, marker=dict(size=cluster_cross_size, symbol='x', color=self.df_cluster.cluster_label), mode='markers')
        fig.add_trace(trace=centroids)
        if hide_text:
            fig.update_traces(mode='markers')
        title_text = f"Vectorizer: {self.vectorizer_type.name} --- Dimension Reducer: {self.dimension_reduction_method.name} --- No. of Dimensions: {self.reduced_vector_dimension} --- Clusterer: {self.cluster_method.name} --- No. of Clusters: {self.number_of_clusters}"
        fig.update_layout(title_text=title_text, coloraxis_showscale=False, template=template)
        fig.show(renderer='browser')  # fig.show()


if __name__ == '__main__':
    #
    tv = Visualizer()

    # text_list = ["I spent a great time in Berlin",
    #              "I spent a magnificent time in Berlin",
    #              "I spent a wonderful time in Berlin",
    #              "I ate an apple for lunch",
    #              "I ate an apple for diner",
    #              "I ate an apple for breakfast"]
    # nat_lang = NaturalLanguage.EN
    # n_clusters = 4


