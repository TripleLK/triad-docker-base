"""
Django Management Command to Test Interactive Selector

Created by: Phoenix Velocity
Date: 2025-01-08
Project: Triad Docker Base
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.content_extractor.models import ExtractionProject, AnalyzedPage, ContentSelector
from apps.content_extractor.selectors.interactive_selector import InteractiveSelector
import json
import time


class Command(BaseCommand):
    help = 'Test the interactive selector system with a sample website'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            type=str,
            default='https://httpbin.org/html',
            help='URL to test with (default: httpbin.org/html)'
        )
        parser.add_argument(
            '--headless',
            action='store_true',
            help='Run browser in headless mode'
        )
        parser.add_argument(
            '--project-name',
            type=str,
            default='Test Project',
            help='Name for the test extraction project'
        )
    
    def handle(self, *args, **options):
        self.stdout.write("Starting Interactive Selector Test...")
        
        # Create or get test project
        project, created = ExtractionProject.objects.get_or_create(
            name=options['project_name'],
            defaults={
                'domain': options['url'],
                'description': 'Test project for interactive selector validation',
                'status': 'selecting'
            }
        )
        
        if created:
            self.stdout.write(f"Created new test project: {project.name}")
        else:
            self.stdout.write(f"Using existing project: {project.name}")
        
        # Initialize the interactive selector
        selector = InteractiveSelector(headless=options['headless'])
        
        try:
            # Test 1: Load page
            self.stdout.write("\n=== Test 1: Loading Page ===")
            if not selector.load_page(options['url']):
                self.stdout.write(self.style.ERROR("Failed to load page"))
                return
            
            page_info = selector.get_page_info()
            self.stdout.write(f"Page loaded successfully:")
            self.stdout.write(f"  Title: {page_info.get('title', 'N/A')}")
            self.stdout.write(f"  URL: {page_info.get('url', 'N/A')}")
            self.stdout.write(f"  HTML length: {page_info.get('page_source_length', 0)} chars")
            
            # Store page in database
            analyzed_page, created = AnalyzedPage.objects.get_or_create(
                project=project,
                url=options['url'],
                defaults={
                    'title': page_info.get('title', ''),
                    'original_html': selector.driver.page_source if selector.driver else '',
                    'processed_dom': {},  # We're not using DOM conversion anymore
                    'content_hash': 'test_hash'
                }
            )
            
            if not options['headless']:
                # Test 2: Interactive selection
                self.stdout.write("\n=== Test 2: Interactive Selection ===")
                self.stdout.write("Browser window should be open. Testing selection mode...")
                
                # Start selection for title
                self.stdout.write("Starting selection mode for 'title'...")
                if selector.start_selection('title'):
                    self.stdout.write("Selection mode started. Check the browser:")
                    self.stdout.write("  - You should see a blue instruction box")
                    self.stdout.write("  - Hover over elements to see highlighting")
                    self.stdout.write("  - Click elements to select them")
                    self.stdout.write("  - Click 'Done' when finished")
                    
                    # Wait for user interaction
                    input("\nPress Enter when you've finished selecting elements...")
                    
                    # Get selections
                    selections = selector.stop_selection()
                    self.stdout.write(f"\nCaptured {len(selections)} selections:")
                    
                    for i, selection in enumerate(selections, 1):
                        self.stdout.write(f"\nSelection {i}:")
                        self.stdout.write(f"  Label: {selection.get('label', 'N/A')}")
                        self.stdout.write(f"  XPath: {selection.get('xpath', 'N/A')}")
                        self.stdout.write(f"  CSS: {selection.get('cssSelector', 'N/A')}")
                        self.stdout.write(f"  Text: {selection.get('text', 'N/A')[:100]}...")
                        self.stdout.write(f"  Tag: {selection.get('tagName', 'N/A')}")
                        
                        # Store selector in database
                        content_selector, created = ContentSelector.objects.get_or_create(
                            project=project,
                            label=f"{selection.get('label', 'unknown')}_{i}",
                            defaults={
                                'xpath': selection.get('xpath', ''),
                                'css_selector': selection.get('cssSelector', ''),
                                'confidence_score': 1.0,
                                'created_by_human': True
                            }
                        )
                        content_selector.pages_matched.add(analyzed_page)
                        
                        if created:
                            self.stdout.write(f"  ✓ Saved to database as: {content_selector.label}")
                    
                    # Test 3: Validation of selectors
                    self.stdout.write("\n=== Test 3: Selector Validation ===")
                    for selection in selections:
                        xpath = selection.get('xpath')
                        if xpath:
                            try:
                                elements = selector.driver.find_elements("xpath", xpath)
                                self.stdout.write(f"XPath '{xpath}' matches {len(elements)} elements")
                                if elements:
                                    text = elements[0].text[:50]
                                    self.stdout.write(f"  First match text: '{text}'...")
                            except Exception as e:
                                self.stdout.write(f"XPath validation failed: {e}")
                else:
                    self.stdout.write(self.style.ERROR("Failed to start selection mode"))
            else:
                self.stdout.write("\n=== Headless Mode ===")
                self.stdout.write("Running in headless mode - skipping interactive selection")
                self.stdout.write("Page loaded successfully, basic functionality confirmed")
            
            # Test 4: Database verification
            self.stdout.write("\n=== Test 4: Database Verification ===")
            self.stdout.write(f"Project: {project.name}")
            self.stdout.write(f"  Pages: {project.pages.count()}")
            self.stdout.write(f"  Selectors: {project.selectors.count()}")
            
            for selector_obj in project.selectors.all():
                self.stdout.write(f"  - {selector_obj.label}: {selector_obj.pages_matched.count()} pages matched")
            
            self.stdout.write(self.style.SUCCESS("\n✓ Interactive Selector Test Complete!"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Test failed with error: {e}"))
            import traceback
            self.stdout.write(traceback.format_exc())
        
        finally:
            # Clean up
            selector.close()
            self.stdout.write("Browser closed.")
    
    def get_version(self):
        return "1.0.0" 