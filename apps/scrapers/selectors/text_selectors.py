# This file will contain selectors for text manipulation

from .base import Selector, Selected, SelectedType
from bs4 import BeautifulSoup

# A TextSelector takes a Selected Single and returns the text value within it.
class TextSelector(Selector):
    def __init__(self):
        self.expected_selected = SelectedType.SINGLE

    def select(self, selected):
        super().select(selected)
        return Selected(str(selected.value.get_text()).strip(), SelectedType.VALUE)

    def toYamlDict(self):
        return 'text_selector'

    def fromYamlDict(yamlDict):
        return TextSelector()

# An HTMLSelector takes a Selected Single and returns the whole html value within it.
class HtmlSelector(Selector):
    def __init__(self):
        self.expected_selected = SelectedType.SINGLE

    def select(self, selected):
        super().select(selected)

        return Selected(str(selected.value.prettify()).strip(), SelectedType.VALUE)

    def toYamlDict(self):
        return 'html_selector'

    def fromYamlDict(yamlDict):
        return HtmlSelector()

# A PlainTextSelector is initialized with a string and returns that string as a Selected Value no matter what selected is passed in.
class PlainTextSelector(Selector):
    def __init__(self, text):
        self.text = text

    def select(self, selected):
        return Selected(self.text, SelectedType.VALUE)

    def toYamlDict(self):
        return {"plain_text_selector": {"text": self.text}}

    def fromYamlDict(yamlDict):
        print("Text is " + yamlDict["text"])
        return PlainTextSelector(yamlDict["text"])


# Split Selector takes a Selected Single (which it will turn to HTML) or a Selected Value. It splits that string by the string delimiter, and returns a Selected Multiple of Selected Values.
class SplitSelector(Selector):
    def __init__(self, delimiter):
        self.expected_selected = [SelectedType.VALUE, SelectedType.SINGLE]
        self.delimiter = delimiter

    def select(self, selected):
        text_rep = str(selected.value if selected.selected_type == SelectedType.SINGLE else selected.value)
        split_up = text_rep.split(self.delimiter)
        portions = []

        for portion in split_up:
            portion_soup = BeautifulSoup(portion, 'html.parser')
            portion_single = Selected(portion_soup, SelectedType.SINGLE)
            portions.append(portion_single)


        return Selected(portions, SelectedType.MULTIPLE)

    def fromYamlDict(yamlDict):
        return SplitSelector(yamlDict['delimiter'])

    def toYamlDict(self):
        return {"split_selector": {"delimiter": self.delimiter}}

