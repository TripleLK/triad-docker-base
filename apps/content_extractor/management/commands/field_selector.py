"""
Field-Specific Content Selector Management Command

Enhanced command for testing field-specific content selection for LabEquipmentPage model.
Supports floating field menu and field-specific selection workflow.

Created by: Quantum Catalyst
Date: 2025-01-08
Project: Triad Docker Base
"""

import json
import time
from typing import Dict, List
from django.core.management.base import BaseCommand, CommandError
from apps.content_extractor.selectors.interactive_selector import InteractiveSelector


class Command(BaseCommand):
    """Management command for field-specific content selection testing"""
    
    help = 'Test field-specific content selection with LabEquipmentPage fields'

    def add_arguments(self, parser):
        parser.add_argument(
            'url',
            type=str,
            help='URL to test field selection on'
        )
        parser.add_argument(
            '--headless',
            action='store_true',
            help='Run browser in headless mode (no visual interface)'
        )
        parser.add_argument(
            '--field',
            type=str,
            help='Specific field to test (bypasses field menu)'
        )
        parser.add_argument(
            '--output',
            type=str,
            help='JSON file to save field selections to'
        )
        parser.add_argument(
            '--timeout',
            type=int,
            default=300,
            help='Maximum time to wait for user selections (seconds)'
        )
        parser.add_argument(
            '--show-status',
            action='store_true',
            help='Show field completion status at the end'
        )

    def handle(self, *args, **options):
        """Execute the field selection test"""
        url = options['url']
        headless = options['headless']
        specific_field = options['field']
        output_file = options['output']
        timeout = options['timeout']
        show_status = options['show_status']

        self.stdout.write(
            self.style.SUCCESS(f'🚀 Starting field-specific content selection test')
        )
        self.stdout.write(f'URL: {url}')
        self.stdout.write(f'Mode: {"Headless" if headless else "Visual"}')
        
        if specific_field:
            self.stdout.write(f'Target Field: {specific_field}')

        # Initialize selector
        selector = InteractiveSelector(headless=headless)
        
        try:
            # Load page
            self.stdout.write('\n📄 Loading page...')
            if not selector.load_page(url):
                raise CommandError(f'Failed to load page: {url}')
            
            self.stdout.write(self.style.SUCCESS('✅ Page loaded successfully'))
            
            # Get page info
            page_info = selector.get_page_info()
            self.stdout.write(f'Page Title: {page_info.get("title", "Unknown")}')
            self.stdout.write(f'Page Source Length: {page_info.get("page_source_length", 0):,} characters')

            if specific_field:
                # Test specific field
                self._test_specific_field(selector, specific_field, timeout)
            else:
                # Show field menu and let user choose
                self._test_field_menu_workflow(selector, timeout)
            
            # Get final results
            all_selections = selector.get_all_field_selections()
            total_selections = sum(len(selections) for selections in all_selections.values())
            
            self.stdout.write(f'\n📊 Selection Results:')
            self.stdout.write(f'Fields with selections: {len(all_selections)}')
            self.stdout.write(f'Total selections: {total_selections}')
            
            # Show field breakdown
            for field_name, selections in all_selections.items():
                if selections:
                    self.stdout.write(f'  {field_name}: {len(selections)} selections')
            
            # Show completion status if requested
            if show_status:
                self._show_completion_status(selector)
            
            # Save results if output file specified
            if output_file:
                self._save_results(all_selections, output_file, page_info)
            
            self.stdout.write(self.style.SUCCESS('\n✅ Field selection test completed successfully'))

        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\n⚠️ Test interrupted by user'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Test failed: {e}'))
            raise CommandError(f'Field selection test failed: {e}')
        finally:
            # Clean up
            selector.close()
            self.stdout.write('🧹 Browser closed')

    def _test_specific_field(self, selector: InteractiveSelector, field_name: str, timeout: int):
        """Test selection for a specific field"""
        self.stdout.write(f'\n🎯 Testing field-specific selection for: {field_name}')
        
        # Validate field
        valid_fields = [field['name'] for field in selector.FIELD_OPTIONS]
        if field_name not in valid_fields:
            raise CommandError(f'Invalid field: {field_name}. Valid fields: {valid_fields}')
        
        # Start field selection
        if not selector.start_field_selection(field_name):
            raise CommandError(f'Failed to start selection for field: {field_name}')
        
        self.stdout.write(f'✅ Field selection mode started for: {field_name}')
        self.stdout.write('👆 Click elements on the page to select them for this field')
        self.stdout.write('🔄 When done, close the instruction box or press Ctrl+C')
        
        # Wait for selections
        self._wait_for_selections(selector, field_name, timeout)

    def _test_field_menu_workflow(self, selector: InteractiveSelector, timeout: int):
        """Test the full field menu workflow"""
        self.stdout.write('\n📋 Testing field menu workflow')
        
        # Show field menu
        if not selector.show_field_menu():
            raise CommandError('Failed to show field selection menu')
        
        self.stdout.write('✅ Field selection menu displayed')
        self.stdout.write('👆 Choose a field from the floating menu, then select content')
        self.stdout.write('🔄 When done, close menus or press Ctrl+C')
        
        # Wait for selections
        self._wait_for_selections(selector, None, timeout)

    def _wait_for_selections(self, selector: InteractiveSelector, field_name: str, timeout: int):
        """Wait for user to make selections"""
        start_time = time.time()
        last_count = 0
        
        while time.time() - start_time < timeout:
            try:
                time.sleep(2)  # Check every 2 seconds
                
                if field_name:
                    # Monitor specific field
                    selections = selector.get_field_selections(field_name)
                    count = len(selections)
                    if count != last_count:
                        self.stdout.write(f'📈 {field_name}: {count} selections')
                        last_count = count
                else:
                    # Monitor all fields
                    all_selections = selector.get_all_field_selections()
                    total_count = sum(len(selections) for selections in all_selections.values())
                    if total_count != last_count:
                        active_fields = [f for f, s in all_selections.items() if s]
                        self.stdout.write(f'📈 Total: {total_count} selections across {len(active_fields)} fields')
                        last_count = total_count
                        
            except KeyboardInterrupt:
                break
        
        if time.time() - start_time >= timeout:
            self.stdout.write(self.style.WARNING(f'⏰ Timeout reached ({timeout}s)'))

    def _show_completion_status(self, selector: InteractiveSelector):
        """Display field completion status"""
        self.stdout.write('\n📊 Field Completion Status:')
        
        status = selector.get_field_completion_status()
        
        # Group by completion status
        completed_fields = []
        incomplete_fields = []
        ready_for_generalization = []
        
        for field_name, field_status in status.items():
            if field_status['is_complete']:
                completed_fields.append((field_name, field_status))
                if field_status['ready_for_generalization']:
                    ready_for_generalization.append((field_name, field_status))
            else:
                incomplete_fields.append((field_name, field_status))
        
        # Display completed fields
        if completed_fields:
            self.stdout.write(f'\n✅ Completed Fields ({len(completed_fields)}):')
            for field_name, field_status in completed_fields:
                field_type = "Multi-value" if field_status['is_multi_value'] else "Single"
                self.stdout.write(f'  {field_name}: {field_status["selection_count"]} selections ({field_type})')
        
        # Display ready for generalization
        if ready_for_generalization:
            self.stdout.write(f'\n🎯 Ready for Generalization ({len(ready_for_generalization)}):')
            for field_name, field_status in ready_for_generalization:
                self.stdout.write(f'  {field_name}: {field_status["selection_count"]} examples')
        
        # Display incomplete fields
        if incomplete_fields:
            self.stdout.write(f'\n⏳ Incomplete Fields ({len(incomplete_fields)}):')
            for field_name, field_status in incomplete_fields:
                field_type = "Multi-value" if field_status['is_multi_value'] else "Single"
                self.stdout.write(f'  {field_name}: No selections ({field_type})')

    def _save_results(self, all_selections: Dict[str, List], output_file: str, page_info: Dict):
        """Save selection results to JSON file"""
        self.stdout.write(f'\n💾 Saving results to: {output_file}')
        
        # Prepare data for saving
        results = {
            'page_info': page_info,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'field_selections': all_selections,
            'summary': {
                'total_fields_with_selections': len([f for f, s in all_selections.items() if s]),
                'total_selections': sum(len(selections) for selections in all_selections.values()),
                'fields_by_type': {
                    'single_value': [],
                    'multi_value': []
                }
            }
        }
        
        # Categorize fields by type
        selector = InteractiveSelector()  # Just for field info
        for field in selector.FIELD_OPTIONS:
            field_name = field['name']
            if field_name in all_selections and all_selections[field_name]:
                field_category = 'multi_value' if field['type'] == 'multi-value' else 'single_value'
                results['summary']['fields_by_type'][field_category].append({
                    'field_name': field_name,
                    'selection_count': len(all_selections[field_name]),
                    'description': field['description']
                })
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            self.stdout.write(self.style.SUCCESS(f'✅ Results saved to {output_file}'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Failed to save results: {e}')) 