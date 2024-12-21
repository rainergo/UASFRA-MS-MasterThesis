""" sources:
    - https://github.com/chartbeat-labs/textacy/blob/main/src/textacy/preprocessing/resources.py
"""
import re
from typing import Pattern

from src.settings.params import (company_suffixes_legal_form, abbrevs_numerals,
                                 abbrevs_lengths, abbrevs_and_company_suffixes_with_dot_at_end)
from src.settings.params import (hyphen_chars, repeat_chars, www_domains, sentence_end_chars,
                                 required_seperator_at_last_position_of_geo_pattern, company_name_bindings)

# Section ################################   FUNCTIONS   ######################################################
ESC_CHARS_REPL_MAP = {" ": "[ ]", ".": r"\.", "^": r"\^", "$": r"\$", "*": r"\*", "+": r"\+", "-": r"\-", "?": r"\?",
                      "(": r"\(", ")": r"\)", "[": r"\[", "]": r"\]", "{": r"\{", "}": r"\}", "|": r"\|", "\\": "\\\\"}


def make_pattern_from_raw_str_iterable(raw_str_iterable: list[str] | str | tuple[str] | str | dict[str, any],
                                       must_contain_either: list[str] = None, as_group: bool = False, as_words: bool = False, in_list: bool = False) -> str:
    if raw_str_iterable is None or len(raw_str_iterable) == 0:
        return ''
    raw_str_list_new = []
    if must_contain_either is not None:
        for character in must_contain_either:
            for raw_str in raw_str_iterable:
                if character in raw_str:
                    raw_str_list_new.append(raw_str)
    else:
        raw_str_list_new = raw_str_iterable
    escaped_str_list: list = [ele.translate(str.maketrans(ESC_CHARS_REPL_MAP)) for ele in raw_str_list_new]
    if in_list:
        pattern_string = '[' + ''.join(escaped_str_list) + ']+'
    else:
        pattern_string: str = '|'.join(escaped_str_list)
    if as_words:
        pattern_string = r'\b(?:' + pattern_string + r')\b'
    if as_group:
        pattern_string = '(?:' + pattern_string + ')'
    return pattern_string


def pattern_maker_remove_before_after(rem_before_pattern: Pattern or None = None,
                                      rem_after_pattern: Pattern or None = None,
                                      rem_before_words: list[str] or None = None,
                                      rem_after_words: list[str] or None = None,
                                      flag_ignorecase: bool = True,
                                      flag_multiline: bool = False,
                                      limit_chars_before_after: int = 500) -> Pattern:
    if rem_before_pattern and rem_before_words or rem_after_pattern and rem_after_words:
        raise ValueError("Either rem_..._words or rem_..._patterns can be used, but not both at the same time!")

    pattern_list = [
        fr"(\A(.|\n){{,{limit_chars_before_after}}}?{rem_before_pattern}[\s\-]*)" if rem_before_pattern else None,
        fr"([\s\-]*{rem_after_pattern}(.|\n)*$)" if rem_after_pattern else None,
        fr"(\A(.|\n){{,{limit_chars_before_after}}}?({'|'.join([ele.translate(str.maketrans(ESC_CHARS_REPL_MAP)) for ele in rem_before_words])})[\s\-]*)" if rem_before_words else None,
        fr"([\s\-]*({'|'.join([ele.translate(str.maketrans(ESC_CHARS_REPL_MAP)) for ele in rem_after_words])})(.|\n)*$)" if rem_after_words else None]
    pattern_string = '|'.join([ele for ele in pattern_list if ele is not None])
    match (flag_ignorecase, flag_multiline):
        case (True, True):
            flags = (re.IGNORECASE | re.MULTILINE)
        case (True, False):
            flags = re.IGNORECASE
        case (False, True):
            flags = re.MULTILINE
        case _:
            flags = re.NOFLAG
    return re.compile(pattern=pattern_string, flags=flags)


def or_patterns(compiled_patterns: list[Pattern]) -> Pattern:
    return re.compile('(' + '|'.join([pat.pattern for pat in compiled_patterns]) + ')', flags=re.IGNORECASE)


def and_patterns(compiled_patterns: list[Pattern]) -> Pattern:
    return re.compile('(' + ''.join([pat.pattern for pat in compiled_patterns]) + ')', flags=re.IGNORECASE)


def make_negative_lookbehinds_no_words_with_dot_at_end(abbrevs_with_dot_at_end: list[str]) -> str:
    escaped_list_of_diff_len_strings = [
        (re.sub(pattern=r"(?P<prev>\b(?:\w|\.)+\b)(?P<dot>\.)", repl=lambda m: m.group('prev'), string=ele)) for ele in
        abbrevs_with_dot_at_end]
    list_of_list_of_diff_len_strings = [
        [ele.replace('.', r'\.') for ele in escaped_list_of_diff_len_strings if len(ele) == lengths] for lengths in
        list(set([len(exp) for exp in escaped_list_of_diff_len_strings]))]
    negative_lookbehinds = ''
    for list_of_strings in list_of_list_of_diff_len_strings:
        list_of_strings_as_string = '|'.join(list_of_strings)
        neg_lookbehind: str = r"(?<!(?:" + list_of_strings_as_string + r"))"
        negative_lookbehinds += neg_lookbehind
    return negative_lookbehinds

# Section ################################ PATTERNS FROM PARAMS #########################################
company_suffixes = make_pattern_from_raw_str_iterable(
    raw_str_iterable=company_suffixes_legal_form, as_group=False)

company_legal_suffixes = make_pattern_from_raw_str_iterable(raw_str_iterable=company_suffixes_legal_form,
                                                            as_group=False)

company_legal_suffixes_as_group = make_pattern_from_raw_str_iterable(raw_str_iterable=company_suffixes_legal_form,
                                                                     as_group=True)

header_terms: str = make_pattern_from_raw_str_iterable(
    raw_str_iterable=company_suffixes_legal_form + abbrevs_numerals + abbrevs_lengths,
    must_contain_either=['.', ':'],
    as_group=False)
measurement_pattern: str = make_pattern_from_raw_str_iterable(raw_str_iterable=abbrevs_lengths + abbrevs_numerals,
                                                              as_group=True)
hyphen_char_pattern: str = make_pattern_from_raw_str_iterable(raw_str_iterable=hyphen_chars, as_group=True)
www_domain_pattern: str = make_pattern_from_raw_str_iterable(raw_str_iterable=www_domains, as_group=False)

