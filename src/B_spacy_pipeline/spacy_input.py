import json
import re
import pathlib
from enum import Enum

import pandas as pd
from icecream import ic
from spacy.lang.de.stop_words import STOP_WORDS as stop_words_de
from spacy.lang.en.stop_words import STOP_WORDS as stop_words_en

from src.A_data.company_data import df_companies
from src.settings.config import ConfigBasic
from src.settings.enums import NaturalLanguage, RegexFor
from src.settings.params import company_name_bindings, company_name_articles
from src.settings.params import (company_suffixes_legal_form, common_person_names_in_company_names, company_suffixes_industry_hints, common_words_in_company_names)
from src.B_spacy_pipeline.language_data import get_most_common_words, get_most_common_names
from src.G_utils.funcs import fuzzy_similarity
from src.G_utils.regex_funcs import check_if_name_initials_in_substring
from src.G_utils.re_patterns import company_name_bindings_pattern

# Note: Used in checks:
common_terms: list = (sorted(list(set(common_words_in_company_names + get_most_common_words(language=NaturalLanguage.DE, exclude_words=company_suffixes_industry_hints) + get_most_common_words(language=NaturalLanguage.EN, exclude_words=company_suffixes_industry_hints) + list(stop_words_en) + list(stop_words_de)))))

person_names: list = (sorted(list(set(common_person_names_in_company_names + get_most_common_names(language=NaturalLanguage.EN) + get_most_common_names(language=NaturalLanguage.DE)))))


class WordType(Enum):
    CHAR_TYPE_CASE_MIX = 'CHAR_TYPE_CASE_MIX'  # letter/number/specialChar-mix, upper_after_lower
    CHAR_TYPE_CASE_MIX_SHORT = 'CHAR_TYPE_CASE_MIX_SHORT'  # like CHAR_TYPE_MIX but < 4
    UPPER_OR_LOWER = 'UPPER_OR_LOWER'  # upper-only, lower only with len >= 4  ===>>> Must not be in LEGAL
    UPPER_OR_LOWER_SHORT = 'UPPER_OR_LOWER_SHORT'  # upper-only, lower only with len < 4
    INDU_HINT = 'INDU_HINT'  # Indstry names like Pharma, Chemicals, Energy, etc.
    LEGAL_TERM = 'LEGAL_TERM'  # Legal abbreviations like SA
    SHORT_NUM = 'SHORT_NUM'  # len < 4
    LONG_NUM = 'LONG_NUM'  # len >= 4
    PER_NAME = 'PER_NAME'  # Person name
    PER_INITIAL = 'PER_INITIAL'  # Person name initials
    COMMON_WORDS = 'COMMON_WORDS'  # stop-words, common words (solution, group, dynamics) not in industry hints
    BINDING = 'BINDING'
    ARTICLE = 'ARTICLE'
    UNKNOWN = 'UNKNOWN'  # None of the above with len >= 4
    UNKNOWN_SHORT = 'UNKNOWN_SHORT'  # like UNKNOWN but len < 4


