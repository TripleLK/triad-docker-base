# TriadScientific Implementation Plan
The following is an in depth plan to implement scrapers for the website http://www.triadscientific.com initially written by a planning model and since updated by other models. If you are reading this, you are a model and you have been assigned a specific step that you will be working on (if you haven't, ask me what step you are working on). As you do any work in this project, it is vital that you update this document, both with details of how you accomplished parts of the plan, and with knowledge you've gathered about the project that may be useful for another model. In short, when in doubt, add information to this document.

It is vital that you take small, testable steps at a time and make sure individual parts work before moving onto something else. Each step of the plan is meant to take several turns of interaction between you and the user.


## Step 1: Analyze triadscientific.com website structure [COMPLETE]
**Tasks:**
- Examine the main navigation structure (Lab Instrument, Lab Equipment, etc.)
- Analyze several product detail pages to identify common patterns
- Map the HTML structure of product listings and product details
- Determine URL patterns for navigation (category pages, subcategory pages, product pages)
- Identify key information to extract (name, description, specs, images, price if available)

### Website Structure Analysis

#### Navigation Structure

The website has a hierarchical organization with the following structure:

1. **Main Category Sections** (5 primary columns on the homepage):
   - **Lab Instrument**: Various analytical instruments (FTIR, GC, HPLC, etc.)
   - **Lab casework, Furniture, Hoods, Blowers**: Lab infrastructure and furniture
   - **Instrument Parts and accessories**: Components and replacement parts
   - **Lab Instrumentation and Equipment**: General lab equipment
   - **New Lab Equipment**: New product offerings from various manufacturers

2. **Subcategories**:
   Each main category contains multiple subcategories. For example:
   - Under "Lab Instrument": Atomic Absorption, FTIR Systems, HPLC, etc.
   - Under "Lab Instrumentation and Equipment": Analytical Balances, Centrifuges, etc.

3. **Feature Sections** on the homepage:
   - "Featured items - new!" - Highlighted new products
   - "Used equipment specials" - Special offers on used equipment

#### URL Patterns

The website follows these URL patterns:

- Main website: `http://www.triadscientific.com/`
- Category pages: `http://www.triadscientific.com/en/products/[category]/[id]`
- Product detail pages: `http://www.triadscientific.com/en/products/[category]/[id]/[product-name]/[product-id]`
- Contact page: `http://www.triadscientific.com/en/contact-us/`

Example URLs:
- Category page: `http://www.triadscientific.com/en/products/ftir-systems/1091`
- Product detail page: `http://www.triadscientific.com/en/products/ftir-ir-and-near-ir-spectroscopy/946/mattson-ati-genesis-series-ftir-with-software/249015`

#### Product Listing Pages

Product listing pages contain:
- Category header
- List of products with brief titles
- "+ details" links to access product detail pages
- "Back to main page" navigation

#### Product Detail Pages

Product detail pages contain:
- Product name/title (H1 heading)
- Category breadcrumb navigation
- Product description (varies in length and detail by product)
- Technical specifications (where available)
- Product images
- Related products section ("Other items in same category")
- Standard footer with company information

#### Key Information to Extract

For each product, the following information should be extracted:

1. **Product name**: Main title of the product
2. **Category/subcategory**: Where the product is listed in the navigation
3. **Short description**: Brief summary (when available)
4. **Full description**: Detailed product description
5. **Technical specifications**: Technical details organized in groups (varies by product)
6. **Images**: Product images and gallery
7. **Price information**: When available (often requires contacting seller)
8. **Models/variants**: Some products have different model options

#### HTML Structure Patterns

The website uses a relatively consistent HTML structure with:
- Standard heading elements for titles and section headers
- Text content in paragraph elements
- Product listings often in unordered lists or div containers
- "+ details" links for product navigation

### URL Discovery Strategy

Based on the website structure analysis, we'll use a multi-level discovery approach:

1. **Extract main category URLs** from the homepage
   - Target the 5 main category columns
   
2. **Extract subcategory URLs** from each main category page
   - Extract links to subcategories like FTIR Systems, Analytical Balances, etc.
   
3. **Extract product URLs** from category/subcategory pages
   - Target product listings and "+ details" links

#### Preliminary CSS Selectors

For main categories:
```
div.category-column a
```

