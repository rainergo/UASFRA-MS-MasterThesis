import concurrent.futures
import re
import pandas as pd
from typing import Generator
from collections.abc import Callable


def run_re_finditer_concurrently(pattern_list: list, text: str) -> Generator:
    """ The function here must have exactly one parameter. """
    with (concurrent.futures.ThreadPoolExecutor(max_workers=len(pattern_list))
          as executor):
        future_to_result = [executor.submit(re.finditer, pattern, text)
            for pattern in pattern_list]
        futures_done = concurrent.futures.as_completed(fs=future_to_result,
            timeout=None)
        for future in futures_done:
            try:
                data = list(future.result())
            except (Exception, TimeoutError):
                print(f'Fetching concurrent.future failed for future: {future}')
            else:
                if data is not None and len(data) > 0:
                    yield data


def concurrent_df_apply(df: pd.DataFrame, function: Callable, df_col_name_1: str, df_col_name_2: str, name_new_col: str) -> pd.DataFrame:
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(df.index)) as executor:
        futures = executor.map(function, df[df_col_name_1], df[df_col_name_2])
        print('type(futures):', type(futures))
        try:
            df[name_new_col] = list(futures)
        except (Exception, TimeoutError):
                print(f'Fetching concurrent.future failed.')
        return df


if __name__ == '__main__':
    l = [1, 2, 3]
    m = [ele**2 for ele in l]
    # print(m)
    df = pd.DataFrame({'l': l, 'm': m})
    import time
    import random

    def ret_square(multiplicator: int, num:int) -> int:
        secs = random.randint(2, 6)
        time.sleep(secs)
        return multiplicator * num

    df_new = concurrent_df_apply(df=df, function=ret_square, df_col_name_1='l', df_col_name_2='m', name_new_col='square')
    print(df_new)