negative_lookbehinds_no_words_with_dot_at_end: str = make_negative_lookbehinds_no_words_with_dot_at_end(
    abbrevs_with_dot_at_end=abbrevs_and_company_suffixes_with_dot_at_end)

sentence_end_chars_pattern: str = rf"[{''.join(sentence_end_chars)}]"

company_name_bindings_pattern: str = make_pattern_from_raw_str_iterable(raw_str_iterable=company_name_bindings, as_group=True)


# ToDo: NOT YET IN A_NLP
RE_SENT_END_EXCLUDING_WORDS_WITH_DOT: Pattern = re.compile(
    negative_lookbehinds_no_words_with_dot_at_end
    + sentence_end_chars_pattern,
    flags=re.IGNORECASE | re.MULTILINE
)


# ToDo: This originally comes from project "OpenBBTerminal"
RE_COMPANY_NAME_SPLIT_TO_NAME_AND_LEGAL: re.Pattern = re.compile(
    pattern=r'^(?:(?:(?P<name>.+?)?(?:\s+)?(?P<legal>\b'
            + company_legal_suffixes_as_group
            + r'))|(?P<name2>.+))$'
    , flags=re.IGNORECASE | re.MULTILINE)


# Section ################################ BRACKETS #########################################
RE_BRACKETS_CURLY_AND_CONTENT: Pattern = re.compile(r"\{[^{}]*?\}")
RE_BRACKETS_ROUND_AND_CONTENT: Pattern = re.compile(r"\([^()]*?\)")
RE_BRACKETS_SQUARE_AND_CONTENT: Pattern = re.compile(r"\[[^\[\]]*?\]")
RE_BRACKETS_CURLY: Pattern = re.compile(r"[{}]")
RE_BRACKETS_ROUND: Pattern = re.compile(r"[()]")
RE_BRACKETS_SQUARE: Pattern = re.compile(r"[\[\]]")

# Section ################################ LINEBREAKS, SPACES ################################
RE_LINEBREAK: Pattern = re.compile(r"(\r\n|[\n\v])+")
RE_NONBREAKING_SPACE: Pattern = re.compile(r"[^\S\n\v]+")
RE_ZERO_WIIDTH_SPACE: Pattern = re.compile(r"[\u200B\u2060\uFEFF]+")
RE_SPACE_BEFORE_SENT_END_AND_COMMAS_AND_COLONS: Pattern = re.compile(r"(?<=.)(?P<excesspaceb>\s+)(?=[.,;!?]\s+)")
RE_NO_SPACE_BEFORE_NEXT_SENT: Pattern = re.compile(rf"(?<=\w)(?P<sentendchar>{sentence_end_chars_pattern})(?=[A-ZÄÖÜ]\w+\s)")
RE_LINE_END_DASH_FOLLOWED_BY_NEW_LINE: Pattern = re.compile(r"(?P<beforedash>^.+)(?P<linenenddash>[ ]+\-[ ]*$\n)",
                                                            flags=re.MULTILINE)

# Section ################################ LISTINGS ###########################################

TO_FORMAT_LISTING_SENTS: str = (r"(?P<listing>(?:(?P<beforechar>(?:\W|\A))\n*)"
                                rf"(?P<hyphen>^[ ]*[{hyphen_chars}][ ]+)"
                                r"(?:(?P<short>(?P<sentshort1>(?:[^\n]){{1,{max_line_len}}}$)"
                                rf"(?:(?P<nextlist>(?=[ ]*\n[ ]*[{hyphen_chars}]))|(?=(?P<nextsent>(?:[^\n]*\n[^{hyphen_chars}\n]+)))$)"
                                r")|(?(short)|(?P<long>(?P<sentlong>(?:[^\n])+)))))")

# Section ################################ HEADERS, SECTIONS #####################################

RE_HEADLINE: re.Pattern = re.compile(
    rf"(?:(?P<headline>\A\n*[^\n]+?(?P<sentendchar>{sentence_end_chars_pattern})?[ ]*)(?P<newline>\n?)(?(newline)(?=^(?:[A-ZÄÖÜ\n]|(?P<compnamelowercase>\b[^\n]{{1,20}}\b[ ]*(?:\b(?i:{company_suffixes})\b))))))",
    flags=re.MULTILINE)

RE_MULTIPLE_HEADLINES: re.Pattern = re.compile(r"(?P<headline>\A\n*[^\n]+$)(?(headline)\n+|)" +
                                     rf"(?P<next1>(?:[A-ZÄÖÜ\n]|(?P<compnamelowercase>\b[^\n]{{1,20}}\b[ ]*(?:\b(?:{company_legal_suffixes})\b)))[^\n]+$(?=\n+))?" +
                                     r"(?(next1)\n|)" +
                                     rf"(?P<next2>\b[A-ZÄÖÜ][^\n]+$(?=\n+))?(?(next2)\n|)" +
                                     rf"(?P<next3>\b[A-ZÄÖÜ][^\n]+$(?=\n+))?(?(next3)\n|)" +
                                     rf"(?P<next4>\b[A-ZÄÖÜ][^\n]+$(?=\n+))?(?(next4)\n|)" +
                                     rf"(?P<next5>\b[A-ZÄÖÜ][^\n]+$(?=\n+))?(?(next5)\n|)" +
                                     rf"(?P<next6>\b[A-ZÄÖÜ][^\n]+$(?=\n+))?(?(next6)\n|)" +
                                     rf"(?P<next7>\b[A-ZÄÖÜ][^\n]+$(?=\n+))?(?(next7)\n|)" +
                                     rf"(?P<next8>\b[A-ZÄÖÜ][^\n]+$(?=\n+))?(?(next8)\n|)",
                                               flags=re.MULTILINE)

TO_FORMAT_RE_SECTION_HEADER: str = (r"(?<!\A)(?P<before>(?P<emptyline>(?<=\n\n))|"
                                    rf"(?P<period>(?<={sentence_end_chars_pattern}\n))|(?P<noperiod>(?<=\n)))(?P<sectionheader>(?(noperiod)(?P<uppercasestart>\b[A-ZÄÖÜ]+)|)"
                                    r".{{1,{max_chars_short_sents}}}?"
                                    rf"(?P<sentendchar>{sentence_end_chars_pattern})?[ ]*$)(?P<after>(?=(?P<uppercase>\n\b[A-ZÄÖÜ]\w+))|"
                                    r"(?=(?P<companyname>\n\b[^\n]{{1,30}}"
                                    rf"\b(?i:{company_suffixes})\b)))")     # Note: Company suffixes must be re.IGNORECASE

