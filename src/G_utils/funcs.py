import re
import traceback
from pathlib import Path
import dataframe_image as dfi
import numpy as np
import pandas as pd

from rapidfuzz import fuzz, process


def df_to_img(df: pd.DataFrame, img_name: str,
              base_path: Path = Path('/doc/Assets'),
              decimals: int = 2,
              use_custom_style: bool = True):
    path_and_name: Path = base_path / img_name

    if use_custom_style:
        css_alt_rows = 'background-color: lightgray; color: black;'
        css_indexes = 'background-color: steelblue; color: white;'
        df = (df.style.apply(lambda col: np.where(col.index % 2, css_alt_rows, None))  # alternating rows
              .map_index(lambda _: css_indexes, axis=0)  # row indexes (pandas 1.4.0+)
              .map_index(lambda _: css_indexes, axis=1)
              .format(precision=decimals))  # col indexes (pandas 1.4.0+)
    dfi.export(
        obj=df,
        filename=path_and_name,
        fontsize=12,
        max_rows=None,
        max_cols=None,
        table_conversion="matplotlib",
        chrome_path=None,
        dpi=100,  # enlarge your image，default is 100，set it larger will get a larger image
        use_mathjax=True,  # enable mathjax support， which means you can use latex in your dataframe
    )


def exc_info_formatter(msg: str = None, new_line_repl: str = " ") -> str:
    """ Must be used in "except" ("try/except") if exc_info shall be showed: Packs exc_info string into ONE line. """
    msg: str = "" if msg is None else msg + ": "
    traceback_str = traceback.format_exc()
    matchobjects = list(re.finditer(pattern=r"\n+|\s{2,}", string=traceback_str, flags=re.MULTILINE))
    for match in matchobjects:
        traceback_str = traceback_str.replace(match.group(0), new_line_repl)
    return msg + traceback_str


def fuzzy_search_one(text: str, choices: list, use_partial: bool = False, case_sensitive: bool = False) -> tuple[
    str, float, int]:
    """
    Scorer: fuzz.ratio: Calculates the normalized Indel similarity.
    :param choices: List of company names to search for
    :param text: Candidate for company name
    :param use_partial: Be careful! Would 100% match 'Fresenius Medical Care' and 'Fresenius'
    :param case_sensitive: Converts all characters to lower case -> Be careful: Case sensitive matching only if False !!!
    :return: tuple(match as string, similarity as float (between 0.0 and 100.0), index of match in choices)
    """
    scorer = fuzz.partial_ratio if use_partial else fuzz.ratio
    processor = None if case_sensitive else lambda x: x.lower()
    return process.extractOne(query=text, choices=choices, scorer=scorer, processor=processor)


def fuzzy_similarity(text: str, choices: list) -> float:
    """
    Scorer: fuzz.ratio: Calculates the normalized Indel similarity.
    :param choices: List of strings to search for
    :param text: Candidate for string match
    :return: float between 0.0 and 100.0
    """
    processor = lambda x: x.lower()
    match, similarity, index = process.extractOne(query=text, choices=choices, scorer=fuzz.ratio, processor=processor)
    # print('match, similarity, index:', match, '---' ,similarity,'--',  index)
    return similarity


def fuzzy_ratio(text1: str, text2, use_partial: bool = False, case_sensitive: bool = False) -> float:
    processor = None if case_sensitive else lambda x: x.lower()
    if use_partial:
        ratio = fuzz.partial_ratio(text1, text2, processor=processor)
    else:
        ratio = fuzz.ratio(text1, text2, processor=processor)
    return ratio


if __name__ == '__main__':
    pass
