import pandas as pd
from pathlib import Path

from src.G_utils.regex_funcs import clean_accents_and_umlaute
from src.settings.enums import NaturalLanguage
from src.settings.config import ConfigBasic


def filter_and_clean_df(df: pd.DataFrame, col_name: str, min_len_words: int) -> pd.DataFrame:
    # Note: Conditions to clean df to get pure words
    df = df.dropna()
    condition_exclude_chars = df[col_name].str.contains(r"""(?:[^%,\.'"])""", regex=True)
    condition_alphabetic = df[col_name].str.isalpha()
    condition_len = df[col_name].str.len() >= min_len_words
    condition_ascii = df[col_name].apply(check_letters_are_ascii)
    condition_letters_are_different = df[col_name].apply(check_letters_are_different)

    # Note: Apply conditions
    conditions = condition_exclude_chars & condition_alphabetic & condition_ascii & condition_len & condition_letters_are_different
    df = df[conditions]

    # Note: Get rid of spaces, convert to lowercase and clean for accents and umlaute:
    df[col_name] = df[col_name].str.strip()
    df[col_name] = df[col_name].str.lower()
    df[col_name] = df[col_name].apply(clean_accents_and_umlaute)
    return df


def load_words(language: NaturalLanguage) -> pd.DataFrame:
    if language == NaturalLanguage.EN:
        path: Path = ConfigBasic.path_to_most_common_words_en
    elif language == NaturalLanguage.DE:
        path: Path = ConfigBasic.path_to_most_common_words_de
    else:
        raise ValueError(f"Language {language} is not supported")
    df = pd.read_csv(filepath_or_buffer=path, delimiter='\t', header=None, names=["word"], dtype={"word": 'string'})
    return df


def load_last_names(language: NaturalLanguage) -> pd.DataFrame:
    if language == NaturalLanguage.EN:
        path: Path = ConfigBasic.path_to_most_common_last_names_en
    elif language == NaturalLanguage.DE:
        path: Path = ConfigBasic.path_to_most_common_last_names_de
    else:
        raise ValueError(f"Language {language} is not supported")
    df = pd.read_csv(filepath_or_buffer=path, delimiter='~', header=0)
    return df


def load_first_names(language: NaturalLanguage) -> pd.DataFrame:
    if language == NaturalLanguage.EN:
        path_female: Path = ConfigBasic.path_to_most_common_first_names_female_en
        path_male: Path = ConfigBasic.path_to_most_common_first_names_male_en
        df_female = pd.read_csv(filepath_or_buffer=path_female, delimiter='~', header=0)
        df_male = pd.read_csv(filepath_or_buffer=path_male, delimiter='~', header=0)
        df = pd.concat([df_female, df_male])
    elif language == NaturalLanguage.DE:
        path: Path = ConfigBasic.path_to_most_common_last_names_de
        df = pd.read_csv(filepath_or_buffer=path, delimiter='~', names=["first_name"], dtype={"first_name": 'string'})
    else:
        raise ValueError(f"Language {language} is not supported")
    return df


def check_letters_are_different(text: str) -> bool:
    return not all([letter == text[0] for letter in [text_letter for text_letter in text]])


def check_letters_are_ascii(text: str) -> bool:
    return all([letter.isascii() for letter in text])


def get_most_common_words(language: NaturalLanguage, exclude_words: list[str] = None, min_len_words: int = 3) -> list[
    str]:
    if exclude_words is None:
        exclude_words = []
    df: pd.DataFrame = load_words(language=language)

    df = filter_and_clean_df(df=df, col_name="word", min_len_words=min_len_words)

    most_common_words = sorted(list(set(df.word.tolist())))
    most_common_words = [word for word in most_common_words if word not in exclude_words]
    return most_common_words


def get_most_common_names(language: NaturalLanguage, col_name: str = 'names', min_len_words: int = 3) -> list[str]:
    df_first_names: pd.DataFrame = load_first_names(language=language)
    df_last_names: pd.DataFrame = load_last_names(language=language)
    names_list = df_first_names.first_name.values.tolist() + df_last_names.last_name.values.tolist()
    df_names: pd.DataFrame = pd.DataFrame(data={'names': names_list})
    df_names_clean = filter_and_clean_df(df_names, col_name=col_name, min_len_words=min_len_words)
    names: list = sorted(list(set(df_names_clean[col_name].tolist())))
    return names



if __name__ == '__main__':
    print(len(get_most_common_names(NaturalLanguage.EN)))
    # abc = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
    # res = get_most_common_words(language=NaturalLanguage.DE)
    # print('bayer' in res)
    # print(len(res))
    # print(res)
    # for w in res:
    #     wl = [l for l in w]
    #     # print(wl)
    #     for l in wl:
    #         if l not in abc:
    #             print(w)