RE_ALL_SECTIONS_IN_TEXT: Pattern = re.compile(
    pattern=rf"(?P<section>(?:(?<=\n\n)|\A).+?(?P<sentendchar>{sentence_end_chars_pattern})?[ ]*(?:(?=\n\n)|\Z))",
    flags=re.DOTALL)

TO_FORMAT_LINES_WITH_MAX_CHARS: str = r"^[^\n]{{1,{max_line_len}}}?" + rf"(?P<sentendchar>{sentence_end_chars_pattern})?[ ]*$"

# Section ################################ DATES AND TIMES ########################################
day_num: str = r"[0-3]?[0-9](?:st|nd|rd|th)?"
month_name: str = r"(?:jan|feb|m[aä]r|apr|ma[iy](?!\w)|jun|jul|aug|sep|o[ck]t|nov|de[cz])\w*\b"
month_num: str = r"[0-1]?[0-9]"
year_num: str = r"(?:[1|2][0|9])?[0-9]{2}"

RE_DATE_1_DAY_MONTHNAME_YEAR: Pattern = re.compile(
    rf"(?P<date1>(?<![\w\d])(?P<day1>{day_num})[. /-]+(?(day1)\b(?P<monthname1>{month_name})[,. /-]+(?P<year1>{year_num}))(?!\d|\w))",
    flags=re.IGNORECASE)

RE_DATE_2_MONTHNAME_DAY_YEAR: Pattern = re.compile(
    rf"(?P<date2>(?<![\w\d])\b(?P<monthname2>{month_name})[ ,/-]+(?P<day2>{day_num})[ ,/-]+(?P<year2>{year_num})(?!\d|\w))",
    flags=re.IGNORECASE)

RE_DATE_3_DAY_MONTHNUMBER_YEAR: Pattern = re.compile(
    rf"(?P<date3>(?<![\w\d])(?P<day3>{day_num})[. /-]+(?P<monthnum3>{month_num})[. /-]+(?P<year3>{year_num})(?!\d|\w))",
    flags=re.IGNORECASE)
RE_DATE_4_YEAR_MONTHNUMBER_DAY: Pattern = re.compile(
    rf"(?P<date4>(?<![\w\d])(?P<year4>{year_num})[. /-]+(?P<monthnum4>{month_num})[. /-]+(?P<day4>{day_num})(?!\d|\w))",
    flags=re.IGNORECASE)

RE_MONTH_YEAR: Pattern = re.compile(
    rf"(?P<date5>\b(?:(?P<day51>{day_num})(?:[\.\s\/\-,]*))?(?P<month5>{month_name}\s*(?:(?P<day52>{day_num})(?:[\.\s\/\-,]*))?(?P<year5>{year_num}))\b)",
    flags=re.IGNORECASE)

RE_DATE_EXACT: Pattern = re.compile('(?P<date>' + '|'.join(
    [RE_DATE_1_DAY_MONTHNAME_YEAR.pattern,
     RE_DATE_2_MONTHNAME_DAY_YEAR.pattern,
     RE_DATE_3_DAY_MONTHNUMBER_YEAR.pattern,
     RE_DATE_4_YEAR_MONTHNUMBER_DAY.pattern]) + ')',
                                    flags=re.IGNORECASE)

RE_TIME_SIMPLE: Pattern = re.compile(
    r"(?P<timesimple>(?P<hour>[0-2]?[0-9])[:.](?P<min>[0-5][0-9])[:.]?(?P<sec>[0-5][0-9])?[ ]*(?P<pm>p\.?m\.?)?[ ]*(?P<am>a\.?m\.?)?[ ]*)")
RE_TIME_ADDONS: Pattern = re.compile(
    r"(?P<timeaddons>(?:GMT|UTC)(?P<offset>[+-]\d\d?)?|(?P<tzname>\b(?:CET|EET|GMT[^\w+-]|UTC[^\w+-]|UCT[^\w+-]|EST|WET|MET|HST|MST)\b)?(?P<timesuffix>\b/?(CEST|EEST)\b)?)")
RE_TIME_COMPLEX: Pattern = re.compile(
    r"(?:"
    + RE_TIME_SIMPLE.pattern
    + r"\W*"
    + RE_TIME_ADDONS.pattern
    + r"?"  # Note: optional TIME_ADDONS
      r")"
    ,
    flags=re.IGNORECASE | re.VERBOSE
)

RE_DATE_AND_TIME = re.compile(RE_DATE_EXACT.pattern + r"[ /-]*" + RE_TIME_COMPLEX.pattern + r"\b", flags=re.IGNORECASE)

# Subsection: Aggregated patterns containing Date, Time, Geolocation:
# Note: RE_POTENTIAL_GEO can contain a maximum of 2 lower case words, all other words must be uppercase:
RE_POTENTIAL_GEO: Pattern = re.compile(
    r"(?-i:(?P<potentialgeo>(?P<startupper>\b[A-ZÄÖÜ]\w+\b[^\n\w]*)+(?P<potentiallower>\b\w+\b[^\n\w]*){,2}(?P<upperagain>\b[A-ZÄÖÜ]\w+\b[^\n\w]*)*)[^\n\w]*)")

RE_ART_DATELINE_LOCATION_DATE: Pattern = re.compile(
    r"^[ ]*" +
    RE_POTENTIAL_GEO.pattern
    # + r"(?:" #
    + RE_DATE_EXACT.pattern
    # + r"|" #
    # + RE_MONTH_YEAR.pattern #
    # + r")" #
    + r"[, ]{,3}"
    + r"[ )]*(?:at|um)?[ -]*"
    + RE_TIME_SIMPLE.pattern
    + r"?"  # Note: TIME_SIMPLE optional
    + r"(?:Uhr[ ]*)"
    + r"?"  # Note: UHR optional
    + RE_TIME_ADDONS.pattern
    + r"?"  # Note: TIME_ADDONS optional
    + r"[^\n\w()]*"
    ,flags=re.MULTILINE | re.IGNORECASE | re.VERBOSE
)

