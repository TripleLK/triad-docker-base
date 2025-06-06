# Triad Scientific Website Structure Analysis

This document outlines the structure of the triadscientific.com website for the development of scraping selectors and tools.

## Navigation Structure

The website has a hierarchical navigation structure with the following main categories:

- **Lab Instrumentation**: Various lab instruments categorized by type (FTIR, GC, HPLC, etc.)
- **Lab Equipment**: General lab equipment (balances, centrifuges, baths, etc.)
- **Lab Furniture**: Lab casework, fume hoods, blowers, cabinets, etc.

Additional sections on the homepage include:
- "Featured items - new!" 
- "Used equipment specials"

## URL Pattern Analysis

The website follows these URL patterns:

- Main website: `http://www.triadscientific.com/`
- Category pages: `http://www.triadscientific.com/en/products/[category]/[id]`
- Product detail pages: `http://www.triadscientific.com/en/products/[category]/[id]/[product-name]/[product-id]`
- Contact page: `http://www.triadscientific.com/en/contact-us/`

Example URLs:
- Category page: `http://www.triadscientific.com/en/products/ftir-systems/1091`
- Product detail page: `http://www.triadscientific.com/en/products/ftir-ir-and-near-ir-spectroscopy/946/mattson-ati-genesis-series-ftir-with-software/249015`

## Product Listing Pages

Product listing pages contain:
- Category header
- List of products with brief titles
- "+ details" links to access product detail pages
- "Back to main page" navigation

## Product Detail Pages

Product detail pages contain:
- Product name/title (H1 heading)
- Category breadcrumb navigation
- Product description (varies in length and detail by product)
- Technical specifications (where available)
- Product images
- Related products section
- Standard footer with company information

## Key Information to Extract

For each product, the following information should be extracted:

1. **Product name**: Main title of the product
2. **Category/subcategory**: Where the product is listed in the navigation
3. **Short description**: Brief summary (when available)
4. **Full description**: Detailed product description
5. **Technical specifications**: Technical details organized in groups (varies by product)
6. **Images**: Product images and gallery
7. **Price information**: When available (often requires contacting seller)
8. **Models/variants**: Some products have different model options

## HTML Structure Patterns

The website uses a relatively consistent HTML structure with:
- Standard heading elements for titles and section headers
- Text content in paragraph elements
- Product listings often in unordered lists or div containers
- "+ details" links for product navigation

## Next Steps

Based on this analysis, we will:
1. Create YAML selectors for extracting category and product URLs
2. Develop selectors for product information extraction
3. Implement a scraping strategy that follows the navigation hierarchy
4. Handle pagination and listing pages
5. Extract and process product details

This document will be updated as we gather more information about specific elements and patterns during selector development. 