from typing import Optional
from pydantic import BaseModel, Field
from dataclasses import dataclass, asdict

from src.settings.enums import SpacyComp, IDXReferTo


class Coreference(BaseModel):
    """ Coreferences occur when one or more expressions or mentions in a text refer to a company name at another position in that text.
    For example: In the text 'Steve Jobs founded Apple. The company was very successful. Today it is a media company.' the mention 'company' in the second sentence and the mention 'it' in the third sentence are coreferences to the company name 'Apple'.
    The 'coref_text'-attribute is the substring of the found coreference within the text string.
    The 'coref_with_surrounding'-attribute is the coreference substring plus its surrounding characters to the left and right that can include up to two words on each side. """
    coref_text: Optional[str] = Field(default=None, description='The coreference substring in the text string')
    coref_with_surroundings: Optional[str] = Field(default=None, description='The coreference substring plus its characters to the left and right in the text string up to two words on each side.')


class ClusterHead(BaseModel):
    """ The cluster head is the anchor text of a coreference cluster to which coreferences refer.
    The cluster head always is the name of a company which is provided in the user message.
    The 'head_index_start'- and the 'head_index_end'-attributes are integer values that mark the start and end position of the cluster head substring within the text."""
    head_text: Optional[str] = Field(default=None, description='The string characters of the cluster head which is a company name')
    head_index_start: Optional[int] = Field(default=None, description='The position index of the first character of the cluster head substring')
    head_index_end: Optional[int] = Field(default=None, description='The position index of the last character of the cluster head substring plus one')


class Cluster(BaseModel):
    """ A coreference cluster consists of one cluster head in a text and one or more coreferences at another position in that text that co-refer to this cluster head.
        For example: In the text 'Steve Jobs founded Apple. The company was very successful. Today it is a media company.' the coreference 'company' in the second sentence and the coreference 'it' in the third sentence co-refer to the cluster head which is 'Apple'.
    """
    cluster_id: Optional[int] = Field(default=None, description='The identification number of the cluster provided by the user. Always return the same number that was provided by the user.')
    text: Optional[str] = Field(default=None, description='The text to search in')
    cluster_head: Optional[ClusterHead] = Field(default=None, description='The cluster object which is is provided in the user message')
    coreferences: Optional[list[Coreference]] = None


class DataContainer(BaseModel):
    data_list: list[Cluster] | None = None

    # __hash__ = object.__hash__


@dataclass
class SearchMatch:
    comp_name: str
    comp_symbol: str
    text: str
    label: str
    start_idx: int
    end_idx: int
    idx_refer_to: IDXReferTo

    def __eq__(self, other):
        return self.start_idx == other.start_idx

    def __hash__(self):
        return hash(self.start_idx)

    def __lt__(self, other):
        return self.start_idx < other.start_idx


@dataclass
class EntsWithCustExts:
    start_char: int
    end_char: int
    ent_text: str
    comp_name: str
    comp_symbol: str
    set_in: SpacyComp
    df_index: int | None = None

    def __eq__(self, other):
        return (self.comp_name, self.comp_symbol) == (other.comp_name, other.comp_symbol)

    def __hash__(self):
        return hash((self.comp_name, self.comp_symbol))


if __name__ == '__main__':
    e1 = EntsWithCustExts(start_char=1, end_char=4, ent_text= 'text', comp_name='Apple', comp_symbol='peach', set_in=SpacyComp.SENTER)
    e2 = EntsWithCustExts(start_char=1, end_char=3, ent_text= 'text', comp_name='Apple', comp_symbol='peach', set_in=SpacyComp.SENTER)
    print(e1 == e2)
    s = set()
    s.add(e1)
    s.add(e2)
    print('set:', s)
    print('-------------------')
    print(asdict(e1))