RE_ART_DATELINE_DATE_LOCATION: Pattern = re.compile(
    r"^"
    + r"(?P<datePNW>"
    + RE_DATE_EXACT.pattern
    + r"[^\w\n]*"
    + r")"
    + r"[ )]*(at|um)?[ ]*"
    + r"(?P<timesimplePtimeaddonsPNW>"
    + RE_TIME_SIMPLE.pattern
    + r"?"  # Note: TIME_SIMPLE optional
    + r"(?:Uhr[ ]*)"
    + r"?"  # Note: UHR optional
    + RE_TIME_ADDONS.pattern
    + r"?"  # Note: TIME_ADDONS optional
    + r"[^\w\n]*"
    + r")"
    + RE_POTENTIAL_GEO.pattern
    , flags=re.MULTILINE | re.IGNORECASE | re.VERBOSE
)

RE_DATE_TIME_ONLY_LINE: Pattern = re.compile(
    r"^"
    + RE_DATE_EXACT.pattern
    + r"[^\w\n]*"
    + r"[ )]*(at|um)?[ ]*"
    + RE_TIME_SIMPLE.pattern
    + r"?"  # Note: TIME_SIMPLE optional
    + r"(?:Uhr[ ]*)"
    + r"?"  # Note: UHR optional
    + r"[ ]*(uhr)?[ ]*"
    + RE_TIME_ADDONS.pattern
    + r"?"  # Note: TIME_ADDONS optional
    + r"[ .!?:]*$"
    , flags=re.MULTILINE | re.IGNORECASE | re.VERBOSE
)

RE_GEOLOCATION_AT_LINE_START: Pattern = re.compile(
    r"(?P<spaceorperiodbefore>(?<=\n\n)|(?<=\A)|(?<=" + sentence_end_chars_pattern + r"\n)|(?<=" + sentence_end_chars_pattern + r"[ ]\n))" +  # Note: Needs empty line/end of sent before
    r"^[ ]*" +
    RE_POTENTIAL_GEO.pattern +
    r"(?<=" +  # Note: Previous token WITHIN RE_POTENTIAL_GEO.pattern must be a seperator
    required_seperator_at_last_position_of_geo_pattern +
    r")",
    flags=re.IGNORECASE | re.MULTILINE
)

# Section ################################ CHARS ############################################

# Subsection ############################# MUST be clean: ########################################
RE_STRANGE_DASHES_UNICODE: Pattern = re.compile(r"([\u2010\u2011\u2012\u2013\u2014\u2015\uFF0D\uFE63\u2043\u1680\u002D\u2043\u1806\u2212])")
RE_STRANGE_BLANKS_UNICODE: Pattern = re.compile(r"([\u00A0])")

# Subsection ############################# CAN be cleaned: ########################################
RE_BULLET_POINTS: Pattern = re.compile(
    r"([\u2022\u2023\u2043\u204C\u204D\u2219\u25aa\u25CF\u25E6\u29BE\u29BF\u30fb\u25ba])")
RE_LETTER_LISTING_STARTS: Pattern = re.compile(r"\((?:i+|a+)\)")
RE_NUMBER_LISTING_STARTS: Pattern = re.compile(
    r"(?mi:(?<=\n)^\d[/.][ ]?(?!\d|" + month_name + r")(?=\w))")  # Note: MULTILINE flag set in pattern
RE_LIST_CHARS_AT_LINE_START: Pattern = re.compile(
    # Note: Requires bullet points as first non-whitespace char on a new line
    r"(?:(?<=\n)|(?<=^))[ ]*?"
    + r"(?:"
    + RE_BULLET_POINTS.pattern
    + r'|'
    + RE_NUMBER_LISTING_STARTS.pattern
    + r'|'
    + RE_LETTER_LISTING_STARTS.pattern
    + r")"
)

RE_SUSPICIOUS_CHARS: Pattern = re.compile(r"[\\#<>+|~^°=]+")
RE_SUSPICIOUS_CHARS_IN_COMP_NAMES: Pattern = re.compile(r"[,()]+")
RE_UNICODE_SYMBOLS: Pattern = re.compile(r"([\u00ab\u00BB\u00AE\u2310\u2500\u2026\u300C\u300D])")
RE_SUPER_SUB_SCRIPTED_NUMBERS_AND_SYMBOLS: Pattern = re.compile(
    r"([\u2070\u00B9\u00B2\u00B3\u2074\u2075\u2076\u2077\u2078\u2079\u2080\u2081\u2082\u2083\u2084\u2085\u2086\u2087\u2088\u2089\u2122])")

RE_GERMAN_GENDER_MARKS: Pattern = re.compile(
    r"(?<=(\wd|\wt|(?P<addnosuffixif>er)|\wr))[/]?[*_:](?:(?P<plural>inn)|(?P<singular>in))(?(addnosuffixif)en|)?")

RE_REPEATING_CHARS: Pattern = re.compile(
    fr"{negative_lookbehinds_no_words_with_dot_at_end}(?P<chars>[{repeat_chars}])(?P<repeatchar>\s*(?(chars)[{repeat_chars}])){{1,}}", flags=re.MULTILINE | re.IGNORECASE)

RE_HYPHEN_CHARS: Pattern = re.compile(pattern=r"(?:(?<=\A)|(?<=\s))" +
                                              hyphen_char_pattern +
                                              r"(?=\s)")
RE_FINAL_CLEANUP_CHARS: Pattern = re.compile(r"[()/*]+")

# Subsection ############################### Quotation marks ############################
RE_QUOTATION_MARKS: Pattern = re.compile(r"\'(?!s)|\"")

# Subsection ################################ EMOJIS ####################################
RE_EMOJI: Pattern = re.compile(
    r"[\u2600-\u26FF\u2700-\u27BF\U0001F300-\U0001F5FF\U0001F600-\U0001F64F\U0001F680-\U0001F6FF\U0001F900-\U0001F9FF\U0001FA70-\U0001FAFF]",
    flags=re.IGNORECASE,
)

# Subsection ############################### MEASUREMENTS, UNITS, IDENTIFIERS ########################