For subcategories:
```
ul.subcategories li a
```

For product links:
```
div.product-item a
```
or
```
a:contains("+ details")
```

### Product Information Extraction Strategy

For extracting detailed product information from product pages:

#### Preliminary Product Page Selectors

1. **Product Name**:
```yaml
css_selector:
  selector: "h1"
  extract: text_selector
```

2. **Short Description**:
```yaml
css_selector:
  selector: "div.product-summary p"
  extract: text_selector
```

3. **Full Description**:
```yaml
css_selector:
  selector: "div.product-description"
  extract: html_selector
```

4. **Images**:
```yaml
css_selector:
  selector: "div.product-images img"
  multiple: true
  extract:
    src:
      attr_selector:
        attr_name: "src"
```

5. **Technical Specifications**:
```yaml
css_selector:
  selector: "div.specifications"
  extract:
    specs:
      for_each_selector:
        css_selector:
          selector: "tr"
          multiple: true
          extract:
            spec_name:
              css_selector:
                selector: "td:first-child"
                extract: text_selector
            spec_value:
              css_selector:
                selector: "td:last-child"
                extract: text_selector
```

### Challenges Identified

1. **Variation in Product Information**: Not all products have the same level of detail
2. **Mixed Content Formatting**: Some product descriptions may have HTML formatting
3. **Unknown Pagination**: Need to confirm if pagination is used on category pages
4. **Image Handling**: Multiple images may need special processing

### Implementation Plan for Next Steps

1. **Start with Main Categories**: Begin by implementing selectors for the main navigation categories
2. **Build a Crawler Approach**: Create a crawler that can:
   - Extract main category URLs
   - Visit each category to extract subcategory URLs
   - Visit each subcategory to extract product URLs
   - Handle any pagination encountered

3. **YAML Selectors to Develop**:
   - `categories.yaml` - For main category extraction
   - `subcategories.yaml` - For subcategory extraction from categories
   - `product_urls.yaml` - For product URL extraction from subcategories
   - `pagination.yaml` - If needed for multi-page listings
   - `name.yaml` - For product name extraction
   - `short_description.yaml` - For product summary extraction
   - `full_description.yaml` - For detailed description extraction
   - `imgs.yaml` - For product image extraction
   - `specs_groups.yaml` - For technical specifications extraction
   - `models.yaml` - For product variants/models information
   - `mapping.yaml` - To combine all component extractors

**Expected Output:** Documentation of website structure, URL patterns, and data extraction points [COMPLETED]

## Step 2: Create URL discovery mechanism [COMPLETE]
**Tasks:**
- Create YAML selectors for extracting category links
- Create YAML selectors for extracting product links from category pages
- Develop a URL discovery strategy that:
  - Starts from the main categories
  - Navigates through categories
  - Collects all product page URLs
- Handle pagination if present on category pages
- Implement error handling for failed URL extractions

### URL Discovery Implementation

#### Website Structure Insights

After analyzing the website, we discovered that triadscientific.com has a simpler structure than initially anticipated:

1. **Main Categories**: The website has approximately 246 direct category pages accessible from the homepage
2. **Product Pages**: Each category page lists products with "+ details" links
3. **No true subcategory hierarchy**: While visually grouped into sections like "Lab Instrumentation", "Lab Equipment", etc., the actual URL structure uses a flat category approach

#### YAML Selectors Created

We implemented these key YAML selectors:

1. **`categories.yaml`**: Extracts all category URLs from the homepage
   - Uses CSS selector to find links containing "/products/" in the href
   - Filters using regex to match the pattern: `/en/products/[category]/[id]`
   - Extracts both the URL and category name

2. **`product_urls.yaml`**: Extracts product URLs from category pages
   - Targets links with the text "+ details"
   - Extracts product names from text preceding the links
   - Ensures all URLs are converted to absolute URLs

3. **`pagination.yaml`**: Handles pagination on category pages if present
   - Targets links within pagination divs or lists
   - Follows pagination links to discover all products

#### Discovery Process

The URL discovery mechanism follows a two-level approach:

1. **First Level**: Extract all category URLs from the homepage
2. **Second Level**: For each category, extract all product URLs (following pagination if present)

We implemented a Python module `url_discovery.py` that:

