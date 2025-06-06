# Briefing for Step 3d - Simplifying Specification Extraction for Triad Scientific

## Overview of Step 3c Progress

In Step 3c, we made progress in understanding the type flow issues that were affecting specification extraction:

1. We identified that a key issue was type mismatches between selectors in the extraction chain
2. We discovered that Triad Scientific product specifications are embedded inconsistently in the description text
3. We created a test YAML file (`specs_test.yaml`) to experiment with different extraction approaches
4. We found that proper type conversion with `value_to_single_selector` is critical when transitioning between VALUE and SINGLE types

Despite these insights, we could not achieve a fully functional specification extractor that handles all the different specification formats used across product pages.

## Your Task: Simplified Specification Extraction

Your task for Step 3d is to create a simplified approach to specification extraction that focuses only on the most common and reliable pattern. Instead of trying to handle all possible formats, create a specification extractor that:

1. **Only extracts specifications in "Key: Value" format** (with a colon separator)
2. **Focuses on newline-separated specs** (via `<br>` tags in the description)
3. **Returns an empty result if no specs match** the expected format (rather than attempting complex pattern matching)

### Implementation Approach

1. **Create a new implementation of `specs_groups.yaml`** that:
   - Extracts the product description paragraph
   - Replaces `<br>` tags with newlines
   - Splits the text by newlines
   - Only extracts specifications in "Key: Value" format
   - Uses appropriate type conversions to avoid type mismatch errors
   - Returns empty results if no specifications are found

2. **Test with multiple product pages** to ensure the simplified approach works for a variety of products

3. **Document the type flow** in the YAML file with detailed comments explaining each step and its expected inputs/outputs

### Technical Considerations

1. **Selector Chain Types**: Pay careful attention to the type of data at each step:
   - `CSSSelector` → returns a SINGLE type
   - `TextSelector/HtmlSelector` → converts SINGLE to VALUE type
   - `SplitSelector` → converts VALUE to MULTIPLE of VALUEs
   - `ForEachSelector` → processes each VALUE in a MULTIPLE
   - `value_to_single_selector` → converts VALUE to SINGLE (needed before using many selectors)

2. **Type Mismatches**: The most common error is "SeriesSelector expects input of type SINGLE, but received VALUE" - ensure proper type conversion at each step

3. **System Compatibility**: Any changes should not affect the working AirScience selectors

### Sample Product URLs for Testing

Test your implementation on these product pages with varying specification formats:

1. FTIR/Spectroscopy (has "Key: Value" and "Key is Value" formats): 
   ```
   http://www.triadscientific.com/en/products/ftir-ir-and-near-ir-spectroscopy/946/mattson-ati-genesis-series-ftir-with-software/249015
   ```

2. HPLC Component (mainly "Key: Value" format): 
   ```
   http://www.triadscientific.com/en/products/hplc-systems-and-components/1095/hybrid-biocompatible-peek-coated-fused-silica-tubing-1-16-od-x-250-um-id-x-5m-length/265048
   ```

3. Gas Chromatography (minimal specifications): 
   ```
   http://www.triadscientific.com/en/products/gas-chromatography/1090/perkin-elmer-clarus-500-gc-gas-chromatograph-with-autosampler/256909
   ```

### Testing Your Implementation

Test your implementation using the Django management command:

```
python manage.py scrape_page --config apps/scrapers/triadscientific-yamls/mapping.yaml [URL]
```

You can also create a test file (like `specs_test.yaml`) to experiment with different approaches before modifying the main `specs_groups.yaml` file.

## Expected Output

By the end of Step 3d, you should deliver:

1. An updated `specs_groups.yaml` file that reliably extracts specifications in "Key: Value" format
2. Documentation of your implementation approach and the type flow
3. Test results showing successful extraction from multiple product pages
4. Guidance for Step 4 based on your findings

Remember: It's better to have a simple extractor that works reliably for the most common pattern than a complex one that breaks on edge cases. Focus on making it work for "Key: Value" format specifications and gracefully handle cases where no specifications match this pattern. 