RE_CURR_SYMBOL: Pattern = re.compile(r"[$¢£¤¥ƒ֏؋৲৳૱௹฿៛ℳ元円圆圓﷼\u20A0-\u20C0]")
RE_CURR_AMOUNT: Pattern = re.compile(
    r"(?P<curr>EUR|USD|GBP|JPY)(?:[ ]*)(?P<amount>\b[\,\.\d]+)[ ]?(?P<unit>[A-ZÄÖÜa-zäöü]{1,5}\b[.]?)(?=\W)",
    flags=re.IGNORECASE)
RE_ISIN: Pattern = re.compile(r"(?-i:(?P<ISIN>(?<!\w|\d)[A-Z]{2}[A-Z\d]{9}\d(?!\w|\d)))")

RE_MEASUREMENT_NO_SPACE_UNIT: Pattern = re.compile(rf"(?P<amount>\d+)(?P<unit>{measurement_pattern}(?:2|3)?)(?!\w)",
                                                   flags=re.IGNORECASE)

# Subsection ################################ LOWER, UPPER, CAPITAl CASES #################################

RE_CAPITAL_LETTER_ONLY_LINES: Pattern = re.compile(
    r"(?-i:(?:^(?:(?:(?:\b(?:[A-ZÄÖÜ]|(Ae|Oe|Ue))+\b)[^a-zäöü\n]*){2,}(?:\n|$))+)$)", flags=re.MULTILINE)

RE_E_UMLAUT_CONVERSION_IN_CAPITAL_WORD: Pattern = re.compile(r"\b[A-ZÄÖÜ]+(?:A|O|U)(?P<lowere>e)[A-ZÄÖÜ]+\b")

# Section ################################ PERSONAL INFORMATION, INTERNET, EMAIL, PHONE #########################################
# Note: NEW:
RE_NAME_INITIALS_IN_COMPANY_NAME: Pattern = re.compile(r"^\s*[A-ZÄÖÜ]\.[A-ZÄÖÜ]\.\s*$")

RE_URL: Pattern = re.compile(
    r"(?:^|(?<![\w/.]))"
    # protocol identifier
    # r"(?:(?:https?|ftp)://)"  <-- alt?
    r"(?:(?:https?://|ftp://|www\d{0,3}\.))"
    # user:pass authentication
    r"(?:\S+(?::\S*)?@)?"
    r"(?:"
    # IP address exclusion
    # private & local networks
    r"(?!(?:10|127)(?:\.\d{1,3}){3})"
    r"(?!(?:169\.254|192\.168)(?:\.\d{1,3}){2})"
    r"(?!172\.(?:1[6-9]|2\d|3[0-1])(?:\.\d{1,3}){2})"
    # IP address dotted notation octets
    # excludes loopback network 0.0.0.0
    # excludes reserved space >= 224.0.0.0
    # excludes network & broadcast addresses
    # (first & last IP address of each class)
    r"(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])"
    r"(?:\.(?:1?\d{1,2}|2[0-4]\d|25[0-5])){2}"
    r"(?:\.(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-4]))"
    r"|"
    # host name
    r"(?:(?:[a-z\u00a1-\uffff0-9]-?)*[a-z\u00a1-\uffff0-9])"
    # domain name
    r"(?:\.(?:[a-z\u00a1-\uffff0-9]-?)*[a-z\u00a1-\uffff0-9])*"
    # TLD identifier
    r"(?:\.(?:[a-z\u00a1-\uffff]{2,}))"
    r")"
    # port number
    r"(?::\d{2,5})?"
    # resource path
    r"(?:/\S*)?"
    r"(?:$|(?![\w?!+&/]))",
    flags=re.IGNORECASE,
)

RE_URL_NEW: Pattern = re.compile(r"(?P<before>(?<=\W))"
                                 r"(?P<http>https?://)?(?(http)(?:www\.)?|(?:www\.))"
                                 r"(?P<domain>\.?\w+)+"
                                 r"(?:\.(?P<endings>/?(?:"
                                 + www_domain_pattern +
                                 r"))+"
                                 r"(?P<slash>/)?)"
                                 r"(?(slash)(?P<resources>(?:[\w/.:&%?=-]+\n?))+|(?P<after>/|(?=$|\s|\W)))", flags=re.MULTILINE | re.IGNORECASE)

RE_SHORT_URL: Pattern = re.compile(
    r"(?:^|(?<![\w/.]))"
    # optional scheme
    r"(?:(?:https?://)?)"
    # domain
    r"(?:\w-?)*?\w+(?:\.[a-z]{2,12}){1,3}"
    r"/"
    # hash
    r"[^\s.,?!'\"|+]{2,12}"
    r"(?:$|(?![\w?!+&/]))",
    flags=re.IGNORECASE,
)

RE_URL_DOMAIN: Pattern = re.compile(
    r"(?P<https>\bhttps?://)?(?P<www>(?:www|\w+)\.)?(?P<domain>(?:\w|-)+)(?P<ending>\.(?:" + www_domain_pattern + r")/?)",
    flags=re.IGNORECASE)

RE_HTTP_LINKS: Pattern = re.compile(
    r"(?P<beforelinks>(?:Link|Bildlink|Quellen):\s*)" + r"?"  # Optional
    + RE_URL_NEW.pattern
    , flags=re.IGNORECASE | re.MULTILINE)

RE_EMAIL: Pattern = re.compile(
    r"(?:mailto:)?"
    r"(?:^|(?<=[^\w@.)]))([\w+-](\.(?!\.))?)*?[\w+-]@(?:\w-?)*?\w+(\.([a-z]{2,})){1,3}"
    r"(?:$|(?=\b))",
    flags=re.IGNORECASE,
)

RE_PHONE_NUMBER: Pattern = re.compile("(%s|%s)" % (
    # Note: Intl.
    r"(?:\+(?:1|44|90)[\-\s]+[0-9]{3}([\-\s0-9]{4,11}(?:$|\s)))|(?:\+[0-9]{2,3}[\-\s]+\(?[0-9]{2,5}\)?[\/\-\s0-9]{4,11}(?:$|\s))",
    # Note: National
    r"(?P<nat1>0|\+)?(?(nat1)[0-9]{2,5}|\(0?[0-9]{2,5}\))[\s\-\/]([\-\s\d]{3,11})($|\s+)"),
                                      flags=re.IGNORECASE)

