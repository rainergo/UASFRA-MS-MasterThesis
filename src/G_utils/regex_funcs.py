import re

from src.G_utils import re_patterns as repat

# Note: Umlaute must be case sensitive, so this here differs from A_NLP:
TBL_UMLAUTE: dict = {'ä': 'ae', 'Ä': 'AE', 'ö': 'oe', 'Ö': 'OE', 'ü': 'ue', 'Ü': 'UE', 'ß': 'ss'}
TBL_ACCENTS: dict = {'à': 'a', 'á': 'a', 'â': 'a', 'ã': 'a', 'å': 'a', 'ạ': 'a', 'ẵ': 'a', 'ā': 'a',
                     'À': 'A', 'Á': 'A', 'Â': 'A', 'Å': 'A',
                     'ç': 'c', 'Ç': 'C', 'Č': 'C', 'č': 'c',
                     'Đ': 'D',
                     'è': 'e', 'é': 'e', 'ê': 'e', 'ë': 'e', 'ȩ': 'e', 'ě': 'e', 'ệ': 'e',
                     'È': 'E', 'É': 'E', 'Ê': 'E', 'Ë': 'E',
                     'ì': 'i', 'í': 'i', 'î': 'i', 'ï': 'i', 'Î': 'I', 'Ï': 'I', 'Í': 'I', 'İ': 'I',
                     'Ł': 'L',
                     'ñ': 'n',
                     'ò': 'o', 'ó': 'o', 'ô': 'o', 'õ': 'o', 'ō': 'o', 'ồ': 'o', 'ớ': 'o',
                     'Ô': 'O', 'Ò': 'O', 'Ó': 'O', 'Ō': 'O',
                     'Ś': 'S', 'Ş': 'S', 'Š': 'S',
                     'ù': 'u', 'ú': 'u', 'û': 'u', 'ủ': 'u', 'ū': 'u', 'Ù': 'U', 'Û': 'U', 'Ú': 'U',
                     'Ż': 'Z', 'Ž': 'Z'}
TBL_FANCY_QUOTATION_MARKS: dict[int, int] = {
        ord(x): ord(y) for x, y in
        [("ʼ", "'"), ("‘", "'"), ("ʿ", "'"), ("’", "'"), ("´", "'"), ("`", "'"), ("“", '"'), ("”", '"'), ("„", "'"),
         ("‚", "'")]}


def sub_umlaute(text: str) -> str:
    """ Substitutes German umlaute """
    try:
        table = str.maketrans(TBL_UMLAUTE)
        text = text.translate(table)
        # Note: The umlaut conversion inserts an 'e' which must be corrected if the word is all capital letters:
        text = repat.RE_E_UMLAUT_CONVERSION_IN_CAPITAL_WORD.sub(repl=lambda m: m.group(0).replace(m.group('lowere'),
                                                                                                  'E'), string=text)
        return text
    except:
        print(f"sub_umlaute not working.")


def sub_accent_chars(text: str) -> str:
    try:
        """ Substitutes accented characters with their root character (i.e.: 'ê' -> 'e') """
        table = str.maketrans(TBL_ACCENTS)
        return text.translate(table)
    except:
        print(f"sub_accent_chars not working.")


def sub_fancy_quot_marks(text: str) -> str:
    """ Substitutes non-normal quotation marks with normal double-dash quotation marks (i.e.: '‘' -> '"') """
    try:
        table = str.maketrans(TBL_FANCY_QUOTATION_MARKS)
        return text.translate(table)
    except:
        logger.error(f"sub_fancy_quot_marks not working.")


# Note: NEW
def sub_suspicious_chars_in_comp_names(text: str) -> str:
    text = repat.RE_SUSPICIOUS_CHARS_IN_COMP_NAMES.sub(repl="", string=text)    # Only comma, so far. Do not erase "." as it appears in web.com
    return text


def clean_accents_and_umlaute(text: str) -> str:
    text = sub_umlaute(text)
    text = sub_accent_chars(text)
    text = sub_suspicious_chars_in_comp_names(text)
    return text


def check_if_name_initials_in_substring(text: str) -> bool:
    match = repat.RE_NAME_INITIALS_IN_COMPANY_NAME.search(string=text)
    return match is not None


def split_company_name_to_name_and_legal(company_name: str) -> tuple[str, str]:
    name, legal = None, None
    match = repat.RE_COMPANY_NAME_SPLIT_TO_NAME_AND_LEGAL.search(string=company_name)
    if match is not None:
        # print(match.groups())
        if match.group('name'):
            name = match.group('name')
        else:
            name = match.group('name2')
        # if (isinstance(name, str)) and name.isnumeric():
        #     name = company_name
        legal = match.group('legal') if match.group('legal') else legal
    # print(f'text: {company_name} --- name: {name} --- name: {match.group("name")} --- legal: {match.group("legal")} --- name2: {match.group("name2")}')
    # print('--------------------------------------')
    return name, legal


def split_name(name: str) -> list[str] | None:
    if name:
        str_pat = r'(?<=\w{2})(?!\.com|\.de|\.org|\.fr|\.co\.uk|\.int|\.net|\.edu|\.gov)([^\w\.])(?=\w{1,}|[ ])'
        pattern = re.compile(pattern=str_pat, flags=re.IGNORECASE)
        list_with_all_separators = pattern.split(string=name)
        list_with_separators_but_without_space = ' '.join(list_with_all_separators).split()
        return list_with_separators_but_without_space
    else:
        return None


if __name__ == '__main__':
    # t = " A.S. "
    # print(check_if_name_initials_in_substring(t))
    cn = 'N.V.'
    n, l = split_company_name_to_name_and_legal(company_name=cn)
    print('name and legal:', (n, l))
    # n = "450 Plc"
    # split_name = split_company_name_to_name_and_legal(company_name=n)
    # print('split_name:', split_name)