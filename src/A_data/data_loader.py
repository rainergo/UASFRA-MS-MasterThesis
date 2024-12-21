import pathlib
import pandas as pd

from src.settings.config import ConfigBasic
from src.settings.enums import Frequency


class DataLoader:

    def __init__(self):
        self.base_path = ConfigBasic.path_to_data_news_articles

    def load_monthly_df(self, year: int, month: int) -> pd.DataFrame:
        path: pathlib.Path = self.base_path / str(year) / str(month) / f"{Frequency.MONTHLY}_{year}-{month:02d}"
        return pd.read_parquet(path=path)

    def load_df(self, path: pathlib.Path | str, dtype: dict = None, columns: list = None) -> pd.DataFrame:
        if isinstance(path, str):
            path = pathlib.Path(path)
        if path.name.endswith(".parquet"):
            return pd.read_parquet(path=path, columns=columns)
        elif path.name.endswith(".csv"):
            return pd.read_csv(filepath_or_buffer=path, dtype=dtype, usecols=columns)
        elif path.name.endswith(".xlsx"):
            return pd.read_excel(io=path, engine="openpyxl", dtype=dtype, usecols=columns)
        else:
            raise ValueError("File type not supported")

    def save_df(self, df: pd.DataFrame, path: pathlib.Path):
        if isinstance(path, str):
            path = pathlib.Path(path)
        df.to_parquet(path=path)


if __name__ == '__main__':
    from pathlib import Path
    dl = DataLoader()
    df = dl.load_df(Path('/src/A_DATA/Comp_Symbol_ISIN.xlsx'))
    print(df.columns)