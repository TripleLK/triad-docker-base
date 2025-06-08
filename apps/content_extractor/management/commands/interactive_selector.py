"""
Interactive Content Selector Management Command

Official interactive selector for hierarchical content extraction with nested object support.
Provides comprehensive interface for field selection with visual depth indicators and context management.

Created by: Quantum Horizon
Enhanced by: Swift Weaver (Dynamic API Token Generation)
Enhanced by: Rapid Forge (Multi-URL Testing Support)
Date: 2025-01-08
Updated: 2025-01-22
Project: Triad Docker Base
"""

import time
import signal
import atexit
from django.core.management.base import BaseCommand
from apps.content_extractor.selectors.interactive_selector import InteractiveSelector
from apps.base_site.models import APIToken
from apps.content_extractor.models import SiteConfiguration


class Command(BaseCommand):
    help = 'Launch interactive content selector with nested object support, hierarchical field mapping, and multi-URL testing'
    
    # Class variable to track temporary token for cleanup
    temporary_token = None

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
            '--command',
            action='store_true',
            help='Run in command-line interactive mode instead of visual interactive mode (default is visual interactive)'
        )
        parser.add_argument(
            '--base-url',
            type=str,
            default='http://localhost:8000',
            help='Base URL for API calls (default: http://localhost:8000)'
        )
        parser.add_argument(
            '--token-expires',
            type=int,
            default=60,
            help='Token expiration time in minutes (default: 60)'
        )
        parser.add_argument(
            '--enable-multi-url',
            action='store_true',
            help='Enable multi-URL testing functionality - allows switching between configured test URLs during selection'
        )

    def handle(self, *args, **options):
        url = options['url']
        headless = options['headless']
        demo_mode = options['demo']
        command_mode = options['command']
        base_url = options['base_url']
        token_expires = options['token_expires']
        enable_multi_url = options['enable_multi_url']
        
        # Generate temporary API token
        api_token = self._generate_temporary_token(token_expires)
        self.temporary_token = api_token  # Store for cleanup
        
        # Set up signal handlers for cleanup
        self._setup_signal_handlers()
        
        # Register cleanup at exit
        atexit.register(self._cleanup_token)
        
        # Get site configuration for multi-URL testing
        site_config = None
        test_urls = []
        if enable_multi_url:
            site_config, test_urls = self._get_site_configuration_and_test_urls(url)
        
        self.stdout.write(
            self.style.SUCCESS("🚀 Interactive Content Selector - Hierarchical Field Mapping with Multi-URL Testing")
        )
        self.stdout.write("🔐 API Authentication:")
        self.stdout.write(f"   Generated temporary token: {api_token.name}")
        self.stdout.write(f"   Token expires in: {token_expires} minutes")
        self.stdout.write(f"   Token will be cleaned up automatically")
        self.stdout.write("")
        
        if enable_multi_url and site_config:
            self.stdout.write("🌐 Multi-URL Testing:")
            self.stdout.write(f"   Site: {site_config.site_name} ({site_config.site_domain})")
            self.stdout.write(f"   Available test URLs ({len(test_urls)}):")
            for i, test_url in enumerate(test_urls, 1):
                marker = ">>> " if test_url == url else "    "
                self.stdout.write(f"   {marker}{i}. {test_url}")
            self.stdout.write("   Use 'switch_url' command in interactive mode to test selectors on different URLs")
            self.stdout.write("")
        elif enable_multi_url:
            self.stdout.write("⚠️  Multi-URL Testing:")
            self.stdout.write(f"   No site configuration found for URL: {url}")
            self.stdout.write("   Create a SiteConfiguration in Wagtail admin and add test URLs to enable multi-URL testing")
            self.stdout.write("")
        
        self.stdout.write("📋 Supported extraction URLs:")
        self.stdout.write("   https://www.airscience.com/product-category-page?brandname=safefume-fuming-chambers&brand=14")
        self.stdout.write("   https://www.airscience.com/product-category-page?brandname=purair-flow-laminar-flow-cabinets&brand=13")
        self.stdout.write("   https://www.airscience.com/product-category-page?brandname=purair-nano-ductless-nanoparticle-enclosures&brand=47")
        self.stdout.write("   https://www.airscience.com/product-category-page?brandname=purair-flex-portable-isolators&brand=37")
        self.stdout.write("")
        self.stdout.write(f"Target URL: {url}")
        self.stdout.write(f"Base URL: {base_url}")
        self.stdout.write(f"Visual Mode: {'Disabled' if headless else 'Enabled'}")
        self.stdout.write(f"Demo Mode: {'Enabled' if demo_mode else 'Disabled'}")
        self.stdout.write(f"Command Mode: {'Enabled' if command_mode else 'Disabled (Visual Interactive Mode)'}")
        self.stdout.write(f"Multi-URL Testing: {'Enabled' if enable_multi_url else 'Disabled'}")
        self.stdout.write("=" * 60)
        
        # Initialize interactive selector with nested support, API token, and multi-URL support
        selector = InteractiveSelector(
            headless=headless, 
            session_name="content_extraction", 
            base_url=base_url,
            api_token=api_token.token,  # Pass the generated token
            enable_multi_url=enable_multi_url,
            site_config=site_config,
            test_urls=test_urls
        )
        
        try:
            # Load the target page
            self.stdout.write("📄 Loading content extraction target...")
            if not selector.load_page(url):
                self.stdout.write(self.style.ERROR("❌ Failed to load target page"))
                return
            
            self.stdout.write(self.style.SUCCESS("✅ Target page loaded successfully"))
            
            if enable_multi_url and test_urls:
                self.stdout.write(f"🌐 Multi-URL testing enabled with {len(test_urls)} test URLs available")
            
            # Display current context information
            self._display_context_info(selector)
            
            if demo_mode:
                self._run_automated_demo(selector)
            elif command_mode:
                self._run_command_interactive_mode(selector)
            else:
                self._run_visual_interactive_mode(selector)
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error during content selection: {e}"))
        finally:
            selector.close()
            self._cleanup_token()
            self.stdout.write("🔄 Content selector closed and token cleaned up")
    
    def _generate_temporary_token(self, expires_in_minutes):
        """Generate a temporary API token for this session."""
        import uuid
        from datetime import datetime
        
        session_id = str(uuid.uuid4())[:8]
        token_name = f"interactive_selector_{session_id}"
        
        # Clean up any existing expired tokens first
        cleanup_count = APIToken.cleanup_expired_tokens()
        if cleanup_count > 0:
            self.stdout.write(f"🧹 Cleaned up {cleanup_count} expired tokens")
        
        # Create temporary token
        api_token = APIToken.create_temporary_token(
            name=token_name,
            description=f"Temporary token for interactive selector session {session_id}",
            expires_in_minutes=expires_in_minutes,
            session_info={
                'session_id': session_id,
                'created_by_command': 'interactive_selector',
                'timestamp': datetime.now().isoformat()
            }
        )
        
        self.stdout.write(self.style.SUCCESS(f"🔑 Generated temporary API token: {api_token.token}"))
        return api_token
    
    def _setup_signal_handlers(self):
        """Set up signal handlers for graceful cleanup."""
        def signal_handler(signum, frame):
            self.stdout.write(f"\n🔄 Received signal {signum}, cleaning up...")
            self._cleanup_token()
            exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
        signal.signal(signal.SIGTERM, signal_handler)  # Termination
    
    def _cleanup_token(self):
        """Clean up the temporary token."""
        if self.temporary_token:
            try:
                # Mark token as inactive instead of deleting (for audit trail)
                self.temporary_token.is_active = False
                self.temporary_token.save()
                self.stdout.write(f"🧹 Deactivated temporary token: {self.temporary_token.name}")
                self.temporary_token = None
            except Exception as e:
                self.stdout.write(f"⚠️ Error cleaning up token: {e}")
    
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
    
    def _run_command_interactive_mode(self, selector):
        """Run command-based interactive mode allowing manual field exploration and selection."""
        self.stdout.write("🎮 Interactive Command Mode")
        self.stdout.write("=" * 40)
        self.stdout.write("Available commands:")
        self.stdout.write("  menu    - Show field selection menu")
        self.stdout.write("  enter <field>  - Enter nested field context")
        self.stdout.write("  parent  - Navigate to parent context")
        self.stdout.write("  depth <n>  - Navigate to specific depth")
        self.stdout.write("  info    - Display current context info")
        self.stdout.write("  export  - Export selection hierarchy")
        self.stdout.write("  quit    - Exit selector")
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

    def _run_visual_interactive_mode(self, selector):
        """Run visual-based interactive mode allowing manual field exploration through browser interface."""
        self.stdout.write("🎮 Visual Interactive Mode")
        self.stdout.write("=" * 40)
        self.stdout.write("Instructions:")
        self.stdout.write("  • Use the browser interface to navigate fields")
        self.stdout.write("  • Click elements to select content for fields")
        self.stdout.write("  • Use menus to enter nested contexts")
        self.stdout.write("  • Monitor this terminal for real-time feedback")
        self.stdout.write("")
        
        # Show initial field menu
        selector.show_field_menu()
        
        # Monitor for user actions
        try:
            def poll_for_actions():
                """Monitor selector for user actions and provide feedback"""
                last_context = None
                while True:
                    time.sleep(1)
                    
                    # Check if context changed
                    current_context = selector.get_nested_selection_hierarchy()
                    if current_context != last_context:
                        self.stdout.write(f"🎯 Context: {' → '.join(current_context['breadcrumbs'])}")
                        last_context = current_context
            
            poll_for_actions()
            
        except KeyboardInterrupt:
            self.stdout.write("\n👋 Visual interactive mode ended")
        
        self.stdout.write(self.style.SUCCESS("\n✅ Interactive mode completed!"))

    def _get_site_configuration_and_test_urls(self, url):
        """Get site configuration and test URLs for the given URL."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.replace('www.', '')  # Remove www for matching
            
            # Try to find site configuration by domain
            site_config = SiteConfiguration.objects.filter(
                site_domain__icontains=domain,
                is_active=True
            ).first()
            
            if not site_config:
                # Try alternative matching
                site_config = SiteConfiguration.objects.filter(
                    is_active=True
                ).filter(
                    site_domain__in=[domain, f"www.{domain}", parsed.netloc]
                ).first()
            
            if site_config:
                test_urls = site_config.get_valid_test_urls()
                # Ensure current URL is in the list
                if url not in test_urls:
                    test_urls.insert(0, url)
                return site_config, test_urls
            
            return None, []
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"⚠️ Error getting site configuration: {e}"))
            return None, [] 