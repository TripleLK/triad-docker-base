# Selectors Package

A framework for composable, serializable HTML selectors based on BeautifulSoup.

## Overview

The selectors package provides a type-safe way to extract and manipulate data from HTML documents. It's built around the concept of selector chaining, where simple selectors can be composed to create complex data extraction pipelines.

Key features:
- **CSS Selectors**: Use standard CSS selectors to extract elements
- **Type Safety**: Selectors validate their input and output types
- **Composability**: Chain selectors together to create complex extraction pipelines
- **Serialization**: Save and load selectors from YAML files

## Key Concepts

### SelectedType

Represents the type of data held by a `Selected` object:
- `VALUE`: Terminal values that cannot be further selected from (strings, numbers, dicts, etc.)
- `SINGLE`: A single BeautifulSoup tag or the root BeautifulSoup object
- `MULTIPLE`: A list of `Selected` objects

### Selected

A wrapper around the result of a selector operation, including its type information.

### Selector

The abstract base class for all selectors. Selectors are callable objects that transform one `Selected` object into another.

## Available Selectors

### Core Selectors
- `CSSSelector`: Select elements using CSS selectors
- `TextSelector`: Extract text from a `SINGLE` element
- `IndexedSelector`: Extract an element at a specific index from a `MULTIPLE`

### Additional Selectors (Coming Soon)
- `HtmlSelector`: Extract HTML from a `SINGLE` element
- `SoupSelector`: Select elements using BeautifulSoup's find/find_all capabilities
- `AttrSelector`: Extract an attribute from a `SINGLE` element
- `SplitSelector`: Split text by a delimiter
- `SeriesSelector`: Apply a sequence of selectors
- `ForEachSelector`: Apply a selector to each element in a `MULTIPLE`
- `MappingSelector`: Create a dictionary by applying multiple selectors to a `SINGLE`
- `ZipSelector`: Create a dictionary by zipping keys and values from two selectors
- `PlainTextSelector`: Return a fixed text value
- `ConcatSelector`: Concatenate the results of two selectors
- `PrintSelector`: Print debug information
- `FileSelector`: Load a selector from a file

## Example Usage

```python
from bs4 import BeautifulSoup
from selectors import Selected, SelectedType, CSSSelector, TextSelector, IndexedSelector

# Parse HTML
html = '''
<html>
  <body>
    <div class="content">
      <h1>Title</h1>
      <p>Paragraph 1</p>
      <p>Paragraph 2</p>
    </div>
  </body>
</html>
'''
soup = BeautifulSoup(html, 'html.parser')

# Wrap in a Selected object
selected = Selected(soup, SelectedType.SINGLE)

# Select all paragraphs
p_selector = CSSSelector('p')
paragraphs = p_selector.select(selected)  # Returns a MULTIPLE

# Get the first paragraph
first_p = IndexedSelector(0).select(paragraphs)  # Returns a SINGLE

# Extract the text
text = TextSelector().select(first_p)  # Returns a VALUE
print(text.value)  # Outputs: "Paragraph 1"

# Or chain the operations:
result = CSSSelector('h1').select(selected)
result = IndexedSelector(0).select(result)
result = TextSelector().select(result)
print(result.value)  # Outputs: "Title"
```

## YAML Serialization

Selectors can be serialized to and from YAML:

```python
import yaml
from selectors import Selector, CSSSelector

# Create a selector
selector = CSSSelector('div.content > h1')

# Convert to YAML dict
yaml_dict = selector.toYamlDict()

# Serialize to YAML string
yaml_str = yaml.dump(yaml_dict)

# Deserialize
loaded_yaml = yaml.safe_load(yaml_str)
recreated_selector = Selector.fromYamlDict(loaded_yaml)
```

## Migration from Old Selectors

To migrate from the old selector system:

1. Replace `SoupSelector` with `CSSSelector` when possible
2. Chain selectors using direct method calls instead of `SeriesSelector` for simpler cases
3. Use the new type checking system to catch errors earlier

Example migration:
```python
# Old approach
old_selector = SeriesSelector([
    SoupSelector({"tag_name": "div", "class": "content"}),
    IndexedSelector(0),
    SoupSelector({"tag_name": "h1"}),
    IndexedSelector(0),
    TextSelector()
])

# New approach
new_selector = CSSSelector('div.content h1', index=0)
result = new_selector.select(selected)
result = TextSelector().select(result)
``` 