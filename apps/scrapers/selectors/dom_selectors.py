# This file will contain selectors for DOM manipulation

from .base import Selector, Selected, SelectedType
from copy import deepcopy
import re

# A SoupSelector is initialized with a dictionary of attribute names to values. It takes a Selected Single and finds all children of the Single that have those values for those attributes. Use tag_name to target a tag. Has an optional "index" parameter that can be used to specify an index, which will be accessed using an IndexedSelector
class SoupSelector(Selector):
    def __init__(self, attrs, re_attrs=None, index=None):
        self.original_attrs = attrs
        self.original_re_attrs = re_attrs
        new_attrs = deepcopy(attrs)

        # compile any regex type attributes
        if re_attrs != None:

            for key, val in re_attrs.items():
                compiled = re.compile(val)
                new_attrs[key] = re.compile(val)


        self.expected_selected = SelectedType.SINGLE
        self.tagname = new_attrs.pop("tag_name") if "tag_name" in attrs else None
        self.attrs = new_attrs
        self.index=index

    def select(self, selected):
        super().select(selected)

        if self.tagname != None:
            values = selected.value.find_all(self.tagname, attrs=self.attrs)
        else:
            values = selected.value.find_all(attrs=self.attrs)

        selecteds = Selected([Selected(val, SelectedType.SINGLE) for val in values], SelectedType.MULTIPLE)
        if self.index != None:
            return IndexedSelector(self.index).select(selecteds)
        return selecteds

    def toYamlDict(self):
        args_dict = {}
        args_dict['attrs'] = self.original_attrs

        if self.index != None:
            args_dict['index'] = self.index

        if self.original_re_attrs != None:
            args_dict['re_attrs'] = self.original_re_attrs

        return {'soup_selector': args_dict}

    def fromYamlDict(yamlDict):
        if 'index' in yamlDict:
            return SoupSelector(yamlDict['attrs'], index=yamlDict['index'])

        attrs_dict = deepcopy(yamlDict['attrs'])

        re_attrs_dict = deepcopy(yamlDict['re-attrs']) if 're-attrs' in yamlDict else None


        return SoupSelector(yamlDict['attrs'], re_attrs=re_attrs_dict)


# An IndexedSelector is initialized with an index n. It takes a Selected Multiple and returns the nth element of it.
class IndexedSelector(Selector):
    def __init__(self, index):
        self.expected_selected = SelectedType.MULTIPLE
        self.index = index

    def select(self, selected):
        super().select(selected)

        return selected.value[self.index]

    def toYamlDict(self):
        return {'indexed_selector': {'index': self.index}}

    def fromYamlDict(yamlDict):
        return IndexedSelector(yamlDict['index'])

# An AttrSelector retrieves a given attribute from a Selected Single
class AttrSelector(Selector):
    def __init__(self, attr):
        self.expected_selected = SelectedType.SINGLE
        self.attr = attr

    def select(self, selected):
        super().select(selected)
        return Selected(selected.value[self.attr], SelectedType.VALUE)

    def toYamlDict(self):
        return {'attr_selector': {'attr': self.attr}}

    def fromYamlDict(yamlDict):
        return AttrSelector(yamlDict['attr'])