- Uses BeautifulSoup to extract the relevant elements based on our YAML selectors
- Implements proper error handling for network issues or parsing errors
- Includes rate limiting (1 second delay between requests) to avoid overloading the website
- Tracks visited URLs to prevent duplicate processing
- Handles relative URLs, converting them to absolute URLs

#### Testing and Validation

We created a test script `test_url_discovery.py` to verify our selectors and URL discovery mechanism:

- **Main Category Test**: Successfully extracts 246 category URLs from the homepage
- **Product URL Test**: Successfully extracts product URLs from category pages
- **Single Category Test**: Validates the full workflow for a single category

#### Output Format

The discovery process saves product URLs and their names to a text file, with each line containing:
```
[product_url] | [product_name]
```

This format will provide the necessary input for Step 3 (product information extractors).

**Expected Output:** YAML configurations for URL discovery and a Python module that uses these to extract all product URLs [COMPLETED]

## Step 3: Develop product information extractors [PARTIAL]
**Tasks:**
- Create name.yaml for extracting product names (likely from h1 or similar elements)
- Create short_description.yaml for extracting product summaries
- Create full_description.yaml for extracting detailed product descriptions
- Create imgs.yaml for extracting product images
- Create specs_groups.yaml for extracting technical specifications if available
- Create models.yaml for handling product variants
- Create mapping.yaml to combine all component extractors

### Implementation Progress

We have created initial versions of the following YAML selectors:

1. **`name.yaml`**: Extracts product names from `<h1>` tags
2. **`imgs.yaml`**: Extracts product images from the carousel with `id="bigPicture"`
3. **`short_description.yaml`**: Extracts a brief product summary (first ~200 characters)
4. **`full_description.yaml`**: Extracts the complete product description as HTML
5. **`specs_groups.yaml`**: Implements a simplified approach for technical specifications that points to the full description
6. **`models.yaml`**: Creates a simplified model structure since Triad products don't typically have variants
7. **`mapping.yaml`**: Combines all component extractors

In Step 3b, we successfully migrated to the modular selector system, fixed YAML format compatibility issues, and established initial testing. Step 3c identified type flow challenges in specification extraction, particularly with VALUE/SINGLE/MULTIPLE type conversions.

Step 3d implemented a simplified specification extraction approach that provides a consistent placeholder directing users to the full description, ensuring reliable extraction across all product types.

**Expected Output:** Complete set of YAML selectors for extracting product information [PARTIALLY COMPLETED]

## Step 3e: Implement Short Description Fallback and Finalize Integration [COMPLETE]
**Tasks:**
- ✅ Implement a Python-level fallback mechanism for short descriptions when none are found by selectors
- ✅ Create intelligent selection of relevant sentences from full descriptions using fuzzy matching
- ✅ Add NLTK support for improved sentence tokenization with regex-based fallback
- ✅ Update mapping.yaml to integrate all component selectors
- ✅ Test the complete extraction process on multiple product pages across categories
- ✅ Document the implementation approach and test results

### Implementation
We successfully implemented a robust Python-level fallback for short descriptions in `Scrapers.py` using:
- Fuzzy string matching between product name and sentences
- Word-level matching to identify sentences containing product name components
- Multiple fallback strategies when no good match is found
- Proper handling of HTML content extraction
- Error resilience with graceful degradation

Comprehensive testing across multiple product categories (Atomic Absorption, Laboratory Equipment, Spectroscopy, Analytical Instruments) confirmed the solution's reliability and consistency.

**Expected Output:** A complete extraction system with fallback mechanisms for inconsistent content [COMPLETED]

## Step 4: Create Django Integration and Optimize Performance [COMPLETE]
**Tasks:**
- ✅ Implement proper integration with Django models for storing extracted data
- ✅ Create validation mechanisms for ensuring data quality and consistency
- ✅ Implement appropriate error handling and reporting for production environment
- ✅ Add performance optimizations for handling large-scale scraping
- ✅ Implement batch operations for processing multiple URLs
- ✅ Create a comprehensive logging system for production monitoring
- ✅ Develop validation checks to ensure continued accuracy as the website evolves

### Implementation
We successfully integrated the Triad Scientific scraper with Django models and enhanced it for production use:

