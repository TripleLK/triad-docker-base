# This file will contain selectors for handling multiple elements or complex structures

from .base import Selector, Selected, SelectedType
from copy import deepcopy
# A ForEachSelector is initialized with a Selector of any type (including a SeriesSelector). It takes a Selected Multiple and returns a Selected Multiple, where each Selected in the returned Selected Multiple is the result of applying the selector to an element of the inputted Selected Multiple (in order)
class ForEachSelector(Selector):
    def __init__(self, selector, skip_on_fail=False):
        self.expected_selected = SelectedType.MULTIPLE
        self.selector = selector
        self.skip_on_fail = skip_on_fail

    def select(self, selected):
        super().select(selected)
        sub_selecteds = selected.value

        result_selecteds = []
        for sub_selected in sub_selecteds:
            try:
                result_selected = self.selector.select(sub_selected)
                result_selecteds.append(result_selected)
            except Exception as e:
                if self.skip_on_fail:
                    pass
                else:
                    raise e

        return Selected(result_selecteds, SelectedType.MULTIPLE)

    def toYamlDict(self):
        return {'for_each_selector': {'selector': self.selector.toYamlDict()}}

    def fromYamlDict(yamlDict):
        skip_on_fail = "skip_on_fail" in yamlDict and yamlDict["skip_on_fail"]
        subselector = Selector.fromYamlDict(yamlDict['selector'])
        return ForEachSelector(subselector, skip_on_fail)

# A SeriesSelector is initialized with a list of Selectors. It takes a Selected of the type expected by its first selector and calls the selectors in sequence, returning the final value.
# Variable type, depends on selectors assigned to it
class SeriesSelector(Selector):
    def __init__(self, selectors):
        self.selectors = selectors

    def select(self, selected):

        current = selected
        series_copy = deepcopy(self.selectors)
        while series_copy != []:
            current = series_copy.pop(0).select(current)

        return current

    def toYamlDict(self):
        return [selector.toYamlDict() for selector in self.selectors]

    def fromYamlDict(yamlDictList):
        subSelectors = [Selector.fromYamlDict(subYamlDict) for subYamlDict in yamlDictList]
        return SeriesSelector(subSelectors)


# A MappingSelector is initialized with a dictionary of string keywords to selectors. It takes a Selected Single and returns a Selected Value with the same keywords, mapped to the value selected by their Selector
# error strategy will get upgraded at some point, but can be "mark_none" (to mark the option down as none), "raise" (to raise the error), or "skip" to skip this entire iteration of the map
class MappingSelector(Selector):
    def __init__(self, mapping, error_strategy="skip"):
        self.expected_selected = SelectedType.SINGLE
        self.mapping = mapping
        self.error_strategy = error_strategy

    def select(self, selected):
        super().select(selected)

        mapped = {}
        for key, selector in self.mapping.items():
            try:
                mapped[key] = selector.select(selected).collapsed_value
            except Exception as e:
                if self.error_strategy == "raise":
                    raise e
                elif self.error_strategy == "mark_none":
                    print("Exception raised while reterieving value for", str(key) + ", setting to None: ", e)
                    mapped[key] = None
                else:
                    raise Exception("skipping, error says: ", e)

        return Selected(mapped, SelectedType.VALUE)

    def toYamlDict(self):
        args_dict = {}
        for key, val in self.mapping.items():
            args_dict[key] = val.toYamlDict()

        return {'mapping_selector': args_dict}

    def fromYamlDict(yamlDict):
        mapping = {}
        for key, selector in yamlDict.items():
            mapping[key] = Selector.fromYamlDict(selector)

        return MappingSelector(mapping)

# A ZipSelector takes two Selectors as arguments, one of which (keys) will be used to make the keys of a dictionary, the other of which (values) will be used to make the values of that dictionary. May adapt it eventually to allow an arbitrary number of value options, but not sure
class ZipSelector(Selector):
    def __init__(self, keys_selector, vals_selector):
        self.keys_selector = keys_selector
        self.vals_selector = vals_selector

    
    def select(self, selected):
        keys = self.keys_selector.select(selected).value
        vals = self.vals_selector.select(selected).value

        if len(keys) != len(vals):
            raise Exception("Keys and Vals provided to ZipSelector must be the same length!")

        keys_are_values = [key.selected_type == SelectedType.VALUE for key in keys]
        vals_are_values = [val.selected_type == SelectedType.VALUE for val in vals]

        key_values = [key.collapsed_value for key in keys]
        val_values = [val.collapsed_value for val in vals]

        mapped = dict(zip(key_values, val_values))

        return Selected(mapped, SelectedType.VALUE)

    def toYamlDict(self):
        return {'zip_selector': {'keys': self.keys_selector.toYamlDict(), 'vals': self.vals_selector.toYamlDict()}}

    def fromYamlDict(yamlDict):
        mapping = {}
        for key, selector in yamlDict.items():
            mapping[key] = Selector.fromYamlDict(selector)

        return ZipSelector(Selector.fromYamlDict(yamlDict['keys']), Selector.fromYamlDict(yamlDict['vals']))


# A ConcatSelector takes two Selectors as arguments, and returns a Selected Value with the result of concatenating the result of the first selector with the result of the second selector
class ConcatSelector(Selector):
    def __init__(self, first, second):
        self.first = first
        self.second = second
        print("concat inited")

    def select(self, selected):
        return Selected(str(self.first.select(selected).collapsed_value) + str(self.second.select(selected).collapsed_value), SelectedType.VALUE)

    def toYamlDict(self):
        return {"concat_selector": {first: self.first.toYamlDict(), second: self.second.toYamlDict()}}

    def fromYamlDict(yamlDict):
        print("About to init concat")
        return ConcatSelector(Selector.fromYamlDict(yamlDict['first']), Selector.fromYamlDict( yamlDict['second'] ))