# Section ################################  Abbreviations, Repetitions  ################################
RE_NAME_INITIALS_BLOCK: Pattern = re.compile(
    r"(?:(?<=^)|(?<=\W))(?!\b(?:"
    + www_domain_pattern +
    r")\b)(?P<firstslash>/)?[^\d\W]{2,4}/[^\d\W]{2,4}(?(firstslash)/?|/)(?:(?<=/)(?:[^\d\W]{2,4})/?)*",
    flags=re.IGNORECASE)

RE_REPEATING_WORDS_AT_BEGINNING: Pattern = re.compile(
    r"(?:(?P<repetition>\A(?P<repeatchars>.{3,1000}\b)).{,3}(?P=repeatchars))",
    flags=re.MULTILINE | re.DOTALL)

RE_DUPLICATE_SENTENCES: Pattern = re.compile(
    r"(?P<start>\A|^)(?P<first>^\b.+?\b)(?P<firstend>[ ]*)(?:(?P<emptylines>\s*)(?P<last>\b(?P=first)\b))+",
    flags=re.MULTILINE | re.IGNORECASE | re.DOTALL)

# Section ###############################  BEGINNINGS, ENDINGS  ##############################################
RE_NON_WORDS_AT_TEXT_START: Pattern = re.compile(r"\A\W+")

# Note: ?im -> re.I and re.M
RE_UEBER_ABOUT: Pattern = re.compile(
    r"(?:^(About|Unternehmensprofil|(Ü|Ue)ber|Zu)\s+(der|die|das)?\s*(?P<companyname>(\b\w+\b[&+., -]*){1,5})(?P<suffixes>\b(?:" + company_suffixes + r")\b[ ]?)*[ .:]*$\n+[\w, ]{,50}\b(?P=companyname))",
    flags=re.IGNORECASE)

RE_UEBER_ABOUT_WWW: Pattern = re.compile(
    r"(?:^(About|Unternehmensprofil|(Ü|Ue)ber|Zu)\s+(der|die|das)?\s*(?P<compname>(\b\w+\b[&+., -]*){1,5})(?P<www>[^\n\w]*(www\.)?(?P=compname)\.(" + www_domain_pattern + r")):?$)")

# Section ################################ WEBSITE SPECIFIC PATTERNS #########################################

# Subsection ################################ EQS ###########################################
# Note: REMOVE BEFORE PREFIX:
# Note: Flags DOTALL, IGNORCASE are set in general. (?-is:...) must be set to revert these flags.
prefix_list_eqs: list = [r"^Schlagwort\(e\):?\s*\w*$",
                         RE_CAPITAL_LETTER_ONLY_LINES.pattern,
                         # rf"^(ISIN:?)?[ ]*{RE_ISIN.pattern}[ ]*$", Note: THIS is a problem !!!
                         r"^Pressemitteilung:?\s*$",
                         r"^Medienmitteilung:?\s*$",
                         r"^Corporate\sNews:?\s*$",
                         r"^Ad[ -]hoc[ -](Mitteilung|announcement)\s(gem(ä|ae)ss|pursuant\sto)\s(Art\.|§§*)\s\d{1,3}[^\n]*$",
                         r"^Disclosure\sof\s[^\n]{1,30}according\sto[^\n]{1,100}$"
                         ]

prefixes_eqs = '|'.join([prefix.replace('.*', '').replace('{', '{{').replace('}', '}}') for prefix in
                         prefix_list_eqs])  # Note: MUST NOT CONTAIN '.*' or single curly brackets !
TO_FORMAT_RE_EQS_PREFIXES_AND_BEFORE: str = r"\A.{{0,{max_prefix_chars}}}(?P<terms>(?:" + prefixes_eqs + r")\W*$)"

# Note: REMOVE:
RE_EQS_PIC_TITLES: Pattern = re.compile(r"(?P<pictitle>(Bildtitel|Bild\s\d\d?|Foto-Download):[^\n]*$)",
                                        flags=re.IGNORECASE | re.MULTILINE)
RE_EQS_REPORTING_NUMBERS: Pattern = re.compile(
    r"(?P<firstrow>^(Verw(ae|ä)ssertes\sund\sunverw(ae|ä)ssertes\s)?(?P<nonoptional>Kennzahlen(?:[ ]im[ ](?:ue|ü)berblick[:]?)?$|Ver(ä|ae)nderung:?$|Ebit|Konzernergebnis|Ergebnis:?$|Ergebnis\s(?:(nach|vor)\sSteuern|je\sAktie)|Umsatz|Gearing\sRatio|(Material|Personal)aufwand|Free[ ]Cashflow|Abschreibungen(?:[ ])und[ ]Wertminderungen|Sonstige[ ]betriebliche)[^\n]{,177}$)(?P<numberrows>\n([.,%\u2212\u00A0\u2013 +-]|\d+|n\.a\.){1,25}$)+",
    flags=re.IGNORECASE | re.MULTILINE)
RE_EQS_DISCLOSURES: Pattern = re.compile(
    r"(?P<disclosure>^"
    + r"(?P<start>.{,60}"
    + r"(?:Ver(?:ö|oe)ffentlichung|MEDIENMITTEILUNG)[ ]+)"
    + r"(?P<middle>[^\n]+\n?[^\n]*)"
    + r"(?P<end>"
    + r"(?:europaweiten[ ]+Verbreitung)"
    + r"|"
    + r"(?:Gesamtzahl[ ]+der[ ]+Stimmrechte)"
    + r"|"
    + r"(?:Service[ ]+der[ ]+EQS[ ]+Group[ ]+AG)"
    + r"|"
    + r"(?:gem(?:ae|ä)(?:ß|ss)[ ]Art(ikel)?\.?[ ]\d+[^\n]{,50})"
    + r")"
    + r"[ .:]*$)",
    flags=re.IGNORECASE | re.MULTILINE
)

RE_EQS_HOLLOW_PHRASES: Pattern = re.compile(
    r"(?P<hollowphrases>^(?:"
    r"(?:IR-Mitteilung)"
    r"|"
    r"(?:(?:(?:EQS-News|EQS-Ad-hoc):)?[^\n]+Schlagwort[^\n]+)"
    r"|"
    r"(?:\W*PRESSEMITTEILUNG\W*)"
    r"|"
    r"(?:<?Ende[ ]+der[ ]+Mitteilung>?)"
    r")"
    r"[ .:]*$)"
    ,
    flags=re.MULTILINE | re.IGNORECASE
)