class SpacyInput:

    def __init__(self, df_companies: pd.DataFrame, min_len_word: int = 4, min_len_long_number: int = 5, fuzzy_threshold: float = 95.00):
        self.df_companies = df_companies
        self.min_len_word: int = min_len_word
        self.min_len_long_number: int = min_len_long_number
        self.fuzzy_threshold: float = fuzzy_threshold

    @staticmethod
    def compile_regex_entity_patterns() -> list[re.Pattern]:
        pattern_list = []
        with open(file=ConfigBasic.path_to_entity_regex_patterns, mode='r') as regex_file:
            json_list = list(regex_file)
            for json_str in json_list:
                result = json.loads(json_str)
                pattern_list.append(result["REGEX"])  # pattern as string
            return pattern_list

    @staticmethod
    def symbol_to_groupname_convert(symbol: str, named_group_prefix: str = 'SYMB_',
                                    do_reverse: bool = False) -> str:
        CONVERTER_MAP = {".": "_DOT_", "-": "_DASH_"}
        REVERSE_CONVERTER_MAP = {v: k for k, v in CONVERTER_MAP.items()}
        if do_reverse:
            if not symbol.startswith(named_group_prefix):
                raise ValueError(f"Named group to be converted must start "
                                 f"with symbol: {named_group_prefix}")
            symbol = symbol[len(named_group_prefix):]
            conversion_dict = REVERSE_CONVERTER_MAP
        else:
            if symbol.startswith(named_group_prefix):
                raise ValueError(f"Named group already converted as "
                                 f"it starts with symbol: {named_group_prefix}")
            symbol = named_group_prefix + symbol
            conversion_dict = CONVERTER_MAP
        regex = re.compile("|".join(map(re.escape, conversion_dict.keys())))
        return regex.sub(lambda match: conversion_dict[match.group(0)], symbol)

    @staticmethod
    def adjust_entity_regex_pattern(token_pattern: str, named_group: str) -> str:
        """ entity_regex_pattern must have space before and afterward to distinguish it from token_pattern. Token patterns
         shall match partial matches such as "Adidas-Aktie" or "BMW-Vorstand" but entity_regex_patterns shall not. """
        space_or_line_start_before: str = r'(?:(?<=\s)|(?<=^))'
        space_afterward: str = r'(?=\s)'
        regex_pattern = rf'(?P<{named_group}>{space_or_line_start_before}(?:' + token_pattern + rf'){space_afterward})'
        return regex_pattern

    def get_word_type_for_term(self, term: str) -> WordType:
        term_is_binding: bool = term.lower() in company_name_bindings
        term_is_person_name_initials: bool = check_if_name_initials_in_substring(text=term)
        term_is_person_name: bool = fuzzy_similarity(text=term.lower(), choices=person_names) > self.fuzzy_threshold and not term_is_person_name_initials
        term_is_legal_term: bool = fuzzy_similarity(text=term.lower(), choices=company_suffixes_legal_form) > self.fuzzy_threshold and not term_is_person_name_initials
        term_is_industry_hint: bool = fuzzy_similarity(text=term.lower(), choices=company_suffixes_industry_hints) > self.fuzzy_threshold
        term_is_number: bool = term.isnumeric()
        term_case_upper_after_lower: bool = not term.islower() and not term.isupper() and not term.istitle() and not term.isnumeric() and not term_is_person_name_initials
        term_is_article: bool = term.lower() in company_name_articles
        term_is_common: bool = (fuzzy_similarity(text=term.lower(), choices=common_terms) > self.fuzzy_threshold and not term_is_person_name_initials and not term_is_person_name and not term_is_legal_term and not term_is_industry_hint and not term_is_number and not term_case_upper_after_lower and not term_is_article)
        term_has_numbers_and_letters: bool = term.isalnum() and not term.isnumeric() and not term.isalpha() and not term_is_person_name_initials
        term_case_either_upper_or_lower: bool = (term.isupper() or term.islower()) and not term_is_person_name_initials and not term_is_common and not term_is_industry_hint and not term_is_legal_term

        len_term: int = len(term)

        if term_is_binding:
            word_type = WordType.BINDING
        elif term_is_article:
            word_type = WordType.ARTICLE
        elif term_is_common:
            word_type = WordType.COMMON_WORDS
        elif term_case_upper_after_lower or term_has_numbers_and_letters:
            if len_term >= self.min_len_word:
                word_type = WordType.CHAR_TYPE_CASE_MIX
            else:
                word_type = WordType.CHAR_TYPE_CASE_MIX_SHORT
        elif term_case_either_upper_or_lower:
            if len_term >= self.min_len_word:
                word_type = WordType.UPPER_OR_LOWER
            else:
                word_type = WordType.UPPER_OR_LOWER_SHORT
        elif term_is_industry_hint:
            word_type = WordType.INDU_HINT
        elif term_is_number:
            if len_term >= self.min_len_long_number:
                word_type = WordType.LONG_NUM
            else:
                word_type = WordType.SHORT_NUM
        elif term_is_person_name:
            word_type = WordType.PER_NAME
        elif term_is_person_name_initials:
            word_type = WordType.PER_INITIAL
        elif term_is_legal_term:
            word_type = WordType.LEGAL_TERM
        else:
            if len_term >= self.min_len_word:
                word_type = WordType.UNKNOWN
            else:
                word_type = WordType.UNKNOWN_SHORT
        return word_type

    def get_word_type_for_all_terms(self, name_split_list: list[str]) -> list[WordType]:
        word_type_list = list()
        for term in name_split_list:
            word_type: WordType = self.get_word_type_for_term(term=term)
            word_type_list.append(word_type)
        return word_type_list

    def single_entity_pattern_maker(self, name_split_legal: tuple[list, str | None],
                                          regex_for: RegexFor,
                                          make_regex_str: bool = True,
                                          is_for_matcher: bool = False):
        ic(name_split_legal)
        if make_regex_str:
            pattern: str = ''
        else:
            pattern: list = list()

        if regex_for == RegexFor.SPAN:
            space: str = r'\s*'
        else:
            space: str = r'\W*'

        pat: str = r'(?:\b{term}\b)'
        pat_ign_case: str = r'(?i:\b{term}\b)'
        pat_upper_lower = r'(?:\b{term}|{term_title}\b)'
        pat_opt: str = r'(?:\b{term}\b)?'
        pat_opt_ign_case: str = r'(?i:\b{term}\b)?'

        name_split_list: list[str] = name_split_legal[0]
        legal: str = name_split_legal[1]
        # Get word types for each term and put it into list:
        word_type_list: list[WordType] = self.get_word_type_for_all_terms(name_split_list=name_split_list)

        # terms:
        term1 = name_split_list[0] if len(name_split_list) >= 1 else None
        term2 = name_split_list[1] if len(name_split_list) >= 2 else None
        term3 = name_split_list[2] if len(name_split_list) >= 3 else None
        term4 = name_split_list[3] if len(name_split_list) >= 4 else None
        terms = [term1, term2, term3, term4]

        # types:
        type1 = word_type_list[0] if len(word_type_list) >= 1 else None
        type2 = word_type_list[1] if len(word_type_list) >= 2 else None
        type3 = word_type_list[2] if len(word_type_list) >= 3 else None
        type4 = word_type_list[3] if len(word_type_list) >= 4 else None

        # pattern legal:
        pat_legal = pat.format(term=legal) if make_regex_str else {'TEXT': legal} if legal is not None else None
        pat_legal_opt_case = pat_opt_ign_case.format(term=legal) if make_regex_str else {'LOWER': legal, 'OP': '?'} if legal is not None else None

        # patterns
        patterns = dict()
        patterns['pat_bind'] = company_name_bindings_pattern if make_regex_str else {'LOWER': {"REGEX": company_name_bindings_pattern}}
        for ind, t in enumerate(terms, start=1):
            if t is not None:
                patterns[f"pat{ind}"] = pat.format(term=t) if make_regex_str else {'TEXT': t}
                patterns[f"pat{ind}_opt"] = pat_opt.format(term=t) if make_regex_str else {'TEXT': t, 'OP': '?'}
                patterns[f"pat{ind}_ign_case"] = pat_ign_case.format(term=t) if make_regex_str else {'LOWER': t}
                patterns[f"pat{ind}_opt_ign_case"] = pat_opt_ign_case.format(term=t) if make_regex_str else {'LOWER': t, 'OP': '?'}
                t_title = t.title()
                terms: list = list(set([t, t_title]))
                if t == t_title:
                    patterns[f"pat{ind}_up_low"] = pat.format(term=t) if make_regex_str else {'TEXT': t}
                else:
                    patterns[f"pat{ind}_up_low"] = pat_upper_lower.format(term=t, term_title=t_title) if make_regex_str else {'TEXT': {'IN': terms}}

        # Now apply pattern according to term sequence
        if len(word_type_list) == 1:
            match type1:
                case WordType.CHAR_TYPE_CASE_MIX | WordType.CHAR_TYPE_CASE_MIX_SHORT | WordType.UPPER_OR_LOWER:  # ['1&1'], ['4imprint'], ['ABIONYX'], ['adesso'], ['adidas'],
                    pattern1 = patterns['pat1_up_low']
                    pattern_legal = pat_legal_opt_case

                case WordType.UNKNOWN:  # ['Siemens']
                    pattern1 = patterns['pat1']
                    pattern_legal = pat_legal_opt_case

                case WordType.UPPER_OR_LOWER_SHORT | WordType.LONG_NUM | WordType.PER_NAME | WordType.UNKNOWN_SHORT:  # ['3i'], ['ABC']
                    pattern1 = patterns['pat1']
                    if regex_for == RegexFor.SPAN:
                        pattern_legal = pat_legal
                    else:
                        pattern_legal = pat_legal_opt_case

                case _:  # ['450'], ['Wes']
                    pattern1 = patterns['pat1']
                    pattern_legal = pat_legal

            if make_regex_str:
                pattern += pattern1
                if pattern_legal:
                    pattern += space
                    pattern += pattern_legal
            else:
                pattern.append(pattern1)
                if pattern_legal:
                    pattern.append(space)
                    pattern.append(pattern_legal)

            ic(name_split_list, '--', word_type_list)
            ic('PATTERN:', pattern)
            ic('-------------------------------------------------------------------')

        elif len(word_type_list) == 2:
            match type1, type2:
                # CHAR_TYPE_CASE_MIX and UPPER_OR_LOWER (or vice versa):
                case WordType.CHAR_TYPE_CASE_MIX | WordType.UPPER_OR_LOWER, WordType.UPPER_OR_LOWER | WordType.CHAR_TYPE_CASE_MIX:  # ['SUESS', 'MicroTec']
                    pattern1 = patterns['pat1_up_low']
                    pattern2 = patterns['pat2_up_low']

                # CHAR_TYPE_CASE_MIX:
                case WordType.CHAR_TYPE_CASE_MIX, _:  # ['4imprint', 'Group'], ['B-A-L', 'Germany'], ['SolidWorld', 'Group'], ['Team17', 'Group'], ['TraWell', 'Co'], ['BiVictriX', 'Therapeutics']
                    pattern1 = patterns['pat1_up_low']
                    pattern2 = patterns['pat2_opt_ign_case']

                case WordType.CHAR_TYPE_CASE_MIX_SHORT, WordType.INDU_HINT:  # ['2G', 'Energy'], ['B+S', 'Banksysteme'], ['S4', 'Capital']
                    pattern1 = patterns['pat1_up_low']
                    if regex_for == RegexFor.SPAN:
                        pattern2 = patterns['pat2']
                    else:
                        pattern2 = patterns['pat2_opt_ign_case']

                case WordType.CHAR_TYPE_CASE_MIX_SHORT, _:  # ['3i', 'Corporation'], ['U10', 'Corp'], ['B&C', 'Speakers']
                    pattern1 = patterns['pat1_up_low']
                    if regex_for == RegexFor.SPAN:
                        pattern2 = patterns['pat2_ign_case']
                    else:
                        pattern2 = patterns['pat2_opt_ign_case']

                # UPPER_OR_LOWER:
                case WordType.UPPER_OR_LOWER, WordType.CHAR_TYPE_CASE_MIX:  # ['SUESS', 'MicroTec']
                    pattern1 = patterns['pat1_up_low']
                    if regex_for == RegexFor.SPAN:
                        pattern2 = patterns['pat2_ign_case']
                    else:
                        pattern2 = patterns['pat2_opt_ign_case']

                case WordType.UPPER_OR_LOWER, WordType.INDU_HINT | WordType.COMMON_WORDS | WordType.LEGAL_TERM:  # ['ABIONYX', 'Pharma'], ['BPER', 'Banca'], ['BRAIN', 'Biotech'], ['SCHOTT', 'Pharma'], ['BANIJAY', 'GROUP'], ['ASML', 'Holding']
                    pattern1 = patterns['pat1_up_low']
                    pattern2 = patterns['pat2_opt_ign_case']

                case WordType.UPPER_OR_LOWER_SHORT, WordType.COMMON_WORDS | WordType.LEGAL_TERM | WordType.INDU_HINT:  # ['BAE', 'Systems'],  ['BSF', 'Enterprise'], ['BT', 'Group'], ['SBM', 'Offshore'], ['SDI', 'Group']
                    pattern1 = patterns['pat1']
                    if regex_for == RegexFor.SPAN:
                        pattern2 = patterns['pat2_ign_case']
                    else:
                        pattern2 = patterns['pat2_opt_ign_case']

                case WordType.UPPER_OR_LOWER_SHORT, WordType.INDU_HINT | WordType.PER_NAME | WordType.UNKNOWN:  # ['BD', 'Multimedia'], ['BFF', 'Bank'], ['SGL', 'Carbon'], ['SM', 'Wirtschaftsberatungs'], ['TAG', 'Immobilien'], ['WH', 'Smith'], ['BNP', 'Paribas'], ['BOA', 'Concept']
                    pattern1 = patterns['pat1']
                    pattern2 = patterns['pat2']

                # INDU_HINT:
                case WordType.INDU_HINT, WordType.UNKNOWN | WordType.UPPER_OR_LOWER:  # ['Banca', 'Generali'], ['Banca', 'Profilo'], ['Banco', 'Santander'], ['Banca', 'IFIS'], ['Banco', 'BPM']
                    pattern1 = patterns['pat1']
                    pattern2 = patterns['pat2']

                # NUMBERS:
                case WordType.LONG_NUM, WordType.COMMON_WORDS:  # ['11880', 'Solutions']
                    pattern1 = patterns['pat1']
                    if regex_for == RegexFor.SPAN:
                        pattern2 = patterns['pat2_ign_case']
                    else:
                        pattern2 = patterns['pat2_opt_ign_case']

                case WordType.SHORT_NUM, WordType.COMMON_WORDS:  # ['123', 'Corporation']
                    pattern1 = patterns['pat1']
                    pattern2 = patterns['pat2']

                # PERSONS:
                case WordType.PER_INITIAL, WordType.PER_NAME:  # ['A.G.', 'BARR']
                    pattern1 = patterns['pat1']
                    pattern2 = patterns['pat2']

                case WordType.PER_INITIAL, WordType.UNKNOWN:  # ['S.S.', 'Lazio'], ['S.T.', 'Dupont']
                    if regex_for == RegexFor.SPAN:
                        pattern1 = patterns['pat2_ign_case']
                    else:
                        pattern1 = patterns['pat2_opt_ign_case']
                    pattern2 = patterns['pat2']

                case WordType.PER_NAME, WordType.PER_NAME:  # ['John', 'Meyer'], evtl: ['Balfour', 'Beatty'], ['Barbara', 'Bui'], ['Robert', 'Walters']
                    pattern1 = patterns['pat1']
                    pattern2 = patterns['pat2']

                case WordType.PER_NAME, WordType.INDU_HINT | WordType.COMMON_WORDS:  # ['Schneider', 'Electric'], ['Smiths', 'News'], ['Smiths', 'Group']
                    pattern1 = patterns['pat1']
                    if regex_for == RegexFor.SPAN:
                        pattern2 = patterns['pat2_ign_case']
                    else:
                        pattern2 = patterns['pat2_opt_ign_case']
                # UNKNOWN:
                case WordType.UNKNOWN, WordType.CHAR_TYPE_CASE_MIX | WordType.UNKNOWN | WordType.SHORT_NUM:  # ['Amadeus', 'FiRe'], ['Tritax', 'EuroBox'], ['Anglo', 'American'], ['Balfour', 'Beatty'], ['Bastei', 'Luebbe'], ['Argentum', '47']
                    pattern1 = patterns['pat1']
                    pattern2 = patterns['pat2']

                case WordType.UNKNOWN, WordType.COMMON_WORDS:  # ['Amigo', 'Holdings'], ['Bakkavor', 'Group'], ['Barratt', 'Developments'], ['Sareum', 'Holdings'], ['Singular', 'People']
                    pattern1 = patterns['pat1']
                    pattern2 = patterns['pat2_opt_ign_case']

                case WordType.UNKNOWN, WordType.INDU_HINT:  # ['Amplitude', 'Surgical'], ['Baader', 'Bank'], ['Barinthus', 'Biotherapeutics'], ['Beowulf', 'Mining']
                    pattern1 = patterns['pat1']
                    pattern2 = patterns['pat2']

                case WordType.UNKNOWN_SHORT, WordType.PER_NAME | WordType.UNKNOWN:  # ['S', 'Meyer']
                    pattern1 = patterns['pat1']
                    pattern2 = patterns['pat2']

                # COMMON_WORDS:
                case WordType.COMMON_WORDS, WordType.UNKNOWN | WordType.PER_NAME | WordType.UPPER_OR_LOWER | WordType.UPPER_OR_LOWER_SHORT:  # ['Koninklijke', 'Philips'], ['Koninklijke', 'KPN'],
                    pattern1 = patterns['pat1_opt']
                    pattern2 = patterns['pat2']

                case WordType.COMMON_WORDS, WordType.INDU_HINT | WordType.COMMON_WORDS:  # ['Silence', 'Therapeutics'], ['Benchmark', 'Holdings'], ['Science', 'Group']
                    pattern1 = patterns['pat1']
                    pattern2 = patterns['pat2']

                case WordType.COMMON_WORDS, WordType.UNKNOWN_SHORT:  # ['Triple', 'P']
                    pattern1 = patterns['pat1']
                    pattern2 = patterns['pat2']

                # LEGAL_TERM
                case WordType.LEGAL_TERM, WordType.UNKNOWN | WordType.CHAR_TYPE_CASE_MIX_SHORT:  # ['SA', 'Energisme'], ['SA', 'Entreparticuliers.com'], ['SAS', 'Florentaise'], ['SAS', 'AG3i']
                    if regex_for == RegexFor.SPAN:
                        pattern1 = patterns['pat1_ign_case']
                    else:
                        pattern1 = patterns['pat1_opt_ign_case']
                    pattern2 = patterns['pat2']

                case _:
                    pattern1 = patterns['pat1']
                    pattern2 = patterns['pat2']

            pattern_legal = pat_legal_opt_case
            if make_regex_str:
                pattern += (pattern1 + space + pattern2 + space + pattern_legal)
            else:
                pattern.append(pattern1)
                pattern.append(space)
                pattern.append(pattern2)
                pattern.append(space)
                pattern.append(pattern_legal)

            ic(name_split_list, '--', word_type_list)
            ic('PATTERN:', pattern)
            ic('-------------------------------------------------------------------')

        elif len(word_type_list) == 3:

            match type1, type2, type3:
                # CHAR_TYPE_CASE_MIX and UPPER_OR_LOWER (or vice versa):
                case WordType.CHAR_TYPE_CASE_MIX | WordType.UPPER_OR_LOWER, WordType.UPPER_OR_LOWER | WordType.CHAR_TYPE_CASE_MIX, _:  #
                    pattern1 = patterns['pat1_up_low']
                    pattern2 = patterns['pat2_up_low']
                    pattern3 = patterns['pat3_opt']

                # BINDINGS
                case _, WordType.BINDING, _:
                    pattern1 = patterns['pat1']
                    pattern2 = patterns['pat_bind']
                    pattern3 = patterns['pat3']
                # CHAR_TYPE_CASE_MIX:

                # UPPER OR LOWER
                case WordType.UPPER_OR_LOWER | WordType.CHAR_TYPE_CASE_MIX, _, _:  # ['DEFAMA', 'Deutsche', 'Fachmarkt'], ['ACCENTRO', 'Real', 'Estate']
                    pattern1 = patterns['pat1_up_low']
                    pattern2 = patterns['pat2_opt']
                    pattern3 = patterns['pat3_opt']

                case WordType.UPPER_OR_LOWER_SHORT, WordType.UPPER_OR_LOWER_SHORT | WordType.INDU_HINT, _:  # ['ABN', 'AMRO', 'Bank'], ['AEW', 'UK', 'REIT'], ['RIT', 'Capital', 'Partners']
                    pattern1 = patterns['pat1']
                    pattern2 = patterns['pat2']
                    pattern3 = patterns['pat3_opt_ign_case']

                case WordType.UPPER_OR_LOWER_SHORT, _, WordType.INDU_HINT:  # ['ATON', 'Green', 'Storage']
                    pattern1 = patterns['pat1']
                    if regex_for == RegexFor.SPAN:
                        pattern2 = patterns['pat2']
                        pattern3 = patterns['pat3']
                    else:
                        pattern2 = patterns['pat2_opt_ign_case']
                        pattern3 = patterns['pat3_opt_ign_case']

                case WordType.UPPER_OR_LOWER_SHORT, _, _:  # ['ASA', 'International', 'Group'], ['ADVA', 'Optical', 'Networking'], ['AEW', 'UK', 'REIT'], ['ASA', 'International', 'Group']
                    pattern1 = patterns['pat1']
                    if regex_for == RegexFor.SPAN:
                        pattern2 = patterns['pat2']
                    else:
                        pattern2 = patterns['pat2_opt']
                    pattern3 = patterns['pat3_opt']

                # PERSONS:
                case WordType.PER_INITIAL, _, _:  # ['A.S.', 'Creation', 'Tapeten']
                    pattern1 = patterns['pat1']
                    pattern2 = patterns['pat2']
                    pattern3 = patterns['pat3_opt_ign_case']

                case WordType.PER_NAME, WordType.PER_NAME, _:  # ['Johnson', 'Smith']
                    pattern1 = patterns['pat1']
                    pattern2 = patterns['pat2']
                    pattern3 = patterns['pat3_opt_ign_case']

                case WordType.PER_NAME, WordType.COMMON_WORDS | WordType.INDU_HINT, _:  # ['Alba', 'Mineral', 'Resources']
                    pattern1 = patterns['pat1']
                    pattern2 = patterns['pat2']
                    pattern3 = patterns['pat3_opt_ign_case']

                # ARTICLES
                case WordType.ARTICLE, _, _:  # ['The', 'Alumasc', 'Group'], ['The', 'Blockchain', 'Group'], ['The', 'Heavitree', 'Brewery'], ['The', 'PRS', 'REIT']
                    pattern1 = patterns['pat1']
                    pattern2 = patterns['pat2']
                    pattern3 = patterns['pat3']

                case _, WordType.ARTICLE, _:  # ['Aeroports', 'de', 'Paris'], ['Banco', 'de', 'Sabadell'], ['Asturiana', 'de', 'Laminados']
                    pattern1 = patterns['pat1']
                    pattern2 = patterns['pat2']
                    pattern3 = patterns['pat3']

                # INDUSTRY HINT
                case WordType.INDU_HINT, WordType.COMMON_WORDS, WordType.LEGAL_TERM:  # ['Auction', 'Technology', 'Group'], ['Auto', 'Trader', 'Group']
                    pattern1 = patterns['pat1']
                    pattern2 = patterns['pat2']
                    pattern3 = patterns['pat3_opt_ign_case']

                case WordType.INDU_HINT, WordType.INDU_HINT, WordType.COMMON_WORDS | WordType.INDU_HINT:  # ['Capital', 'Venture', 'Europe']
                    pattern1 = patterns['pat1']
                    pattern2 = patterns['pat2']
                    pattern3 = patterns['pat3']

                # COMMON
                case WordType.COMMON_WORDS, WordType.COMMON_WORDS | WordType.UPPER_OR_LOWER_SHORT | WordType.INDU_HINT, WordType.LEGAL_TERM:  # ['ABOUT', 'YOU', 'Holding'], ['Alphawave', 'IP', 'Group'], ['Big', 'Yellow', 'Group'], ['Active', 'Energy', 'Group'], ['Amadeus', 'IT', 'Group'], ['BE', 'Semiconductor', 'Industries']
                    pattern1 = patterns['pat1']
                    pattern2 = patterns['pat2']
                    pattern3 = patterns['pat3_opt_ign_case']

                case WordType.COMMON_WORDS, WordType.LEGAL_TERM, WordType.COMMON_WORDS:  # ['Alpha', 'Group', 'International']
                    pattern1 = patterns['pat1']
                    pattern2 = patterns['pat2']
                    pattern3 = patterns['pat3_opt_ign_case']

                case WordType.COMMON_WORDS, WordType.COMMON_WORDS | WordType.INDU_HINT, WordType.COMMON_WORDS | WordType.INDU_HINT:   # ['Advanced', 'Bitcoin', 'Technologies'], ['Alternative', 'Income', 'REIT'], ['Applied', 'Graphene', 'Materials'], ['Associated', 'British', 'Foods'], ['Beta', 'Systems', 'Software']
                    pattern1 = patterns['pat1']
                    pattern2 = patterns['pat2']
                    pattern3 = patterns['pat3']

                case WordType.COMMON_WORDS, WordType.UPPER_OR_LOWER | WordType.UPPER_OR_LOWER_SHORT, WordType.COMMON_WORDS:
                    pattern1 = patterns['pat1_opt']
                    pattern2 = patterns['pat2']
                    if regex_for == RegexFor.SPAN:
                        pattern3 = patterns['pat3']
                    else:
                        pattern3 = patterns['pat3_opt']

                # UNKNOWNS
                case WordType.UNKNOWN, WordType.UNKNOWN | WordType.COMMON_WORDS, WordType.LEGAL_TERM:  # ['Aukett', 'Swanke', 'Group'], ['Begbies', 'Traynor', 'Group'], ['Britannia', 'Bulk', 'Holdings']
                    pattern1 = patterns['pat1']
                    pattern2 = patterns['pat2']
                    pattern3 = patterns['pat3_opt_ign_case']

                case WordType.UNKNOWN, WordType.UNKNOWN, WordType.COMMON_WORDS | WordType.INDU_HINT:  # ['Bayerische', 'Motoren', 'Werke'], ['Brioschi', 'Sviluppo', 'Immobiliare']
                    pattern1 = patterns['pat1']
                    pattern2 = patterns['pat2']
                    pattern3 = patterns['pat3_opt_ign_case']

                case WordType.UNKNOWN, _, _:  # ['Aptitude', 'Software', 'Group'], ['Arbuthnot', 'Banking', 'Group'], ['Arteche', 'Lantegi', 'Elkartea'], ['Ashtead', 'Technology', 'Holdings']
                    pattern1 = patterns['pat1']
                    if regex_for == RegexFor.SPAN:
                        pattern2 = patterns['pat2']
                        pattern3 = patterns['pat3']
                    else:
                        pattern2 = patterns['pat2_opt_ign_case']
                        pattern3 = patterns['pat3_opt_ign_case']

                case WordType.UNKNOWN_SHORT, WordType.INDU_HINT, WordType.COMMON_WORDS:  # ['Atai', 'Life', 'Sciences']
                    pattern1 = patterns['pat1']
                    pattern2 = patterns['pat2']
                    pattern3 = patterns['pat3_opt_ign_case']

                # OTHERS
                case _:
                    pattern1 = patterns['pat1']
                    pattern2 = patterns['pat2']
                    pattern3 = patterns['pat3']

            pattern_legal = pat_legal_opt_case
            if make_regex_str:
                pattern += (pattern1 + space + pattern2 + space + pattern3 + space + pattern_legal)
            else:
                pattern.append(pattern1)
                pattern.append(space)
                pattern.append(pattern2)
                pattern.append(space)
                pattern.append(pattern3)
                pattern.append(space)
                pattern.append(pattern_legal)

            ic(name_split_list, '--', word_type_list)
            ic('PATTERN:', pattern)
            ic('-------------------------------------------------------------------')

        else:
            match type1, type2, type3, type4:
                # CHAR_TYPE_CASE_MIX and UPPER_OR_LOWER (or vice versa):
                case WordType.CHAR_TYPE_CASE_MIX | WordType.UPPER_OR_LOWER, WordType.UPPER_OR_LOWER | WordType.CHAR_TYPE_CASE_MIX, _, _:  #
                    pattern1 = patterns['pat1_up_low']
                    pattern2 = patterns['pat2_up_low']
                    pattern3 = patterns['pat3_opt']
                    pattern4 = patterns['pat4_opt']

                # BINDINGS
                case _, WordType.BINDING, _, _:
                    pattern1 = patterns['pat1']
                    pattern2 = patterns['pat_bind']
                    pattern3 = patterns['pat3']
                    pattern4 = patterns['pat4_opt_ign_case']

                # UPPER LOWER
                case (WordType.UPPER_OR_LOWER | WordType.UPPER_OR_LOWER_SHORT | WordType.CHAR_TYPE_CASE_MIX | WordType.CHAR_TYPE_CASE_MIX_SHORT, WordType.COMMON_WORDS, WordType.COMMON_WORDS, WordType.COMMON_WORDS | WordType.INDU_HINT):
                    pattern1 = patterns['pat1']
                    pattern2 = patterns['pat2_opt_ign_case']
                    pattern3 = patterns['pat3_opt_ign_case']
                    pattern4 = patterns['pat4_opt_ign_case']

                # PERSONS
                case WordType.PER_NAME, WordType.PER_NAME, _, _:
                    pattern1 = patterns['pat1']
                    pattern2 = patterns['pat2']
                    pattern3 = patterns['pat3_opt_ign_case']
                    pattern4 = patterns['pat4_opt_ign_case']

                # COMMON
                case WordType.COMMON_WORDS, WordType.COMMON_WORDS | WordType.INDU_HINT, WordType.COMMON_WORDS, _:
                    pattern1 = patterns['pat1']
                    pattern2 = patterns['pat2']
                    pattern3 = patterns['pat3']
                    pattern4 = patterns['pat4_opt_ign_case']

                case _, _, WordType.BINDING, _:
                    pattern1 = patterns['pat1']
                    pattern2 = patterns['pat2']
                    pattern3 = patterns['pat_bind']
                    pattern4 = patterns['pat4']

                case _, _, _, WordType.BINDING:
                    pattern1 = patterns['pat1']
                    pattern2 = patterns['pat2']
                    pattern3 = patterns['pat3']
                    pattern4 = patterns['pat_bind']


                # LEGAL
                case _, _, _, WordType.LEGAL_TERM:
                    pattern1 = patterns['pat1']
                    pattern2 = patterns['pat2']
                    pattern3 = patterns['pat3']
                    pattern4 = patterns['pat4_opt_ign_case']

                case _:
                    pattern1 = patterns['pat1']
                    pattern2 = patterns['pat2']
                    pattern3 = patterns['pat3']
                    pattern4 = patterns['pat4']

            if make_regex_str:
                pattern += (pattern1 + space + pattern2 + space + pattern3 + space + pattern4)
            else:
                pattern.append(pattern1)
                pattern.append(space)
                pattern.append(pattern2)
                pattern.append(space)
                pattern.append(pattern3)
                pattern.append(space)
                pattern.append(pattern4)

            if len(word_type_list) > 4:

                for term in name_split_list[4:]:
                    if make_regex_str:
                        pattern += space
                        pattern += pat_opt_ign_case.format(term=term)
                    else:
                        pattern.append(space)
                        pattern.append({'LOWER': term, 'OP': '?'})

                pattern_legal = pat_legal_opt_case
                if pattern_legal:
                    if make_regex_str:
                        pattern += space
                        pattern += pattern_legal
                    else:
                        pattern.append(space)
                        pattern.append(pattern_legal)
            ic(name_split_list, '--', word_type_list)
            ic(pattern)
            ic('-------------------------------------------------------------------')

        if not make_regex_str and is_for_matcher:
            pattern = [item for item in pattern if isinstance(item, dict)] if is_for_matcher and not make_regex_str else pattern

        return pattern

    def create_and_save_entity_patterns(self, entity_label: str = ConfigBasic.spacy_comp_label):
        """ The first "with..." here creates "entity_ruler_patterns", the second creates "entity_token_matcher_patterns" """
        start = 20
        end = 30
        path = pathlib.Path('/media/rainergo/PROJECTS/UASFRA-MS-Thesis/src/B_spacy_pipeline/patterns')
        with open(file=path / 'entity_ruler_patterns.jsonl', mode='w', encoding='utf-8') as span_file:
            for _, row in self.df_companies.iloc[start:end].iterrows():
                span_pattern: list = self.single_entity_pattern_maker(name_split_legal=row['name_split_and_legal'], regex_for=RegexFor.SPAN, make_regex_str=False, is_for_matcher=True)
                pattern = {"label": entity_label, "pattern": span_pattern, "id": row['name']}
                json.dump(pattern, span_file)
                span_file.write('\n')
        with open(file=path / 'entity_token_matcher_patterns.jsonl', mode='w', encoding='utf-8') as token_file:
            for _, row in df_companies.iloc[start:end].iterrows():
                token_pattern: str = self.single_entity_pattern_maker(name_split_legal=row['name_split_and_legal'], regex_for=RegexFor.TOKEN, make_regex_str=True)
                pattern = {row['name']: [[{'TEXT': {"REGEX": token_pattern}}]]}
                json.dump(pattern, token_file)
                token_file.write('\n')
        with open(file=path / 'entity_regex_patterns.jsonl', mode='w', encoding='utf-8') as regex_file:
            for _, row in df_companies.iloc[start:end].iterrows():
                token_pattern: str = self.single_entity_pattern_maker(name_split_legal=row['name_split_and_legal'], regex_for=RegexFor.SPAN, make_regex_str=True)
                named_group = self.symbol_to_groupname_convert(row['symbol'])
                regex_pattern: str = self.adjust_entity_regex_pattern(token_pattern=token_pattern, named_group=named_group)
                pattern = {"comp_name": row['name'], "REGEX": regex_pattern}
                json.dump(pattern, regex_file)
                regex_file.write('\n')



if __name__ == '__main__':
    # ic.disable()
    ic.enable()
    # print(df_companies.head(n=20).to_string())

    spin = SpacyInput(df_companies=df_companies)
    # print(spin.compile_regex_entity_patterns())
    spin.create_and_save_entity_patterns()
    # for item in df_companies['name_split_and_legal'].to_list():
    #     if len(item[0]) == 3:
    #         spin.single_entity_pattern_maker(name_split_legal=item, regex_for=RegexFor.TOKEN)  # frequency = {f'c{i}': eval(f'spin.c{i}') for i in range(0, 44)}  # pprint(frequency)
