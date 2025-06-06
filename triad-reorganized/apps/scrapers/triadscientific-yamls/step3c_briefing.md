# Briefing for Step 3c - Fixing Specification Extraction for Triad Scientific Scraper

## Overview of Current Status

Steps 3 and 3b have made significant progress in implementing the Triad Scientific scraper:

1. YAML selectors have been created for all product information components:
   - Product name (`name.yaml`)
   - Images (`imgs.yaml`)
   - Short description (`short_description.yaml`) 
   - Full description (`full_description.yaml`)
   - Specifications (`specs_groups.yaml`)
   - Models (`models.yaml`)

2. The project has been successfully migrated from the monolithic `Selectors.py` to the new modular selector system in `apps.scrapers.selectors`.

3. Testing confirms that most selectors are working correctly:
   - Product name extraction works
   - Full description extraction works
   - Image extraction works
   - Similar AirScience selectors work correctly with the same system

## Current Issue: Specification Extraction

The main challenge remaining is with the extraction of technical specifications from product descriptions. Due to Triad Scientific's format, specifications are embedded within the product description text, separated by `<br>` tags. We've attempted to extract these using a series of selectors:

1. Parse the description text
2. Replace `<br>` tags with newlines
3. Split by newlines
4. Process each line using pattern matching for different specification formats

However, we're encountering a type mismatch error:

```
SeriesSelector type validation error: SeriesSelector expects input of type SINGLE, but received VALUE.
```

This indicates that in the processing chain, a selector is receiving data of type VALUE when it expects SINGLE.

## Your Task: Fix the Specification Extraction

Your primary task is to fix the specification extraction in `specs_groups.yaml` to address the type mismatch issue and ensure specifications are properly extracted. This involves:

1. **Analyze the Type Flow**: 
   - Review the selector chain in `specs_groups.yaml`
   - Identify where type mismatches occur
   - Adjust selectors to handle the appropriate types

2. **Improve Regex Patterns**:
   - Refine the regex patterns for extracting specifications
   - Ensure they handle the three main patterns identified ("Name: Value", "Name is Value", and pattern-based)

3. **Handle Type Conversions**:
   - Insert appropriate conversions between VALUE and SINGLE types where needed
   - Use appropriate selectors to convert between types (e.g., ValueToSingleSelector)

4. **Extensive Testing**:
   - Test with multiple product pages to validate the fixes
   - Ensure specifications are correctly extracted for each pattern type

## Sample Product URLs for Testing

Use these URLs to test your specification extraction fixes:

1. FTIR/Spectroscopy (uses "is" format): 
   ```
   http://www.triadscientific.com/en/products/ftir-ir-and-near-ir-spectroscopy/946/mattson-ati-genesis-series-ftir-with-software/249015
   ```

2. HPLC Component (uses ":" format): 
   ```
   http://www.triadscientific.com/en/products/hplc-systems-and-components/1095/hybrid-biocompatible-peek-coated-fused-silica-tubing-1-16-od-x-250-um-id-x-5m-length/265048
   ```

3. Atomic Absorption (mixed formats): 
   ```
   http://www.triadscientific.com/en/products/atomic-absorption/942/universal-xyz-autosampler-auroraa-s-revolutionary/250558
   ```

## Technical Reference

Here are some useful tools to address type conversion issues:

1. **ValueToSingleSelector**: Convert a VALUE type to a SINGLE type
2. **HtmlSelector**: Convert a SINGLE to VALUE with HTML content
3. **TextSelector**: Convert a SINGLE to VALUE with text content
4. **SplitSelector**: Split a VALUE string into a MULTIPLE of VALUEs

## Expected Output

By the end of Step 3c, you should deliver:

1. Updated `specs_groups.yaml` with fixed type handling
2. Documentation of the changes made and why they were necessary
3. Example output from testing showing successful specification extraction
4. Any recommendations for further improvements

Your work will complete the implementation of the product information extractors, allowing the project to proceed to Step 4 (creating the final mapping file and selectors). 