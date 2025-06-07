from apps.ai_processing.utils import extract_universal_specifications
import json

# The input test data
test_data = {
  "title": "Purair® ADVANCED Ductless Fume Hoods",
  "short_description": "The Purair® ADVANCED Series ductless fume hoods provide high operator protection to fume and particle hazards, and are designed to protect the user and the environment from hazardous vapors.",
  "full_description": "<p>The Purair® ADVANCED Series ductless fume hoods are available in 7 standard sizes in metal or polypropylene construction. This Series of high-efficiency products is designed to protect the user and the environment from hazardous vapors generated on the work surface.</p>",
  "source_url": "https://www.airscience.com/",
  "slug": "purair-advanced-ductless-fume-hoods",
  "tags": [
    "Manufacturer: Air Science",
    "Product Category: Laboratory Equipment",
    "Product Application: Laboratory"
  ],
  "models": [
    {
      "name": "P10-XT-A",
      "specifications": [
        {
          "name": "Dimensions & Weights",
          "specs": [
            {"key": "Internal Height", "value": "38\" | 965 mm"},
            {"key": "External Width", "value": "30\" | 762 mm"},
            {"key": "External Depth", "value": "27.375\" | 695 mm"},
            {"key": "External Height", "value": "53\" | 1346 mm"},
            {"key": "Shipping Width", "value": "50\" | 1270 mm"},
            {"key": "Shipping Depth", "value": "40\" | 1016 mm"},
            {"key": "Net Weight", "value": "111 lbs | 50 kg"},
            {"key": "Shipping Weight", "value": "175 lbs | 79 kg"}
          ]
        },
        {
          "name": "Construction",
          "specs": [
            {"key": "Cabinet Style", "value": "Tall"},
            {"key": "Construction", "value": "Epoxy-coated Steel"}
          ]
        },
        {
          "name": "Protection & Compliance",
          "specs": [
            {"key": "OSHA", "value": "OSHA Standard -29 CFR, Safety and Health Regulations for General Industry, 1910.1450"},
            {"key": "Environmental", "value": "ISO 14001 : 2015; ENERGY STAR® Partner"},
            {"key": "Quality", "value": "ISO 9001 : 2015"}
          ]
        },
        {
          "name": "Options & Accessories",
          "specs": [
            {"key": "Advanced Controller", "value": "P10-XT-A-ADVP"},
            {"key": "Base Cabinet, Fixed (Metal)", "value": "CART-MCC-30"},
            {"key": "Base Cabinet, Fixed (Polypropylene)", "value": "CART-SSC-30"},
            {"key": "Base Stand, Mobile, with Casters", "value": "CART-30"},
            {"key": "Fire Safety Cabinet Base", "value": "CART-FSC-30"},
            {"key": "Monitair Controller", "value": "P10-XT-A-MONP"},
            {"key": "Polypropylene Construction", "value": "P10-XT-A-PP"}
          ]
        },
        {
          "name": "Airflow & Filtration",
          "specs": [
            {"key": "Airflow", "value": "Vertical"},
            {"key": "Airflow Direction", "value": "Upflow"},
            {"key": "Face Velocity", "value": "100"},
            {"key": "Main Filter", "value": "22 lbs each"},
            {"key": "Carbon Filter", "value": "1 x 11 lbs each"},
            {"key": "Biological Filter", "value": "HEPA / ULPA"}
          ]
        },
        {
          "name": "Electrical",
          "specs": [
            {"key": "Electrical Voltage", "value": "120V, 60Hz"},
            {"key": "NEMA Plug", "value": "5-15P"}
          ]
        },
        {
          "name": "Controls & Monitoring",
          "specs": [
            {"key": "Control", "value": "Electronic#Monitair"}
          ]
        }
      ]
    },
    {
      "name": "P10XL-XT-A",
      "specifications": [
        {
          "name": "Dimensions & Weights",
          "specs": [
            {"key": "Internal Height", "value": "38\" | 965 mm"},
            {"key": "External Width", "value": "34\" | 864 mm"},
            {"key": "External Depth", "value": "27.375\" | 695 mm"},
            {"key": "External Height", "value": "53\" | 1346 mm"},
            {"key": "Shipping Width", "value": "40\" | 1016 mm"},
            {"key": "Shipping Depth", "value": "40\" | 1016 mm"},
            {"key": "Net Weight", "value": "141 lbs | 64 kg"},
            {"key": "Shipping Weight", "value": "225 lbs | 102 kg"}
          ]
        },
        {
          "name": "Construction",
          "specs": [
            {"key": "Cabinet Style", "value": "Tall"},
            {"key": "Construction", "value": "Epoxy-coated Steel"}
          ]
        },
        {
          "name": "Protection & Compliance",
          "specs": [
            {"key": "OSHA", "value": "OSHA Standard -29 CFR, Safety and Health Regulations for General Industry, 1910.1450"},
            {"key": "Environmental", "value": "ISO 14001 : 2015; ENERGY STAR® Partner"},
            {"key": "Quality", "value": "ISO 9001 : 2015"}
          ]
        },
        {
          "name": "Options & Accessories",
          "specs": [
            {"key": "Advanced Controller", "value": "P10XL-XT-A-ADVP"},
            {"key": "Base Cabinet, Fixed (Metal)", "value": "CART-MCC-35"},
            {"key": "Base Cabinet, Fixed (Polypropylene)", "value": "CART-SSC-35"},
            {"key": "Base Stand, Mobile, with Casters", "value": "CART-35"},
            {"key": "Fire Safety Cabinet Base", "value": "CART-FSC-35"},
            {"key": "Monitair Controller", "value": "P10XL-XT-A-MONP"},
            {"key": "Polypropylene Construction", "value": "P10XL-XT-A-PP"}
          ]
        },
        {
          "name": "Airflow & Filtration",
          "specs": [
            {"key": "Airflow", "value": "Vertical"},
            {"key": "Airflow Direction", "value": "Upflow"},
            {"key": "Face Velocity", "value": "100"},
            {"key": "Main Filter", "value": "22 lbs each"},
            {"key": "Carbon Filter", "value": "1 x 11 lbs each"},
            {"key": "Biological Filter", "value": "HEPA / ULPA"}
          ]
        },
        {
          "name": "Electrical",
          "specs": [
            {"key": "Electrical Voltage", "value": "120V, 60Hz"},
            {"key": "NEMA Plug", "value": "5-15P"}
          ]
        },
        {
          "name": "Controls & Monitoring",
          "specs": [
            {"key": "Control", "value": "Electronic#Monitair"}
          ]
        }
      ]
    }
  ],
  "images": [
    "https://www.airscience.com/wp-content/uploads/2021/12/PDT_P10-XT_Left.png",
    "https://www.airscience.com/wp-content/uploads/2021/12/PDT_P15-XT_Left.png",
    "https://www.airscience.com/wp-content/uploads/2021/12/PDT_P20-XT.png",
    "https://www.airscience.com/wp-content/uploads/2021/12/PDT_P10-XT_Left.png"
  ],
  "specifications": [
    {
      "name": "External Dimensions",
      "specs": [
        {"key": "Model", "value": "P10-XT-A"},
        {"key": "Width", "value": "30\" | 762 mm"},
        {"key": "Depth", "value": "27.375\" | 695 mm"},
        {"key": "Height", "value": "53\" | 1346 mm"}
      ]
    },
    {
      "name": "Internal Dimensions",
      "specs": [
        {"key": "Model", "value": "P10-XT-A"},
        {"key": "Width", "value": "-"},
        {"key": "Depth", "value": "-"},
        {"key": "Height", "value": "38\" | 965 mm"}
      ]
    },
    {
      "name": "Filter Options",
      "specs": [
        {"key": "Formula", "value": "GP Plus!"},
        {"key": "Description", "value": "The most widely used filter in the range, primarily for solvent, organic and alcohol removal."}
      ]
    }
  ]
}

