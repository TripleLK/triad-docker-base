"""
Command Line Interface for Content Extractor App

Provides CLI access to the selenium-based content extraction functionality.

Created by: Quantum Bear
Date: 2025-01-22
Project: Triad Docker Base
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path

from .app import ContentExtractorApp

logger = logging.getLogger(__name__)


class ContentExtractorCLI:
    """Command line interface for the content extractor."""
    
    def __init__(self):
        self.app = None
    
    def run(self, args=None):
        """Main entry point for CLI execution."""
        parser = self.create_parser()
        args = parser.parse_args(args)
        
        # Set up logging level
        if args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        elif args.quiet:
            logging.getLogger().setLevel(logging.WARNING)
        else:
            logging.getLogger().setLevel(logging.INFO)
        
        try:
            return self.execute_command(args)
        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
            return 1
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return 1
    
    def create_parser(self):
        """Create argument parser for CLI."""
        parser = argparse.ArgumentParser(
            description="Extract content from web pages using selenium",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s extract https://example.com/product --config config.json
  %(prog)s extract https://example.com/product --output extracted_data.json
  %(prog)s create-config --output sample_config.json
            """
        )
        
        # Global options
        parser.add_argument('-v', '--verbose', action='store_true',
                          help='Enable verbose logging')
        parser.add_argument('-q', '--quiet', action='store_true',
                          help='Suppress info messages')
        parser.add_argument('--headless', action='store_true', default=True,
                          help='Run browser in headless mode (default)')
        parser.add_argument('--gui', action='store_true',
                          help='Show browser window (not headless)')
        
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Extract command
        extract_parser = subparsers.add_parser('extract', help='Extract content from a web page')
        extract_parser.add_argument('url', help='URL to extract content from')
        extract_parser.add_argument('--config', '-c', 
                                  help='JSON configuration file with field mappings')
        extract_parser.add_argument('--output', '-o', default='extracted_content.json',
                                  help='Output JSON file (default: extracted_content.json)')
        extract_parser.add_argument('--session-id', 
                                  help='Custom session ID for grouping extractions')
        
        # Create config command
        config_parser = subparsers.add_parser('create-config', help='Create sample configuration file')
        config_parser.add_argument('--output', '-o', default='extractor_config.json',
                                 help='Output configuration file (default: extractor_config.json)')
        config_parser.add_argument('--template', choices=['basic', 'lab-equipment', 'product'],
                                 default='lab-equipment',
                                 help='Configuration template to use')
        
        # Validate config command
        validate_parser = subparsers.add_parser('validate', help='Validate configuration file')
        validate_parser.add_argument('config', help='Configuration file to validate')
        
        return parser
    
    def execute_command(self, args):
        """Execute the specified command."""
        if args.command == 'extract':
            return self.extract_content(args)
        elif args.command == 'create-config':
            return self.create_config(args)
        elif args.command == 'validate':
            return self.validate_config(args)
        else:
            print("No command specified. Use --help for usage information.")
            return 1
    
    def extract_content(self, args):
        """Extract content from the specified URL."""
        headless = args.headless and not args.gui
        
        print(f"Extracting content from: {args.url}")
        print(f"Browser mode: {'headless' if headless else 'visible'}")
        
        try:
            with ContentExtractorApp(headless=headless, config_file=args.config) as app:
                self.app = app
                
                # Load configuration
                if args.config:
                    if not os.path.exists(args.config):
                        print(f"Error: Configuration file not found: {args.config}")
                        return 1
                    print(f"Using configuration: {args.config}")
                else:
                    print("Warning: No configuration provided, using default selectors")
                    app.config = self.get_default_config()
                
                # Extract content
                extracted_data = app.extract_content(args.url)
                
                if not extracted_data:
                    print("No content was extracted")
                    return 1
                
                # Display results
                print(f"\nExtracted {len(extracted_data)} fields:")
                for field_name, field_data in extracted_data.items():
                    content = field_data.get('content', '')
                    preview = content[:100] + '...' if len(content) > 100 else content
                    status = '✓' if content else '✗'
                    print(f"  {status} {field_name}: {preview}")
                
                # Save output
                if app.save_export_file(args.output, args.session_id):
                    print(f"\nData exported to: {args.output}")
                    print(f"Session ID: {app.session_id}")
                    print("Ready for upload to Django admin")
                    return 0
                else:
                    print("Failed to save export file")
                    return 1
                    
        except Exception as e:
            print(f"Extraction failed: {e}")
            logger.exception("Extraction error details")
            return 1
    
    def create_config(self, args):
        """Create a sample configuration file."""
        config = self.get_config_template(args.template)
        
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            print(f"Created {args.template} configuration template: {args.output}")
            print(f"Fields included: {list(config['fields'].keys())}")
            print("Edit the XPath and CSS selectors to match your target website")
            return 0
            
        except Exception as e:
            print(f"Failed to create configuration: {e}")
            return 1
    
    def validate_config(self, args):
        """Validate a configuration file."""
        try:
            with open(args.config, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Basic validation
            errors = []
            
            if not isinstance(config, dict):
                errors.append("Configuration must be a JSON object")
            
            if 'fields' not in config:
                errors.append("Configuration must contain 'fields' section")
            elif not isinstance(config['fields'], dict):
                errors.append("'fields' must be a JSON object")
            else:
                for field_name, field_config in config['fields'].items():
                    if not isinstance(field_config, dict):
                        errors.append(f"Field '{field_name}' must be a JSON object")
                        continue
                    
                    if not field_config.get('xpath') and not field_config.get('css_selector'):
                        errors.append(f"Field '{field_name}' must have either 'xpath' or 'css_selector'")
            
            if errors:
                print("Configuration validation failed:")
                for error in errors:
                    print(f"  ✗ {error}")
                return 1
            else:
                print("✓ Configuration is valid")
                field_count = len(config['fields'])
                print(f"✓ Found {field_count} field configuration(s)")
                return 0
                
        except json.JSONDecodeError as e:
            print(f"Invalid JSON: {e}")
            return 1
        except FileNotFoundError:
            print(f"Configuration file not found: {args.config}")
            return 1
        except Exception as e:
            print(f"Validation error: {e}")
            return 1
    
    def get_default_config(self):
        """Get default configuration for basic extraction."""
        return {
            "name": "Basic Content Extractor",
            "fields": {
                "title": {
                    "xpath": "//h1",
                    "css_selector": "h1",
                    "description": "Page title"
                },
                "description": {
                    "xpath": "//meta[@name='description']/@content",
                    "css_selector": "meta[name='description']",
                    "description": "Meta description"
                }
            }
        }
    
    def get_config_template(self, template_name):
        """Get configuration template by name."""
        templates = {
            'basic': {
                "name": "Basic Content Extractor",
                "description": "Extract basic page elements",
                "fields": {
                    "title": {
                        "xpath": "//h1",
                        "css_selector": "h1",
                        "description": "Page title"
                    },
                    "description": {
                        "xpath": "//p[1]",
                        "css_selector": "p:first-of-type",
                        "description": "First paragraph"
                    }
                }
            },
            'lab-equipment': {
                "name": "Lab Equipment Extractor",
                "description": "Extract lab equipment details from product pages",
                "fields": {
                    "title": {
                        "xpath": "//h1[contains(@class, 'product-title') or contains(@class, 'entry-title')]",
                        "css_selector": "h1.product-title, h1.entry-title, .product-name h1",
                        "description": "Product title"
                    },
                    "short_description": {
                        "xpath": "//div[contains(@class, 'product-summary')]//p[1]",
                        "css_selector": ".product-summary p, .short-description p",
                        "description": "Brief product description"
                    },
                    "full_description": {
                        "xpath": "//div[contains(@class, 'product-description')]",
                        "css_selector": ".product-description, .product-details",
                        "description": "Full product description"
                    },
                    "features": {
                        "xpath": "//div[contains(@class, 'features')]//ul",
                        "css_selector": ".features ul, .highlights ul",
                        "description": "Product features list"
                    },
                    "specifications": {
                        "xpath": "//div[contains(@class, 'specifications')]//table",
                        "css_selector": ".specifications table, .specs table",
                        "description": "Technical specifications"
                    }
                }
            },
            'product': {
                "name": "Generic Product Extractor",
                "description": "Extract product information from e-commerce pages",
                "fields": {
                    "title": {
                        "xpath": "//h1[@class='product-title' or @class='product-name']",
                        "css_selector": "h1.product-title, h1.product-name",
                        "description": "Product title"
                    },
                    "price": {
                        "xpath": "//span[contains(@class, 'price') or contains(@class, 'cost')]",
                        "css_selector": ".price, .cost, .product-price",
                        "description": "Product price"
                    },
                    "description": {
                        "xpath": "//div[@class='product-description']",
                        "css_selector": ".product-description",
                        "description": "Product description"
                    },
                    "availability": {
                        "xpath": "//span[contains(@class, 'stock') or contains(@class, 'availability')]",
                        "css_selector": ".stock, .availability, .in-stock",
                        "description": "Stock availability"
                    }
                }
            }
        }
        
        return templates.get(template_name, templates['basic'])


def main():
    """Main entry point for command line usage."""
    cli = ContentExtractorCLI()
    return cli.run()


if __name__ == '__main__':
    sys.exit(main()) 