# Note: REMOVE AFTER SUFFIX:
suffix_list_eqs: list = [RE_UEBER_ABOUT.pattern,
                         RE_UEBER_ABOUT_WWW.pattern,
                         RE_NAME_INITIALS_BLOCK.pattern,
                         r"^Disclaimer:?\s*$",
                         r"^Medienkontakte?:?\s*$",
                         r"^Risikohinweis:?\s*$",
                         r'^For\sfurther\sinformation:?\s*$',
                         r'^Ansprechpartner(?:\sf(ü|ue)r\sMedien)?:?$',
                         r"^Ansprechpartner\sf(ü|ue)r\s(Presse|Investoren)([-]*\sund\s(Investoren|Presse))?anfragen:?[ ]*$",
                         r"^F(ü|ue)r\s(?:weitere\sInformationen|Rückfragen)(\swenden\sSie\ssich\sbitte\san)?:?\s*$",
                         r"^[\w ]{,30}Presse\s?kontakt:?\s*$",
                         r"^Contacts:?\s*$",
                         r'^Weitere\sInformationen\s(unter|erhalten\sSie\s(bei|hier)):?\s*$',
                         r"^Kontakte?(?:(?:daten)?(\sf(ue|ü)r\s(?:Investoren(?:\sund\sAnalysten)?|Analysten(?:\sund\sInvestoren)?|(?:die\s)?Medien)?)?)?:?(?=$)",
                         r"^Rechtlicher\sHinweis:?\s*$",
                         r"^(Presse|Medien)mitteilung\s(als\s)?\(?PDF\)?:?\s*$",
                         r"^Weitere\sInformation(en)?:?\s*$",
                         r"^Forward[-\s]looking\sstatements?\s*$",
                         r"^[^\n]{,30}media\scontact:?\s*$",
                         r'^Contact:?\s*$',
                         r"^Bei\sR(ü|ue)ckfragen(\swenden\sSie\ssich\sbitte\san):?\s*$",
                         r"^Alle\sInformationen\szu(.{,40}?)finden\ssie\shier:?\s*$",
                         r"^Ansprechpartner\sf(ü|ue)r\sRückfragen:?\s*$",
                         r"^Pressekontakt(\sund\sInvestor\sRelations):?\s*$",
                         r"^To\scontact\sus:?\s*$",
                         r"^Zukunftsgerichtete\sAussagen\sund\sPrognosen:?\s*$",
                         r"^For\s(further|more)\sinformation,?\splease\scontact\s*\w*:?\s*$",
                         r"^For\sinquiries,\splease\scontact:?\s*$",
                         r"^Company\sInformation:?\s*$",
                         r"^The\sissuer\sis\s(solely\s)?responsible\sfor\sthe\scontent\sof\sthis\s\w+[.:]?\s*$"
                         ]

suffixes_eqs: str = '|'.join([suffix.replace('.*', '').replace('{', '{{').replace('}', '}}') for suffix in
                              suffix_list_eqs])  # Note: MUST NOT CONTAIN '.*' or single curly brackets !
TO_FORMAT_RE_EQS_SUFFIXES_AND_AFTER: str = r"(?P<terms>(?:" + suffixes_eqs + r")).{{0,{max_suffix_chars}}}\Z"

# Subsection ################################ REUTERS #############################################
# Note: NEEDED FOR SCRAPING:
RE_REUTERS_DEPLOYMENT_NR: Pattern = re.compile(r"(?<=Fusion\.deployment=\")(?P<deploymentnumber>\d+)(?=\")",
                                               flags=re.IGNORECASE)
RE_REUTERS_URL_DOMAIN_AND_SECTION: Pattern = re.compile(
    r"\b(?P<domainandsector>https://www\.reuters\.com/\w*/?)(?=(\w*|/)*)",
    flags=re.IGNORECASE)

# Note: PREFIXES:
RE_REUTERS_PREFIX: Pattern = re.compile(r"\(reuters\)[\s-]*", flags=re.IGNORECASE)

# Subsection ################################ DPA #######################################
# Note: REMOVE BEFORE PREFIX:
prefix_list_dpa: list = [r"^IRW-Press[:/\s]+",
                         r"\(dpa-AFX\)",
                         r"^Schlagwort\(e\):*\s*\w*",
                         r"^Dr\.\s+Reuter\s+Investor\s+Relations[\s:-]*",
                         r"^\(dpa-AFX Broker\)",
                         r"^\(GLOBE NEWSWIRE\)",
                         r"^Original-Research:"
                         ]

prefixes_dpa = '|'.join([prefix.replace('.*', '').replace('{', '{{').replace('}', '}}') for prefix in
                         prefix_list_dpa])  # Note: MUST NOT CONTAIN '.*' or single curly brackets !
TO_FORMAT_RE_DPA_PREFIXES_AND_BEFORE: str = r"\A.{{0,{max_prefix_chars}}}(?P<terms>(?:" + prefixes_dpa + r")\W*$)"

# Note: REMOVE:
RE_DPA_PIC_TITLES: Pattern = re.compile(r"(?P<pictitle>Bildtitel:[^\n]*$)",
                                        flags=re.IGNORECASE | re.MULTILINE)

RE_DPA_DISCLAIMERS: Pattern = re.compile(r"(?P<disclaim>^"
                                         + r"(?:F[üue]{1,2}r[ ]*den[ ]*Inhalt[^\n]*verantwortlich)"
                                         + r"[ .:]*$)",
                                         flags=re.IGNORECASE | re.MULTILINE)

RE_DPA_DISCLOSURES: Pattern = re.compile(
    r"(?P<disclosure>^"
    + r"(?P<start>.{,60}"
    + r"(?:Ver(?:ö|oe)ffentlichung|MEDIENMITTEILUNG)[ ]+)"
    + r"(?P<middle>[^\n]+\n?[^\n]*)"
    + r"(?P<end>"
    + r"(?:europaweiten[ ]+Verbreitung)"
    + r"|"
    + r"(?:Gesamtzahl[ ]+der[ ]+Stimmrechte)"
    + r"|"
    + r"(?:Service[ ]+der[ ]+EQS[ ]+Group[ ]+AG)"
    + r"|"
    + r"(?:gem(?:ae|ä)(?:ß|ss)[ ]Art\.?[ ]\d+[ ]\w+\b\.?)"
    + r")"
    + r"[ .:]*$)",
    flags=re.IGNORECASE | re.MULTILINE
)