- **Model Integration**: 
  - Added a `source_url` field to track the original product URL
  - Created a management command (`import_triadscientific`) that maps scraped data to models
  - Implemented creation/update logic to handle existing products

- **Error Handling and Monitoring**:
  - Added comprehensive exception handling with detailed error reporting
  - Implemented a retry mechanism for network-related failures
  - Created a dedicated logging system with a log file for monitoring

- **Production Features**:
  - Added support for batch processing from URL files
  - Implemented validation to ensure data quality
  - Created a dry-run mode for testing without making changes
  - Added detailed documentation and examples

The implementation was thoroughly tested with both single-product imports and batch imports using sample URLs.

**Expected Output:** A production-ready scraper system with complete Django model integration and optimization [COMPLETED]

## Step 5: Implement Management Command Enhancements and Tagging [PENDING]
**Tasks:**
- Integrate URL discovery with the import process in a single command
- Implement category-specific URL discovery options
- Add product categorization using the tagging system
- Implement automatic manufacturer tagging
- Create a unified workflow for complete site scraping
- Add advanced options for controlling the scraping process
- Enhance progress reporting with estimated time remaining and statistics

**Expected Output:** An enhanced management command with URL discovery and tagging capabilities

## Step 6: Develop data import functionality
**Tasks:**
- Create functions to map extracted data to Django models
- Implement creation of LabEquipmentPage instances
- Handle image downloads and gallery creation
- Map specifications to the appropriate models
- Implement tagging based on product categories and features
- Add data validation to ensure data integrity
- Create mechanisms to update existing products when needed

**Expected Output:** Data import module that creates or updates Django models from scraped data

## Step 7: Implement categorization
**Tasks:**
- Analyze triadscientific.com's category structure
- Map triadscientific.com categories to the system's TagCategory model
- Create logic to assign appropriate tags to products based on their categories
- Implement tag cleanup to avoid duplicate tags
- Create a mapping of manufacturer names for consistent tagging

**Expected Output:** Category mapping and tagging implementation

## Step 8: Test and optimize scraper
**Tasks:**
- Develop tests for URL discovery process
- Develop tests for data extraction process
- Test scraper on a sample of products from different categories
- Optimize scraper for performance
- Add rate limiting to avoid overloading the website
- Implement error recovery mechanisms
- Create detailed logs for troubleshooting

**Expected Output:** Testing suite and optimized scraper implementation

## Step 9: Document implementation
**Tasks:**
- Document the YAML configuration structure
- Document the management command usage
- Create examples of common scraping tasks
- Document error handling and recovery procedures
- Document how to extend the scraper for future changes

**Expected Output:** Comprehensive documentation for the triadscientific.com scraper

This detailed plan provides a structured approach to implementing the triadscientific.com scraper, with each step building on the previous ones and clear deliverables defined for each phase. The implementation will be modular and follow the existing architecture of the system while addressing the specific requirements of the triadscientific.com website.


# Detailed Breakdown of Important Project Files

The following is a breakdown of the important files in this project. As you are working, if you create or visit files that you believe are "important" in some way (your discretion) you should add them and an explanation of what they do to this list; you can also update and expand existing file descriptions.

## Core Scraping Framework

### Selector System
- **`apps/scrapers/Selectors.py`**: The legacy monolithic file containing all selector implementations. While deprecated in favor of the modular structure, it still serves as a reference.
- **`apps/scrapers/selectors/base.py`**: Defines the fundamental classes like `Selected`, `SelectedType`, and `Selector` that form the core of the scraping framework.
- **`apps/scrapers/selectors/__init__.py`**: Exports the selector classes for easy importing throughout the project.
- **`apps/scrapers/selectors/css_selector.py`**: Implements selectors for finding elements using CSS selectors.
- **`apps/scrapers/selectors/html_selector.py`**: Extracts HTML content from elements.
- **`apps/scrapers/selectors/text_selector.py`**: Extracts text content from elements.
- **`apps/scrapers/selectors/attr_selector.py`**: Extracts attributes from elements.
- **`apps/scrapers/selectors/for_each_selector.py`**: Applies selectors to each element in a collection.
- **`apps/scrapers/selectors/zip_selector.py`**: Combines keys and values into a dictionary.
- **`apps/scrapers/selectors/mapping_selector.py`**: Maps extracted content to defined structure.
- **`apps/scrapers/selectors/series_selector.py`**: Applies a sequence of selectors in order.
- **`apps/scrapers/selectors/split_selector.py`**: Splits content based on a delimiter.
- **`apps/scrapers/selectors/file_selector.py`**: Loads selector definitions from YAML files.

