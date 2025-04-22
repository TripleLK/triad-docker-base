import requests
from bs4 import BeautifulSoup
import bs4
from enum import Enum
from abc import ABC
import yaml



# This file will contain the base classes and enums
class SelectedType(Enum):
    VALUE = 0
    SINGLE = 1
    MULTIPLE = 2

class Selected:
    def __init__(self, value, selected_type):
        self.value = value
        self.selected_type = selected_type
        potential_type_error = self.__validate_selected_type()

        if potential_type_error != None:
            raise potential_type_error


    @property
    def collapsed_value(self):
        if self.selected_type == SelectedType.MULTIPLE:
            return [sub_selected.collapsed_value for sub_selected in self.value]
        else:
            return self.value



    def __str__(self):
        if self.selected_type != SelectedType.MULTIPLE:
            return str(self.value)
        else:
            return str(self.values())


    def __validate_selected_type(self):
        sts = SelectedType.VALUE
        sts = SelectedType.SINGLE
        stm = SelectedType.MULTIPLE
       # verify that the element being saved in self is of an appropriate type
        selected_type_to_allowed_types = {
            sts: [bs4.element.Tag, BeautifulSoup],
            stm: [list]
        }
        if self.selected_type in selected_type_to_allowed_types:
            allowed_types = selected_type_to_allowed_types[self.selected_type]
            if type(self.value) not in allowed_types:
                return TypeError("Selected of type " + self.selected_type.name + " must have a value of type " + " or ".join([str(typ) for typ in allowed_types])+ ". Your value is of type " + str(type(self.value)))

        # additional check for multiple that its children are all other selecteds
        if self.selected_type == SelectedType.MULTIPLE:
            if not all([isinstance(el, Selected) for el in self.value]):
                return TypeError("Selecteds of type Multiple must be lists of other Selecteds")

        return None


class Selector(ABC):
    def validate_selected_type(self, selected):
        if isinstance(self.expected_selected, list):
            if selected.selected_type not in self.expected_selected:
                raise TypeError(str(type(self)) + " expects a Selected of type " + " or ".join([expsel.name for exspel in self.expected_selected]) + ", but received " + selected.selected_type.name)
        else:
            if selected.selected_type != self.expected_selected:
                raise TypeError(str(type(self)) + " expects a Selected of type " + self.expected_selected.name + ", but received " + selected.selected_type.name)

    def __call__(self, selected):
        return self.select(selected)

    def select(self, selected):
        self.validate_selected_type(selected)

    def fromYamlDict(yamlDict):
        from .text_selectors import TextSelector, HtmlSelector, PlainTextSelector, SplitSelector
        from .structural_selectors import SeriesSelector, MappingSelector, ZipSelector, ConcatSelector, ForEachSelector
        from .dom_selectors import SoupSelector, IndexedSelector, AttrSelector
        from .utility_selectors import FileSelector, PrintSelector
        # Determine what the top level is. if it's a list it must be a seriessel
        if isinstance(yamlDict, list):
            return SeriesSelector.fromYamlDict(yamlDict)
        elif isinstance(yamlDict, str):
            string_specs_dict = {
                "text_selector": TextSelector,
                "html_selector": HtmlSelector
            }
            if yamlDict in string_specs_dict:
                return string_specs_dict[yamlDict].fromYamlDict(yamlDict)
        elif isinstance(yamlDict, dict):
            dict_specs_dict = {
                "soup_selector": SoupSelector,
                "indexed_selector": IndexedSelector,
                "attr_selector": AttrSelector,
                "for_each_selector": ForEachSelector,
                "mapping_selector": MappingSelector,
                "split_selector": SplitSelector,
                "file_selector": FileSelector,
                "print_selector": PrintSelector,
                "concat_selector": ConcatSelector,
                "plain_text_selector": PlainTextSelector,
                'zip_selector': ZipSelector
            }
            # there will only be one key in the dict, and it'll be the name of the selector
            for key, value in yamlDict.items():
                sole_selector = key
                sole_arguments = value

            try:
                return dict_specs_dict[sole_selector].fromYamlDict(sole_arguments)
            except Exception as e:
                print(sole_selector, "<- selector\n", sole_arguments, "<- arguments")
                raise Exception("errored:", e)

    def fromFilePath(file_path):
        try:
            with open(file_path, 'r') as file:
                yaml_file = file.read()

            yaml_dict = yaml.safe_load(yaml_file)
            if yaml_dict == None:
                raise Exception("No contents of file!")

        except Exception as e:
            print("There was an issue trying to load the file! Error:\n", e)
            return None

        return Selector.fromYamlDict(yaml_dict)


    def toYamlDict(self):
        pass

