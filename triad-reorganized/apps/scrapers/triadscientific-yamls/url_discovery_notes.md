# URL Discovery Strategy for Triad Scientific

This document outlines the approach for discovering and extracting product URLs from the triadscientific.com website.

## Approach Overview

Based on the website structure analysis, we'll use a multi-level discovery approach:

1. Extract main category URLs from the homepage
2. Extract subcategory URLs from each main category page
3. Extract product URLs from category/subcategory pages

## Main Category Discovery

From the homepage, we need to extract the main category links:
- Lab Instrumentation
- Lab Equipment
- Lab Furniture

These main categories are located in the top navigation menu. Preliminary CSS selector:
```
div.menubar a
```

## Subcategory Discovery

Within each main category page, multiple subcategories are listed. For example:
- Under "Lab Instrumentation": FTIR Systems, Gas Chromatography, HPLC, etc.
- Under "Lab Equipment": Analytical Balances, Baths-Water, Centrifuges, etc.

These subcategories can be extracted using selectors targeting the list structure. Preliminary CSS selector:
```
ul.subcategories li a
```

## Product URL Extraction

From each subcategory page, we can extract individual product URLs. Products are typically listed with a title and a "+ details" link. Preliminary CSS selector for product links:
```
div.product-item a[href*="products"]
```

Alternatively, we may target the "+ details" links:
```
a:contains("+ details")
```

## Handling Pagination

Some category pages may have pagination. We'll need to check for and handle pagination links to ensure we capture all products. Preliminary CSS selector:
```
div.pagination a
```

## URL Structure Patterns

As identified in the structure analysis:
- Category pages: `http://www.triadscientific.com/en/products/[category]/[id]`
- Product detail pages: `http://www.triadscientific.com/en/products/[category]/[id]/[product-name]/[product-id]`

We'll verify URLs match these patterns during extraction.

## Example YAML Selector for Main Categories

```yaml
---
css_selector:
  selector: "div.menubar a"
  multiple: true
  extract:
    href:
      attr_selector:
        attr_name: "href"
```

## Example YAML Selector for Products on a Category Page

```yaml
---
css_selector:
  selector: "div.product-item a[href*='products']"
  multiple: true
  extract:
    href:
      attr_selector:
        attr_name: "href"
```

## Next Steps

1. Validate these preliminary selectors against the actual website
2. Refine selectors based on testing
3. Create comprehensive YAML files for each level of URL discovery
4. Implement error handling for missing or malformed URLs
5. Test the complete URL discovery process on a sample of categories

This document will be updated as we refine our understanding of the website structure and selector performance. 