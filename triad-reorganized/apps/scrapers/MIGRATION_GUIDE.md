# Selector System Refactoring

This document explains the changes made to the selector system and provides guidance on migrating from the old system to the new one.

## Changes Made

1. **Split into modules**: Each selector class is now in its own file in the `selectors` package.
2. **Added CSS selectors**: Leveraging BeautifulSoup's CSS selector capabilities for cleaner, more powerful selection.
3. **Enhanced type validation**: Better type checking with clearer error messages.
4. **Improved documentation**: Added docstrings, type hints, and a comprehensive README.
5. **Added logging**: Replaced print statements with proper logging.
6. **Error handling**: More robust error handling throughout.

## Key Benefits

- **Simplicity**: CSS selectors make it much easier to extract elements from HTML.
- **Maintainability**: Split code makes it easier to understand and modify.
- **Type safety**: Catch type errors early with better validation.
- **Extensibility**: Easier to add new selectors or modify existing ones.

## Migrating from SoupSelector to CSSSelector

The most important change is the introduction of `CSSSelector`, which allows you to use standard CSS selectors instead of the more verbose attribute-based selectors.

### Before:

```python
selector = SoupSelector({
    "tag_name": "div", 
    "class": "content"
})
```

### After:

```python
selector = CSSSelector('div.content')
```

### Common CSS Selector Patterns:

| Old (SoupSelector) | New (CSSSelector) |
|-------------------|------------------|
| `{"tag_name": "div"}` | `"div"` |
| `{"tag_name": "div", "class": "content"}` | `"div.content"` |
| `{"tag_name": "a", "href": re.compile(r"^https")}` | `"a[href^='https']"` |
| `{"tag_name": "div", "id": "header"}` | `"div#header"` |
| `{"class": "item"}` (any tag with class) | `".item"` |

### Chaining Selectors

#### Before:

```python
selector = SeriesSelector([
    SoupSelector({"tag_name": "div", "class": "content"}),
    IndexedSelector(0),
    SoupSelector({"tag_name": "h1"}),
    TextSelector()
])
```

#### After:

```python
# Option 1: Using SeriesSelector (still available)
selector = SeriesSelector([
    CSSSelector('div.content', index=0),
    CSSSelector('h1', index=0),
    TextSelector()
])

# Option 2: Direct chaining (more explicit)
soup_selected = Selected(soup, SelectedType.SINGLE)
content_div = CSSSelector('div.content', index=0).select(soup_selected)
title_element = CSSSelector('h1', index=0).select(content_div)
title_text = TextSelector().select(title_element)
```

## Importing Selectors

### Before:

```python
from apps.scrapers.Selectors import (
    Selector, Selected, SelectedType,
    SoupSelector, TextSelector, IndexedSelector
)
```

### After:

```python
from apps.scrapers.selectors import (
    Selector, Selected, SelectedType,
    CSSSelector, TextSelector, IndexedSelector
)
```

## Examples

### Extract a Page Title

#### Before:

```python
selector = SeriesSelector([
    SoupSelector({"tag_name": "title"}),
    IndexedSelector(0),
    TextSelector()
])
```

#### After:

```python
selector = SeriesSelector([
    CSSSelector('title', index=0),
    TextSelector()
])
```

### Extract All Links with Their Text

#### Before:

```python
links_selector = SoupSelector({"tag_name": "a"})
links = links_selector.select(soup_selected)

for link in links.value:
    href_selector = AttrSelector("href")
    text_selector = TextSelector()
    
    href = href_selector.select(link).value
    text = text_selector.select(link).value
    print(f"{text}: {href}")
```

#### After:

```python
links_selector = CSSSelector('a')
links = links_selector.select(soup_selected)

for link in links.value:
    href_selector = AttrSelector("href")
    text_selector = TextSelector()
    
    href = href_selector.select(link).value
    text = text_selector.select(link).value
    print(f"{text}: {href}")
```

### Extract Items from a Table

#### Before:

```python
rows_selector = SeriesSelector([
    SoupSelector({"tag_name": "table", "id": "data"}),
    IndexedSelector(0),
    SoupSelector({"tag_name": "tr"})
])
```

#### After:

```python
rows_selector = CSSSelector('table#data tr')
```

## Future Improvements

1. **Fluent API**: Consider adding method chaining for even cleaner code.
2. **Caching**: Add caching for better performance when reusing selectors.
3. **Testing**: Add a comprehensive test suite for all selectors.
4. **More CSS features**: Support for pseudo-selectors and more advanced CSS features.
5. **Async support**: Add async versions of selectors for non-blocking operations.
