#!/usr/bin/env python3
"""
Test Script for Enhanced Interactive Selector
Created by: Stellar Horizon
Date: 2025-01-08

Tests the Phase 1 UI fixes: disappearing prompts, auto-fill, and sub-menus
"""

import os
import sys
import logging
import time
from datetime import datetime

# Add Django project to path
sys.path.append('/Users/lucypatton/LLLK/triad-docker-base')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

import django
django.setup()

from apps.content_extractor.selectors.interactive_selector import InteractiveSelector

# Configure comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console output
        logging.FileHandler('.project_management/logs/interactive_selector_test.log', mode='a')
    ]
)

logger = logging.getLogger(__name__)

# Test URLs for the session
TEST_URLS = [
    "https://www.airscience.com/product-category-page?brandname=safefume-fuming-chambers&brand=14",
    "https://www.airscience.com/product-category-page?brandname=purair-flow-laminar-flow-cabinets&brand=13", 
    "https://www.airscience.com/product-category-page?brandname=purair-nano-ductless-nanoparticle-enclosures&brand=47",
    "https://www.airscience.com/",
    "https://www.airscience.com/products"
]

def print_banner():
    """Print test session banner"""
    print("\n" + "="*80)
    print("🚀 ENHANCED INTERACTIVE SELECTOR TEST SESSION")
    print("Model: Stellar Horizon | Phase 1 UI Fixes")
    print(f"Session Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    print("\n🎯 TESTING FEATURES:")
    print("  ✅ Fixed disappearing prompt menus (custom modals)")
    print("  ✅ Auto-fill functionality for common fields") 
    print("  ✅ Sub-menu architecture for complex fields")
    print("  ✅ Enhanced interaction patterns (Ctrl+Click, Alt+Click)")
    print("\n🔧 INTERACTION GUIDE:")
    print("  • Regular Click: Select elements for current field")
    print("  • Ctrl/Cmd+Click: Navigate page without selecting")
    print("  • Alt+Click: Preview element info (console log)")
    print("  • Use field menu to switch between LabEquipmentPage fields")
    print("  • Try Auto-Fill button for quick field population")
    print("\n📋 AVAILABLE TEST URLS:")
    for i, url in enumerate(TEST_URLS, 1):
        print(f"  {i}. {url}")
    print("\n" + "="*80 + "\n")

def test_selector_session():
    """Run interactive selector test session"""
    
    print_banner()
    
    # Initialize selector with logging
    logger.info("🚀 Starting Enhanced Interactive Selector Test Session")
    logger.info("Features: Fixed prompts, Auto-fill, Sub-menus, Enhanced interactions")
    
    session_name = f"stellar_horizon_test_{int(time.time())}"
    selector = InteractiveSelector(headless=False, session_name=session_name)
    
    try:
        # Setup driver
        logger.info("Setting up Chrome WebDriver...")
        if not selector.setup_driver():
            logger.error("❌ Failed to setup WebDriver")
            return False
        
        logger.info("✅ WebDriver setup successful")
        
        # Get user choice for test URL
        print("Select a test URL:")
        for i, url in enumerate(TEST_URLS, 1):
            print(f"  {i}. {url.split('/')[-1] if '?' in url else url.split('/')[-2:]}")
        
        while True:
            try:
                choice = input("\nEnter URL number (1-5): ").strip()
                url_index = int(choice) - 1
                if 0 <= url_index < len(TEST_URLS):
                    test_url = TEST_URLS[url_index]
                    break
                else:
                    print("❌ Invalid choice. Please enter 1-5.")
            except ValueError:
                print("❌ Please enter a valid number.")
        
        # Load the selected page
        logger.info(f"📍 Loading test URL: {test_url}")
        print(f"\n📍 Loading: {test_url}")
        
        if not selector.load_page(test_url):
            logger.error(f"❌ Failed to load page: {test_url}")
            print("❌ Failed to load page")
            return False
        
        logger.info("✅ Page loaded successfully")
        print("✅ Page loaded successfully!")
        
        # Show field selection menu
        logger.info("🎯 Displaying field selection menu...")
        print("\n🎯 Opening field selection menu...")
        
        if not selector.show_field_menu():
            logger.error("❌ Failed to show field menu")
            print("❌ Failed to show field menu")
            return False
        
        logger.info("✅ Field menu displayed")
        print("✅ Field menu displayed!")
        
        # Instructions for testing
        print("\n" + "="*60)
        print("🧪 TESTING INSTRUCTIONS:")
        print("="*60)
        print("1. 📋 Choose a field from the floating menu")
        print("2. 🎯 Try the Auto-Fill button for automatic content detection")
        print("3. 🖱️  Use different click patterns:")
        print("   • Regular click: Select elements")
        print("   • Ctrl+Click: Navigate without selecting") 
        print("   • Alt+Click: Preview element info")
        print("4. 📊 For multi-value fields, try selecting 2+ examples")
        print("5. 💾 Use Save button to persist selectors")
        print("6. 🧪 Use Test button for cross-page validation")
        print("7. 🧭 Use Navigate button for URL switching")
        print("\n🔍 Monitor console logs for debugging info")
        print("📝 All actions are logged to: .project_management/logs/")
        print("="*60)
        
        # Monitor control panel actions
        logger.info("🔄 Starting control panel monitoring...")
        print("\n🔄 Monitoring control panel actions...")
        print("💡 Browser window is ready for testing!")
        print("⏹️  Press Ctrl+C to end session\n")
        
        # Keep monitoring for user actions
        try:
            while True:
                time.sleep(2)  # Check every 2 seconds
                
                # Handle any control panel actions
                results = selector.handle_control_panel_actions()
                
                if results:
                    for action, result in results.items():
                        if result.get('success'):
                            logger.info(f"✅ {action.upper()} action completed: {result}")
                            print(f"✅ {action.upper()} completed successfully")
                        else:
                            logger.warning(f"⚠️ {action.upper()} action failed: {result}")
                            print(f"⚠️ {action.upper()} failed: {result.get('error', 'Unknown error')}")
                
                # Update progress
                selector.update_control_panel_progress()
                
        except KeyboardInterrupt:
            logger.info("🛑 User interrupted session")
            print("\n🛑 Session ended by user")
    
    except Exception as e:
        logger.error(f"❌ Error during test session: {e}")
        print(f"\n❌ Error during test session: {e}")
        return False
    
    finally:
        # Get final results
        try:
            all_selections = selector.get_all_field_selections()
            completion_status = selector.get_field_completion_status()
            
            logger.info("📊 SESSION SUMMARY:")
            logger.info(f"Fields with selections: {len(all_selections)}")
            logger.info(f"Total selections made: {sum(len(sels) for sels in all_selections.values())}")
            logger.info(f"Completion status: {completion_status}")
            
            print("\n📊 SESSION SUMMARY:")
            print(f"Fields with selections: {len(all_selections)}")
            print(f"Total selections made: {sum(len(sels) for sels in all_selections.values())}")
            
            for field_name, selections in all_selections.items():
                print(f"  • {field_name}: {len(selections)} selections")
            
        except Exception as e:
            logger.error(f"Error getting session summary: {e}")
        
        # Cleanup
        logger.info("🧹 Cleaning up WebDriver...")
        print("\n🧹 Cleaning up...")
        selector.close()
        logger.info("✅ Test session completed")
        print("✅ Session completed!")
    
    return True

if __name__ == "__main__":
    try:
        test_selector_session()
    except Exception as e:
        logger.error(f"Fatal error in test session: {e}")
        print(f"\n💥 Fatal error: {e}")
        sys.exit(1) 