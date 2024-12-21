from pathlib import Path

from src.settings.enums import VectorizerType, ReductionMethod, ClusterMethod

class ConfigBasic:
    # Paths
    abs_path_here = Path(__file__)
    path_to_secrets = Path(abs_path_here.parent.parent.parent, 'secrets.env')
    path_to_data = Path(abs_path_here.parent.parent, '/mnt/nas/SEC_ANA_DATA/')
    path_to_data_news_articles = Path(path_to_data, 'News_Articles/')
    path_to_companies_parquet_file = Path(abs_path_here.parent.parent, 'A_data/', 'companies.parquet')
    path_to_entity_ruler_patterns: Path = Path(abs_path_here.parent.parent, 'B_spacy_pipeline/patterns/backup/entity_ruler_patterns.jsonl')
    path_to_entity_token_matcher_patterns: Path = Path(abs_path_here.parent.parent, 'B_spacy_pipeline/patterns/backup/entity_token_matcher_patterns.jsonl')
    path_to_entity_regex_patterns: Path = Path(abs_path_here.parent.parent, 'B_spacy_pipeline/patterns/backup/entity_regex_patterns.jsonl')
    # path_to_wortschatz_leipzig_de: Path = Path(abs_path_here.parent.parent, 'B_spacy_pipeline/files/deu_news_2023_10K-words.txt')
    # path_to_wortschatz_leipzig_en: Path = Path(abs_path_here.parent.parent, 'B_spacy_pipeline/files/eng_news_2023_10K-words.txt')
    # SOURCE: https://github.com/oprogramador/most-common-words-by-language/tree/master/src/resources :
    path_to_most_common_words_en: Path = Path(abs_path_here.parent, 'files/most_common_words_en.txt')
    path_to_most_common_words_de: Path = Path(abs_path_here.parent, 'files/most_common_words_de.txt')
    # SOURCE: https://names.mongabay.com/most_common_surnames.htm :
    path_to_most_common_last_names_en: Path = Path(abs_path_here.parent, 'files/most_5000_common_last_names_en.csv')
    path_to_most_common_first_names_female_en: Path = Path(abs_path_here.parent, 'files/most_1000_common_first_names_female_en.csv')
    path_to_most_common_first_names_male_en: Path = Path(abs_path_here.parent, 'files/most_1000_common_first_names_male_en.csv')

    # SOURCE: https://forebears.io/germany/surnames :
    path_to_most_common_last_names_de: Path = Path(abs_path_here.parent, 'files/most_1000_common_last_names_de.csv')

    # Comp-Symbol converter data
    path_to_comp_symbol_isin_data: Path = Path(abs_path_here.parent.parent, 'F_knowledge_graph/data/Comp_Symbol_ISIN.xlsx')
    path_to_traditional_topic_models = Path(abs_path_here.parent.parent, 'E_topic_model/traditional/models/')
    path_to_traditional_topic_models_new = Path(abs_path_here.parent.parent, 'E_topic_model/traditional/models_new/')

    # Other
    df_cols_for_duplicate_check: list = ["art_url"]
    df_cols_for_logger: list = ["art_datetime", "art_url"]

    # spaCy:
    # Note: Check relevant_labels for potentially misclassified labels:
    spacy_relevant_labels: list = ['ORG', 'PER', 'MISC', 'PERSON', 'PRODUCT', 'ENT-RULER']
    spacy_threshold_fuzzy_search: float = 90.00
    spacy_init_mark: str = ''
    spacy_comp_label: str = 'ORG'
    spacy_comp_mention_label: str = 'ORG-PART'   # Note: See "entity_token_matcher_patterns.jsonl" and spacy_pipe_func "CompNameTokenRegexMatch"
    spacy_regex_token_search_required_pos_tags: list = ['NOUN', 'PROPN', 'NUM']

    # Topic Model
    sentence_transformer_model: str = 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2'


class ConfigTopic:
    vector_col_name: str = 'top_vector'
    reduced_vector_col_name: str = 'top_red_vector'
    viz_reduced_vector_col_name: str = 'top_red_viz_vector'
    cluster_vector_col_name: str = 'top_cluster_vector'
    most_common_n_words: int = 10


class ConfigGraph:
    path_base_knowledge_graph = Path(ConfigBasic.abs_path_here.parent.parent,"F_knowledge_graph/")
    path_to_onto = Path(path_base_knowledge_graph, "Ontologies/NewsArticles.ttl")


if __name__ == '__main__':
    print(ConfigGraph.path_to_onto)
    # import json
    # with open(conf.path_nordvpn_countries_and_cities) as file:
    #     data = json.load(file)
    # print(data)
