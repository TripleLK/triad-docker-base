"""
Site Field Selector Management Command

Enhanced field selector with site-specific selector storage and cross-page testing.
Supports saving selectors to database and testing them across multiple pages.

Created by: Crimson Phoenix
Date: 2025-01-08
Project: Triad Docker Base
"""

import time
import sys
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from apps.content_extractor.selectors.interactive_selector import InteractiveSelector
from apps.content_extractor.models import SiteFieldSelector, SelectorTestResult, FieldSelectionSession


class Command(BaseCommand):
    help = 'Enhanced field selector with site-specific storage and cross-page testing'

    def add_arguments(self, parser):
        parser.add_argument('url', type=str, help='URL to start field selection on')
        parser.add_argument('--headless', action='store_true', help='Run in headless mode')
        parser.add_argument('--timeout', type=int, default=60, help='Timeout in seconds')
        parser.add_argument('--session', type=str, help='Session name for tracking')
        parser.add_argument('--test-urls', nargs='+', help='Additional URLs to test selectors on')
        parser.add_argument('--show-saved', action='store_true', help='Show saved selectors for this domain')
        parser.add_argument('--test-all', action='store_true', help='Test all saved selectors on provided URLs')

    def handle(self, *args, **options):
        url = options['url']
        headless = options['headless']
        timeout = options['timeout']
        session_name = options['session'] or f"Session_{int(time.time())}"
        test_urls = options['test_urls'] or []
        show_saved = options['show_saved']
        test_all = options['test_all']

        self.stdout.write(f"🚀 Site Field Selector - Enhanced Mode")
        self.stdout.write(f"   URL: {url}")
        self.stdout.write(f"   Session: {session_name}")
        self.stdout.write(f"   Mode: {'Headless' if headless else 'Visual'}")

        # Initialize selector
        selector = InteractiveSelector(headless=headless, session_name=session_name)
        
        try:
            # Load the page
            self.stdout.write("\n📖 Loading page...")
            if not selector.load_page(url, timeout):
                raise CommandError(f"Failed to load page: {url}")
            
            domain = selector.current_domain
            self.stdout.write(f"✅ Page loaded successfully (Domain: {domain})")
            
            # Show saved selectors if requested
            if show_saved:
                self._show_saved_selectors(selector, domain)
                return
            
            # Test all selectors if requested
            if test_all:
                self._test_all_selectors(selector, test_urls)
                return
            
            # Get field completion status
            saved_selectors = selector.get_saved_selectors()
            completed_fields = [s.field_name for s in saved_selectors]
            manual_fields = [s.field_name for s in saved_selectors if s.requires_manual_input]
            
            self.stdout.write(f"\n📊 Field Progress for {domain}:")
            self.stdout.write(f"   ✅ Completed: {len(completed_fields)}/14 fields")
            self.stdout.write(f"   📝 Manual: {len(manual_fields)} fields")
            
            if completed_fields:
                self.stdout.write(f"   Fields completed: {', '.join(completed_fields)}")
            
            # Show field menu
            self.stdout.write("\n🎯 Displaying field selection menu...")
            if not selector.show_field_menu():
                raise CommandError("Failed to display field menu")
            
            # Interactive field selection session
            self._run_interactive_session(selector, test_urls)
            
        except KeyboardInterrupt:
            self.stdout.write("\n\n⚠️  Interrupted by user")
        except Exception as e:
            self.stdout.write(f"\n❌ Error: {e}")
        finally:
            self.stdout.write("\n🔄 Cleaning up...")
            selector.close()
            self.stdout.write("✅ Cleanup complete")

    def _show_saved_selectors(self, selector: InteractiveSelector, domain: str):
        """Display saved selectors for the domain"""
        self.stdout.write(f"\n📋 Saved Selectors for {domain}:")
        
        saved_selectors = selector.get_saved_selectors()
        if not saved_selectors:
            self.stdout.write("   No selectors saved yet.")
            return
        
        for sel in saved_selectors:
            status = "📝 Manual" if sel.requires_manual_input else f"🎯 XPath ({sel.success_rate:.1%})"
            self.stdout.write(f"   • {sel.get_field_name_display()}: {status}")
            if sel.requires_manual_input:
                self.stdout.write(f"     Note: {sel.manual_input_note}")
            else:
                self.stdout.write(f"     XPath: {sel.xpath[:100]}...")
        
        # Show manual input fields
        manual_fields = selector.get_manual_input_fields()
        if manual_fields:
            self.stdout.write(f"\n📝 Manual Input Fields:")
            for field in manual_fields:
                self.stdout.write(f"   • {field['field_label']}: {field['manual_input_note']}")

    def _test_all_selectors(self, selector: InteractiveSelector, test_urls: list):
        """Test all saved selectors on provided URLs"""
        domain = selector.current_domain
        saved_selectors = selector.get_saved_selectors()
        
        if not saved_selectors:
            self.stdout.write(f"No selectors saved for {domain}")
            return
        
        if not test_urls:
            self.stdout.write("❌ No test URLs provided. Use --test-urls option.")
            return
        
        self.stdout.write(f"\n🧪 Testing {len(saved_selectors)} selectors on {len(test_urls)} pages...")
        
        for test_url in test_urls:
            self.stdout.write(f"\n   Testing on: {test_url}")
            results = selector.test_all_selectors_on_page(test_url)
            
            for field_name, result in results.items():
                status = "✅" if result['success'] else "❌"
                self.stdout.write(f"     {status} {field_name}: {result['result_type']}")
                if result['content']:
                    preview = result['content'][:80] + "..." if len(result['content']) > 80 else result['content']
                    self.stdout.write(f"         Content: {preview}")
        
        # Show updated success rates
        self.stdout.write(f"\n📊 Updated Success Rates:")
        success_rates = selector.get_selector_success_rates()
        for field_name, rate in success_rates.items():
            self.stdout.write(f"   • {field_name}: {rate:.1%}")

    def _run_interactive_session(self, selector: InteractiveSelector, test_urls: list):
        """Run interactive field selection session"""
        self.stdout.write("\n🎮 Interactive Field Selection Session")
        self.stdout.write("=" * 50)
        self.stdout.write("Commands:")
        self.stdout.write("  save <field_name>     - Save current selections for field")
        self.stdout.write("  manual <field_name> <note> - Mark field as manual input")
        self.stdout.write("  test <field_name>     - Test field selector on test URLs")
        self.stdout.write("  test-all              - Test all selectors on test URLs")
        self.stdout.write("  status                - Show completion status")
        self.stdout.write("  help                  - Show this help")
        self.stdout.write("  quit                  - Exit session")
        
        if test_urls:
            self.stdout.write(f"\nTest URLs available: {len(test_urls)}")
            for i, url in enumerate(test_urls, 1):
                self.stdout.write(f"  {i}. {url}")
        
        while True:
            try:
                command = input("\n> ").strip()
                
                if not command:
                    continue
                
                parts = command.split(' ', 2)
                cmd = parts[0].lower()
                
                if cmd == 'quit':
                    break
                
                elif cmd == 'help':
                    self._show_help()
                
                elif cmd == 'status':
                    self._show_status(selector)
                
                elif cmd == 'save' and len(parts) >= 2:
                    field_name = parts[1]
                    self._save_field_selector(selector, field_name)
                
                elif cmd == 'manual' and len(parts) >= 3:
                    field_name = parts[1]
                    note = parts[2]
                    self._mark_field_manual(selector, field_name, note)
                
                elif cmd == 'test' and len(parts) >= 2:
                    field_name = parts[1]
                    self._test_field_selector(selector, field_name, test_urls)
                
                elif cmd == 'test-all':
                    self._test_all_selectors(selector, test_urls)
                
                else:
                    self.stdout.write("❌ Unknown command. Type 'help' for available commands.")
                    
            except (EOFError, KeyboardInterrupt):
                break

    def _save_field_selector(self, selector: InteractiveSelector, field_name: str):
        """Save current selections as a field selector"""
        # Get current selections for the field
        selections = selector.get_field_selections(field_name)
        
        if not selections:
            self.stdout.write(f"❌ No selections found for field: {field_name}")
            return
        
        # Use the first selection's XPath
        xpath = selections[0].get('xpath', '')
        if not xpath:
            self.stdout.write(f"❌ No XPath found in selections for: {field_name}")
            return
        
        # Save the selector
        if selector.save_field_selector(field_name, xpath):
            self.stdout.write(f"✅ Saved selector for {field_name}")
            self.stdout.write(f"   XPath: {xpath}")
        else:
            self.stdout.write(f"❌ Failed to save selector for {field_name}")

    def _mark_field_manual(self, selector: InteractiveSelector, field_name: str, note: str):
        """Mark a field as requiring manual input"""
        if selector.mark_field_as_manual(field_name, note):
            self.stdout.write(f"✅ Marked {field_name} as manual input")
            self.stdout.write(f"   Note: {note}")
        else:
            self.stdout.write(f"❌ Failed to mark {field_name} as manual")

    def _test_field_selector(self, selector: InteractiveSelector, field_name: str, test_urls: list):
        """Test a specific field selector"""
        if not test_urls:
            self.stdout.write("❌ No test URLs available")
            return
        
        # Get the selector
        saved_selectors = selector.get_saved_selectors()
        field_selector = next((s for s in saved_selectors if s.field_name == field_name), None)
        
        if not field_selector:
            self.stdout.write(f"❌ No saved selector found for {field_name}")
            return
        
        if field_selector.requires_manual_input:
            self.stdout.write(f"ℹ️  {field_name} is marked as manual input")
            return
        
        self.stdout.write(f"🧪 Testing {field_name} selector on {len(test_urls)} pages...")
        
        for test_url in test_urls:
            result = selector.test_selector_on_page(field_selector, test_url)
            status = "✅" if result['success'] else "❌"
            self.stdout.write(f"  {status} {test_url}: {result['result_type']}")
            
            if result['content']:
                preview = result['content'][:100] + "..." if len(result['content']) > 100 else result['content']
                self.stdout.write(f"      Content: {preview}")
        
        # Update success rate
        field_selector.refresh_from_db()
        self.stdout.write(f"📊 Updated success rate: {field_selector.success_rate:.1%}")

    def _show_status(self, selector: InteractiveSelector):
        """Show current field completion status"""
        domain = selector.current_domain
        saved_selectors = selector.get_saved_selectors()
        
        self.stdout.write(f"\n📊 Status for {domain}:")
        self.stdout.write(f"   Completed: {len(saved_selectors)}/14 fields")
        
        # Get field session
        field_session = selector._get_or_create_field_session(domain)
        remaining_fields = field_session.get_remaining_fields()
        
        if remaining_fields:
            self.stdout.write(f"   Remaining: {', '.join(remaining_fields)}")
        
        # Show success rates
        success_rates = selector.get_selector_success_rates()
        if success_rates:
            self.stdout.write("   Success rates:")
            for field_name, rate in success_rates.items():
                self.stdout.write(f"     • {field_name}: {rate:.1%}")

    def _show_help(self):
        """Show command help"""
        self.stdout.write("\n📖 Available Commands:")
        self.stdout.write("  save <field_name>         - Save current selections for field")
        self.stdout.write("  manual <field_name> <note> - Mark field as manual input")
        self.stdout.write("  test <field_name>         - Test field selector on test URLs")
        self.stdout.write("  test-all                  - Test all selectors on test URLs")
        self.stdout.write("  status                    - Show completion status")
        self.stdout.write("  help                      - Show this help")
        self.stdout.write("  quit                      - Exit session")
        self.stdout.write("\nField selection workflow:")
        self.stdout.write("  1. Use floating menu in browser to select field")
        self.stdout.write("  2. Click elements on page to select content")
        self.stdout.write("  3. Use 'save <field_name>' to save selector")
        self.stdout.write("  4. Use 'test <field_name>' to test on other pages") 