RE_DPA_AGENCY_NAMES: Pattern = re.compile(r"(?:^|\W)[ ]*IRW-Press[ ]*[:/][ ]*",
                                          flags=re.IGNORECASE)

RE_DPA_HOLLOW_PHRASES: Pattern = re.compile(
    r"(?P<hollowphrases>^(?:"
    r"(?:IR-Mitteilung)"
    r"|"
    r"(?:(?:(?:EQS-News|EQS-Ad-hoc):)?[^\n]+Schlagwort[^\n]+)"
    r"|"
     r"(?:PRESSEMITTEILUNG)"
    r")"
    r"[ .:]*$)",
    flags=re.MULTILINE | re.IGNORECASE
)

RE_DPA_DOUBLE_COMPANY_MENTIONS: Pattern = re.compile(
    r"^(?P<prewords>\w+[ .:-]*){,3}?(?P<companyname>(\b\w+\b[&+., -]*){1,5})(?P<suffixes>\b(?i:" + company_suffixes + r")\b)*:[ ]*\b(?P<repetition>(?P=companyname))",
    flags=re.IGNORECASE)

# ToDo: Move from BEFORE PREFIX to REMOVE (Middle of sentence)

# Note: REMOVE AFTER SUFFIX: DO NOT USE ".*"
suffix_list_dpa: list = [r"^Disclaimer[:/]",
                         RE_NAME_INITIALS_BLOCK.pattern,
                         RE_UEBER_ABOUT.pattern,
                         r"^Medienkontakt[:]*",
                         r"^Risikohinweis:\s*$",
                         r"^N[äae]{1,2}here\s+Informationen\s+erhalten\s+Sie\s+[üue]{1,2}ber\s*:",
                         r"^F(?:ue|ü)r[ ]+weitere[ ]+Informationen(?:[^\n]*)wenden[ ]+Sie[ ]+sich[ ]+bitte[ ]+an\W$",
                         r"^Informationen\s+und\s+Erl[äae]{1,2}uterungen\s+des\s+Emittenten\s+zu\s+dieser\s+Mitteilung\s*:",
                         r"^Weitere\s*Informationen\s*(?:(?:[uü]|ue)ber[\w\s-][^\n]*)*finden\s*Sie\s*unter",
                         r"^ANSPRECHPARTNER\s+F[ÜUE]{1,2}R\s+(MEDIEN|INVESTOR\*INNEN\s+UND\s+ANALYST\*INNEN)",
                         r"^Anfragen\s*f[üue]{1,2}r\s*Medien\s*und\s*Investor\s*Relations",
                         r"^(Presse|Investoren)?kontakt:?",
                         r"^Contacts:",
                         r"^Kontakt\s*f[üue]{1,2}r\s*R[üue]{1,2}ckfragen",
                         r"^Ver[öoe]{1,2}ffentlichung\s*einer\s*Corporate\s*News\/Finanznachricht\,\s*[üue]{1,2}bermittelt\s*durch\s*EQS",
                         r"^Haftungsausschluss\s*f[üue]{1,2}r\s*zukunftsgerichtete\s*Informationen",
                         r"^F[üue]{1,2}r\s*weitere\s*Informationen\s*besuchen\s*Sie\s*bitte",
                         r"^Zus[äae]{1,2}tzliche\s*Informationen\s*erhalten\s*Sie\s*[üue]{1,2}ber:",
                         r"^Ende[ ]+der[ ]+Mitteilung.{,25}$"]

suffixes_dpa: str = '|'.join([suffix.replace('.*', '').replace('{', '{{').replace('}', '}}') for suffix in
                              suffix_list_dpa])  # Note: MUST NOT CONTAIN '.*' or single curly brackets !
TO_FORMAT_RE_DPA_SUFFIXES_AND_AFTER: str = r"(?P<terms>(?:" + suffixes_dpa + r")).{{0,{max_suffix_chars}}}\Z"

if __name__ == '__main__':
    print(make_pattern_from_raw_str_iterable(raw_str_iterable=abbrevs_and_company_suffixes_with_dot_at_end, as_group=True))
    # print(RE_COMPANY_NAME_SPLIT_TO_NAME_AND_LEGAL.pattern)
    # d = {',': '', 'I': '', 'had': 'have', 'a': '', 'in': '', 'Berlin': ''}
    # print(make_pattern_from_raw_str_iterable(raw_str_iterable=d))
    # print(RE_ART_DATELINE_LOCATION_DATE.pattern)
    # print(RE_REPEATING_WORDS_AT_BEGINNING.pattern)
    # print(TO_FORMAT_RE_HEADLINE.format(max_chars_short_sents=6, max_chars_short_sents_plus_one=7))
    # print(RE_DPA_REM_BEFORE_PREFIXES.pattern)
    # print(TO_FORMAT_RE_HEADLINE.format(max_chars_short_sents=100, max_chars_short_sents_plus_one=101))
    # print(RE_SENT_END_EXCLUDING_WORDS_WITH_DOT.pattern)
    # print(RE_REPEATING_CHARS.pattern)
    # print(TO_FORMAT_RE_DPA_SUFFIXES_AND_AFTER)
    # print(RE_DPA_PIC_TITLES.pattern)
    # print(TO_FORMAT_RE_TOO_EARLY_LINEBREAK)
    # print(TO_FORMAT_RE_SECTION_HEADER)
    # print(TO_FORMAT_RE_DPA_PREFIXES_AND_BEFORE)
    # print(RE_DPA_REM_AFTER_SUFFIXES.pattern)
    # print(RE_EMAIL.pattern)
    # print(RE_URL.pattern)
    # print(RE_DATE_TIMEOPTIONAL_ONLY_LINES.pattern)
    # print(RE_ALL_SECTIONS_IN_TEXT.pattern)
    # print(RE_GEOLOCATION_AT_LINE_START.pattern)
    # print(RE_DATE_TIME_ONLY_LINES.pattern)
    # print(RE_DATE_AND_TIME.pattern)
    # print(RE_DATE_EXACT.pattern)
    # print(RE_REUTERS_REMOVE_PREFIX_IN_TEXT.pattern)
    # print(RE_TIME.pattern)
    # print(RE_DATE_2_MONTHNAME_DAY_YEAR.pattern)
    # comb = combine_patterns(compiled_one=RE_DATE_EXACT, compiled_two='\.').pattern
    # print(comb)
