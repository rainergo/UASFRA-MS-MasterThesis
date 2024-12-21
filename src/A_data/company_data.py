import warnings

import pandas as pd

from src.settings.config import ConfigBasic
from src.G_utils.regex_funcs import clean_accents_and_umlaute
from src.G_utils.regex_funcs import split_company_name_to_name_and_legal, split_name

pd.set_option('display.max_columns', 50)
warnings.filterwarnings("ignore")

df_companies = pd.read_parquet(ConfigBasic.path_to_companies_parquet_file, columns=['symbol', 'name'])
# Note: Clean company names for accents and umlaute:
df_companies['name'] = df_companies['name'].apply(clean_accents_and_umlaute)
# Note: Split up:
df_companies['name_and_legal'] = df_companies['name'].apply(split_company_name_to_name_and_legal)
df_companies['name_without_legal'] = df_companies['name_and_legal'].apply(lambda x: x[0])
df_companies['name_split_and_legal'] = df_companies['name_and_legal'].apply(lambda x: (split_name(x[0]),x[1]))
df_companies.sort_values(by=['name'], ascending=True, inplace=True)


comp_name_symbol_list: list[tuple[str, str]] = sorted(list(zip(df_companies.name.values.tolist(), df_companies.symbol.values.tolist())), key=lambda x: x[0])
symbol_comp_name_dict: dict = {x[1]: x[0] for x in comp_name_symbol_list}
comp_name_list: list[str] = sorted(df_companies.name.values.tolist())
# comp_name_list_split: list[list[str]] = [split_name(split_company_name_to_name_and_legal(comp)[0]) + ([split_company_name_to_name_and_legal(comp)[1]] if split_company_name_to_name_and_legal(comp)[1] is not None else []) for comp in comp_name_list]
comp_name_list_without_legal: list[str] = df_companies.name_without_legal.values.tolist()
# company_names_dict: dict = {k[0]:{'symbol': k[1], 'name_split': split, 'name_split_without_legal': list(split_company_name_to_name_and_legal(wo_legal))} for k,split, wo_legal in zip(comp_name_symbol_list, comp_name_list_split, comp_name_list_without_legal)}
company_names_dict = dict(zip(comp_name_list, df_companies.symbol.values.tolist()))

if __name__ == '__main__':
    # print(df_companies.head(n=20).to_string())
    for item in df_companies['name_split_and_legal'].to_list():
        if len(item[0]) == 2:
            print('                    ', item[0])
    # print(company_names_dict)
    # for comp in comp_name_list_without_legal:
    #     if len(comp.split()) == 1:
    #         print(comp)
    # print(comp_name_list_without_legal)
    # print(df_companies[900:1000].to_string())
    # pprint(symbol_comp_name_dict)
    # pprint(comp_name_list_split)
    # print('#########################################')
    # pprint(comp_name_list_without_legal)
    # print('#########################################')
    # pprint(company_names_dict)
    # from collections import Counter
    # pprint(Counter(word for sublist in comp_name_list_split for word in sublist))