### Scraper Implementation
- **`apps/scrapers/Scrapers.py`**: A wrapper around the selector system that handles loading configurations and applying them to URLs.
- **`apps/scrapers/utils/image_downloader.py`**: Helper for downloading and processing images from scraped URLs.

### AirScience Scraper Configuration
- **`apps/scrapers/airscience-yamls/mapping.yaml`**: Main configuration file that references other YAML files.
- **`apps/scrapers/airscience-yamls/name.yaml`**: Extracts product names.
- **`apps/scrapers/airscience-yamls/short_description.yaml`**: Extracts product summaries.
- **`apps/scrapers/airscience-yamls/full_description.yaml`**: Extracts detailed product descriptions.
- **`apps/scrapers/airscience-yamls/imgs.yaml`**: Extracts product images.
- **`apps/scrapers/airscience-yamls/models.yaml`**: Extracts product model information.
- **`apps/scrapers/airscience-yamls/spec_groups.yaml`**: Extracts technical specifications.
- **`apps/scrapers/airscience-yamls/categories.yaml`**: Extracts product categories.
- **`apps/scrapers/airscience-yamls/applications.yaml`**: Extracts application information.

### Triad Scientific Scraper Configuration [In Development]
- **`apps/scrapers/triadscientific-yamls/`**: Directory for Triad Scientific YAML selectors
- **`apps/scrapers/triadscientific-yamls/mapping.yaml`**: Main configuration file that references other YAML files
- **`apps/scrapers/triadscientific-yamls/name.yaml`**: Extracts product names
- **`apps/scrapers/triadscientific-yamls/short_description.yaml`**: Extracts product summaries
- **`apps/scrapers/triadscientific-yamls/full_description.yaml`**: Extracts detailed product descriptions
- **`apps/scrapers/triadscientific-yamls/imgs.yaml`**: Extracts product images
- **`apps/scrapers/triadscientific-yamls/models.yaml`**: Extracts product model information
- **`apps/scrapers/triadscientific-yamls/specs_groups.yaml`**: Extracts technical specifications
- **`apps/scrapers/triadscientific-yamls/step4_summary.md`**: Summary of Django integration implementation
- **`apps/scrapers/triadscientific-yamls/import_command_docs.md`**: Documentation for the import command

## Management Commands

- **`apps/scrapers/management/commands/import_airscience.py`**: Command for scraping and importing AirScience products.
- **`apps/scrapers/management/commands/scrape_page.py`**: Generic command for scraping a single page.
- **`apps/scrapers/management/commands/import_triadscientific.py`**: Command for scraping and importing Triad Scientific products.

## Data Models

- **`apps/base_site/models.py`**: Contains the Django models for storing product data:
  - `LabEquipmentPage`: Main model for product pages
  - `EquipmentModel`: Model for equipment variants/models
  - `SpecGroup`: Grouping for technical specifications
  - `Spec`: Individual technical specifications
  - `LabEquipmentGalleryImage`: Product images

## Tagging System

- **`apps/categorized_tags/models.py`**: Implements the tagging system for product categorization:
  - `TagCategory`: Categories for tags (e.g., "Type", "Application", "Manufacturer")
  - `CategorizedTag`: Tags within categories
  - `CategorizedPageTag`: Links between pages and tags

## Project Configuration

- **`config/`**: Directory containing Django project settings.
- **`manage.py`**: Django management script for running commands.
- **`requirements.txt`**: Python package dependencies.

## Utility Scripts

- **`check_tag_db.py`**: Script for verifying tag database integrity.
- **`check_tags.py`**: Script for checking tag usage and consistency.
- **`check_urls.py`**: Script for validating URLs in the database.
- **`check_page_tag.py`**: Script for checking page tagging.


This breakdown covers the most important files you'll need to understand and modify to implement the triadscientific.com scraper. The implementation will primarily involve creating new YAML configuration files similar to the AirScience ones, and potentially a new management command specific to triadscientific.com.
