"""
Test Nested Object Selection Architecture

Management command to test the nested selection interface for hierarchical data.
Demonstrates recursive selection contexts with visual depth indicators.

Created by: Quantum Horizon
Date: 2025-01-08
Project: Triad Docker Base
"""

import time
from django.core.management.base import BaseCommand
from apps.content_extractor.selectors.interactive_selector import InteractiveSelector


class Command(BaseCommand):
    help = 'Test nested object selection architecture with recursive contexts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            type=str,
            default='https://www.airscience.com/product-category-page?brandname=safefume-fuming-chambers&brand=14',
            help='URL to test nested selection on'
        )
        parser.add_argument(
            '--headless',
            action='store_true',
            help='Run browser in headless mode'
        )
        parser.add_argument(
            '--demo',
            action='store_true',
            help='Run automated demo of nested selection features'
        )
        parser.add_argument(
            '--interactive',
            action='store_true',
            help='Run in interactive mode - allows manual testing of the interface'
        )

    def handle(self, *args, **options):
        url = options['url']
        headless = options['headless']
        demo_mode = options['demo']
        interactive_mode = options['interactive']
        
        self.stdout.write(
            self.style.SUCCESS("🚀 Testing Nested Object Selection Architecture")
        )
        self.stdout.write("📋 Available test URLs:")
        self.stdout.write("   https://www.airscience.com/product-category-page?brandname=safefume-fuming-chambers&brand=14")
        self.stdout.write("   https://www.airscience.com/product-category-page?brandname=purair-flow-laminar-flow-cabinets&brand=13")
        self.stdout.write("   https://www.airscience.com/product-category-page?brandname=purair-nano-ductless-nanoparticle-enclosures&brand=47")
        self.stdout.write("   https://www.airscience.com/product-category-page?brandname=purair-flex-portable-isolators&brand=37")
        self.stdout.write("")
        self.stdout.write(f"URL: {url}")
        self.stdout.write(f"Headless: {headless}")
        self.stdout.write(f"Demo Mode: {demo_mode}")
        self.stdout.write(f"Interactive Mode: {interactive_mode}")
        self.stdout.write("=" * 60)
        
        # Initialize interactive selector with nested support
        selector = InteractiveSelector(headless=headless, session_name="nested_test")
        
        try:
            # Load the test page
            self.stdout.write("📄 Loading test page...")
            if not selector.load_page(url):
                self.stdout.write(self.style.ERROR("❌ Failed to load page"))
                return
            
            self.stdout.write(self.style.SUCCESS("✅ Page loaded successfully"))
            
            # Display current context information
            self._display_context_info(selector)
            
            if demo_mode:
                self._run_automated_demo(selector)
            elif interactive_mode:
                self._run_command_interactive_test(selector)
            else:
                self._run_visual_interactive_test(selector)
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error during testing: {e}"))
        finally:
            selector.close()
            self.stdout.write("🔄 Browser closed")
    
    def _display_context_info(self, selector):
        """Display current nested selection context information."""
        context_info = selector.get_nested_selection_hierarchy()
        
        self.stdout.write("\n🎯 Current Selection Context:")
        self.stdout.write(f"   Depth: {context_info['current_depth']}")
        self.stdout.write(f"   Breadcrumbs: {' → '.join(context_info['breadcrumbs'])}")
        self.stdout.write(f"   Available Fields ({len(context_info['available_fields'])}):")
        
        for field in context_info['available_fields']:
            field_type_icon = {
                'single': '📄',
                'multi-value': '📋', 
                'nested': '🏗️'
            }.get(field['type'], '❓')
            
            nested_indicator = ' (has sub-fields)' if field['has_sub_fields'] else ''
            
            self.stdout.write(f"     {field_type_icon} {field['label']} ({field['type']}){nested_indicator}")
        
        self.stdout.write("")
    
    def _run_automated_demo(self, selector):
        """Run automated demonstration of nested selection features."""
        self.stdout.write("🤖 Running Automated Demo")
        self.stdout.write("=" * 40)
        
        # Show the field menu
        self.stdout.write("\n1️⃣ Displaying field selection menu...")
        selector.show_field_menu()
        time.sleep(3)
        
        # Test entering nested context for 'models'
        self.stdout.write("\n2️⃣ Testing nested field entry: 'models'")
        if selector.enter_nested_field('models', 0):
            self.stdout.write(self.style.SUCCESS("✅ Successfully entered 'models' context"))
            self._display_context_info(selector)
            time.sleep(2)
            
            # Show updated menu with models sub-fields
            self.stdout.write("\n3️⃣ Displaying nested context menu...")
            selector.show_field_menu()
            time.sleep(3)
            
            # Test entering deeper nested context for 'spec_groups'
            current_fields = selector.nested_manager.get_current_fields()
            spec_groups_field = next((f for f in current_fields if f.name == 'spec_groups'), None)
            
            if spec_groups_field and spec_groups_field.type == 'nested':
                self.stdout.write("\n4️⃣ Testing deeper nesting: 'spec_groups'")
                if selector.enter_nested_field('spec_groups', 0):
                    self.stdout.write(self.style.SUCCESS("✅ Successfully entered 'spec_groups' context"))
                    self._display_context_info(selector)
                    time.sleep(2)
                    
                    # Show deepest level menu
                    self.stdout.write("\n5️⃣ Displaying deepest nested context menu...")
                    selector.show_field_menu()
                    time.sleep(3)
                    
                    # Test navigation back to parent
                    self.stdout.write("\n6️⃣ Testing parent navigation...")
                    if selector.navigate_to_parent():
                        self.stdout.write(self.style.SUCCESS("✅ Successfully navigated to parent"))
                        self._display_context_info(selector)
                        time.sleep(2)
                    
                    # Test navigation to root
                    self.stdout.write("\n7️⃣ Testing navigation to root...")
                    if selector.navigate_to_depth(0):
                        self.stdout.write(self.style.SUCCESS("✅ Successfully navigated to root"))
                        self._display_context_info(selector)
                        time.sleep(2)
        
        # Show final state
        self.stdout.write("\n8️⃣ Final state - showing root menu...")
        selector.show_field_menu()
        time.sleep(5)
        
        # Export hierarchy
        hierarchy = selector.get_nested_selection_hierarchy()
        self.stdout.write(f"\n📊 Exported hierarchy: {hierarchy}")
        
        self.stdout.write(self.style.SUCCESS("\n✅ Automated demo completed!"))
    
    def _run_command_interactive_test(self, selector):
        """Run command-based interactive test allowing manual exploration."""
        self.stdout.write("🎮 Interactive Test Mode")
        self.stdout.write("=" * 40)
        self.stdout.write("Commands:")
        self.stdout.write("  menu    - Show field selection menu")
        self.stdout.write("  enter <field>  - Enter nested field context")
        self.stdout.write("  parent  - Navigate to parent context")
        self.stdout.write("  depth <n>  - Navigate to specific depth")
        self.stdout.write("  info    - Display current context info")
        self.stdout.write("  export  - Export selection hierarchy")
        self.stdout.write("  quit    - Exit test")
        self.stdout.write("")
        
        # Show initial menu
        selector.show_field_menu()
        
        while True:
            try:
                command = input("\n🎯 Enter command: ").strip().lower()
                
                if command == 'quit':
                    break
                elif command == 'menu':
                    selector.show_field_menu()
                    self.stdout.write("✅ Field menu displayed")
                    
                elif command.startswith('enter '):
                    field_name = command[6:].strip()
                    if selector.enter_nested_field(field_name, 0):
                        self.stdout.write(f"✅ Entered nested field: {field_name}")
                        self._display_context_info(selector)
                    else:
                        self.stdout.write(f"❌ Failed to enter field: {field_name}")
                        
                elif command == 'parent':
                    if selector.navigate_to_parent():
                        self.stdout.write("✅ Navigated to parent")
                        self._display_context_info(selector)
                    else:
                        self.stdout.write("❌ Failed to navigate to parent (already at root?)")
                        
                elif command.startswith('depth '):
                    try:
                        depth = int(command[6:].strip())
                        if selector.navigate_to_depth(depth):
                            self.stdout.write(f"✅ Navigated to depth {depth}")
                            self._display_context_info(selector)
                        else:
                            self.stdout.write(f"❌ Failed to navigate to depth {depth}")
                    except ValueError:
                        self.stdout.write("❌ Invalid depth number")
                        
                elif command == 'info':
                    self._display_context_info(selector)
                    
                elif command == 'export':
                    hierarchy = selector.get_nested_selection_hierarchy()
                    self.stdout.write(f"📊 Hierarchy: {hierarchy}")
                    
                else:
                    self.stdout.write("❓ Unknown command")
                    
                # Check for any pending nested actions from UI
                selector.check_for_nested_actions()
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.stdout.write(f"❌ Error: {e}")
        
        self.stdout.write(self.style.SUCCESS("\n✅ Interactive test completed!"))

    def _run_visual_interactive_test(self, selector):
        """Run visual-based interactive test allowing manual exploration."""
        self.stdout.write("🎮 Visual Interactive Test Mode")
        self.stdout.write("=" * 40)
        self.stdout.write("📍 Instructions:")
        self.stdout.write("  - Browser window will stay open for you to interact with")
        self.stdout.write("  - Click on the field menu to navigate nested contexts")
        self.stdout.write("  - Use breadcrumb navigation to move between levels")
        self.stdout.write("  - Test the visual hierarchy indicators")
        self.stdout.write("  - Press Enter here when you're done testing")
        self.stdout.write("")
        
        # Show the field menu to start
        self.stdout.write("🎯 Displaying field selection menu...")
        selector.show_field_menu()
        self.stdout.write("✅ Field menu is now visible in the browser")
        self.stdout.write("🔍 Current context info:")
        self._display_context_info(selector)
        
        try:
            import threading
            import sys
            
            # Flag to control polling
            should_continue_polling = True
            
            def poll_for_actions():
                """Background thread to continuously poll for nested actions"""
                while should_continue_polling:
                    try:
                        # Check for nested actions from JavaScript
                        if selector.check_for_nested_actions():
                            # Action was handled, display updated context
                            self.stdout.write("🔄 Nested navigation detected - context updated!")
                            self._display_context_info(selector)
                        
                        # Small delay to avoid excessive polling
                        time.sleep(0.5)
                    except Exception as e:
                        # Silent failure - don't spam the console
                        pass
            
            # Start polling thread
            polling_thread = threading.Thread(target=poll_for_actions, daemon=True)
            polling_thread.start()
            
            self.stdout.write("\n🔍 Background polling active - nested navigation will be detected automatically")
            self.stdout.write("💡 Try clicking on 'Models' or 'Specification Groups' to test nested navigation")
            
            # Keep the browser open and let user interact
            input("\n⏳ Press Enter when you're finished testing the interface...")
            
            # Stop polling
            should_continue_polling = False
            
            # Get final state
            self.stdout.write("\n📊 Final test results:")
            hierarchy = selector.get_nested_selection_hierarchy()
            self.stdout.write(f"   Selection hierarchy: {hierarchy}")
            self._display_context_info(selector)
            
        except KeyboardInterrupt:
            should_continue_polling = False
            self.stdout.write("\n🛑 Test interrupted by user")
        except Exception as e:
            should_continue_polling = False
            self.stdout.write(f"\n❌ Error during visual test: {e}")
        
        self.stdout.write(self.style.SUCCESS("\n✅ Visual interactive test completed!")) 