# Process the data
result = extract_universal_specifications(test_data)

# Count specifications before and after extraction
original_universal_specs_count = sum(len(section.get('specs', [])) for section in test_data['specifications'])
result_universal_specs_count = sum(len(section.get('specs', [])) for section in result['specifications'])

# Print results
print(f"BEFORE: Universal specs: {original_universal_specs_count}, Models: {len(test_data['models'])}")
print(f"AFTER: Universal specs: {result_universal_specs_count}, Models: {len(result['models'])}")

# Print all universal specifications sections
print("\nUniversal Specification Sections:")
for section in result['specifications']:
    print(f"\n{section['name']}")
    for spec in section['specs']:
        print(f"  {spec['key']}: {spec['value']}")

# Print each model's remaining specifications
for i, model in enumerate(result['models']):
    print(f"\nModel {i+1}: {model['name']}")
    if not model.get('specifications'):
        print("  No model-specific specifications remain")
        continue
    
    for section in model['specifications']:
        print(f"  {section['name']}")
        for spec in section['specs']:
            print(f"    {spec['key']}: {spec['value']}")

# Check which specs were moved to universal
print("\nSpecifications that were moved to universal level:")
universal_sections = {section['name']: {spec['key']: spec['value'] for spec in section['specs']} 
                     for section in result['specifications']}
original_sections = {section['name']: {spec['key']: spec['value'] for spec in section['specs']} 
                     for section in test_data['specifications']}

for section_name, specs in universal_sections.items():
    if section_name in original_sections:
        original_specs = original_sections[section_name]
        for key, value in specs.items():
            if key in original_specs:
                continue
            print(f"  {section_name} - {key}: {value} (moved to universal)")
    else:
        print(f"  {section_name} (new universal section)")
        for key, value in specs.items():
            print(f"    {key}: {value}") 