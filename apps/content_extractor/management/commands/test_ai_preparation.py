"""
Test AI Preparation Record Creation

Test command to verify that the updated system properly creates AI preparation records
during the content extraction process.

Created by: Stellar Hawk
Date: 2025-01-22
Project: Triad Docker Base - AI Preparation System Integration
"""

from django.core.management.base import BaseCommand
from apps.content_extractor.selectors.interactive_selector import InteractiveSelector
from apps.content_extractor.models import AIPreparationRecord


class Command(BaseCommand):
    help = 'Test AI preparation record creation with the updated selector system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            type=str,
            default='https://www.airscience.com/product-category-page?brandname=safefume-fuming-chambers&brand=14',
            help='URL to test AI preparation records on'
        )
        parser.add_argument(
            '--session-id',
            type=str,
            default='test_ai_session',
            help='Session ID for testing'
        )
        parser.add_argument(
            '--clear-previous',
            action='store_true',
            help='Clear previous test records before running'
        )

    def handle(self, *args, **options):
        url = options['url']
        session_id = options['session_id']
        clear_previous = options['clear_previous']
        
        self.stdout.write(
            self.style.SUCCESS("🧠 Testing AI Preparation Record Creation")
        )
        self.stdout.write(f"Session ID: {session_id}")
        self.stdout.write(f"Test URL: {url}")
        self.stdout.write("=" * 60)
        
        # Clear previous records if requested
        if clear_previous:
            AIPreparationRecord.objects.filter(session_id=session_id).delete()
            self.stdout.write(self.style.WARNING("🗑️  Cleared previous test records"))
        
        # Check existing records before test
        existing_count = AIPreparationRecord.objects.filter(session_id=session_id).count()
        self.stdout.write(f"📊 Existing AI preparation records for session: {existing_count}")
        
        # Initialize selector with test session
        selector = InteractiveSelector(headless=True, session_name=session_id)
        
        try:
            # Load the test page
            self.stdout.write("📄 Loading test page...")
            if not selector.load_page(url):
                self.stdout.write(self.style.ERROR("❌ Failed to load page"))
                return
            
            self.stdout.write(self.style.SUCCESS("✅ Page loaded successfully"))
            
            # Test AI preparation record creation with different scenarios
            test_records = [
                {
                    'field_name': 'title',
                    'extracted_content': 'Safefume Fuming Chambers - Laboratory Safety Equipment',
                    'xpath': '//h1[@class="product-title"]',
                    'user_comment': 'Main product title extracted from page header',
                    'confidence_level': 'high',
                    'content_type': 'text'
                },
                {
                    'field_name': 'short_description', 
                    'extracted_content': 'Premium fuming chambers for laboratory chemical safety',
                    'xpath': '//div[@class="product-summary"]//p[1]',
                    'user_comment': 'Brief product description for AI classification',
                    'confidence_level': 'medium',
                    'content_type': 'text'
                },
                {
                    'field_name': 'features',
                    'extracted_content': 'HEPA filtration, Chemical-resistant construction, Energy efficient operation',
                    'xpath': '//ul[@class="product-features"]//li',
                    'user_comment': 'Key product features list for AI analysis',
                    'confidence_level': 'high',
                    'content_type': 'list',
                    'instance_index': 0
                },
                {
                    'field_name': 'models',
                    'extracted_content': 'Model: SF-1200, Dimensions: 48" x 24" x 30"',
                    'xpath': '//div[@class="model-spec"]',
                    'user_comment': 'Nested model information for AI processing',
                    'confidence_level': 'medium',
                    'content_type': 'nested_data',
                    'instance_index': 0
                }
            ]
            
            self.stdout.write("\n🔬 Creating test AI preparation records...")
            
            for i, record_data in enumerate(test_records, 1):
                self.stdout.write(f"\n{i}️⃣ Creating record: {record_data['field_name']}")
                
                success = selector.save_ai_selection(**record_data)
                
                if success:
                    self.stdout.write(
                        self.style.SUCCESS(f"   ✅ Created AI preparation record for {record_data['field_name']}")
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f"   ❌ Failed to create record for {record_data['field_name']}")
                    )
            
            # Check final record count
            final_count = AIPreparationRecord.objects.filter(session_id=session_id).count()
            new_records = final_count - existing_count
            
            self.stdout.write(f"\n📊 Final Statistics:")
            self.stdout.write(f"   Records before test: {existing_count}")
            self.stdout.write(f"   Records after test: {final_count}")
            self.stdout.write(f"   New records created: {new_records}")
            
            # Display session records
            if final_count > 0:
                self.stdout.write(f"\n📋 AI Preparation Records in Session '{session_id}':")
                records = selector.get_ai_session_records()
                
                for record in records:
                    self.stdout.write(f"   📄 {record.field_name} ({record.content_type})")
                    self.stdout.write(f"      Content: {record.content_preview}")
                    self.stdout.write(f"      Comment: {record.user_comment}")
                    self.stdout.write(f"      Confidence: {record.confidence_level}")
                    self.stdout.write(f"      XPath: {record.xpath_used}")
                    self.stdout.write("")
            
            # Export session for AI
            self.stdout.write("🤖 Testing AI export functionality...")
            ai_export = selector.export_ai_session(format='structured')
            
            if ai_export:
                self.stdout.write(self.style.SUCCESS("✅ AI export successful"))
                content_fields = ai_export.get('content', {}) if isinstance(ai_export, dict) else {}
                self.stdout.write(f"   Exported {len(content_fields)} records for AI processing")
            else:
                self.stdout.write(self.style.WARNING("⚠️  AI export returned empty data"))
            
            # Get session statistics
            stats = selector.get_session_statistics()
            if stats:
                self.stdout.write(f"\n📈 Session Statistics:")
                self.stdout.write(f"   Total records: {stats.get('total_records', 0)}")
                self.stdout.write(f"   Fields extracted: {stats.get('fields_extracted', 0)}")
                self.stdout.write(f"   Extraction methods: {stats.get('extraction_methods', {})}")
                self.stdout.write(f"   Confidence levels: {stats.get('confidence_levels', {})}")
                self.stdout.write(f"   Content types: {stats.get('content_types', {})}")
            
            self.stdout.write(self.style.SUCCESS(f"\n🎉 AI Preparation Record Test Complete!"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error during testing: {e}"))
        finally:
            selector.close()
            self.stdout.write(" Browser closed") 