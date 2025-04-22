# This file will contain utility selectors

from .base import Selector, Selected, SelectedType

# Creates a selector based on a secondary file. Allows for neatening of files
class FileSelector(Selector):
    def __init__(self, file_path):
        self.file_path = file_path

        self.selector = Selector.fromFilePath(file_path)

    def select(self, selected):
        
        return self.selector.select(selected)

    def toYamlDict(self):
        return self.selector.toYamlDict()

    def fromYamlDict(yamlDict):
        return FileSelector(yamlDict['file_path'])

# A PrintSelector is initialized with a message and a boolean value. If the boolean value is true, the message will be printed, and the selected value will be printed. If the boolean value is false, the message will be printed, but the selected value will not be printed.
class PrintSelector(Selector):
    def __init__(self, message, print_selected=False):
        self.message = message
        self.print_selected = print_selected

    def select(self, selected):
        print(self.message)
        if self.print_selected:
            print("PrintSelector report.\nSelected Type:", selected.selected_type, "\nCollapsed Value:", selected.collapsed_value)
        return selected

    def toYamlDict(self):
        if print_selected:
            return {"print_selector": {"message": self.message, "print_selected": True}}
        return {"print_selector": {"message": self.message}}

    def fromYamlDict(yamlDict):
        return PrintSelector(yamlDict["message"], print_selected=("print_selected" in yamlDict and yamlDict["print_selected"]))
