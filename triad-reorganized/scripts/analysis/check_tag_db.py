#!/usr/bin/env python
import os
import django

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.base")
django.setup()

# Import models
from apps.base_site.models import LabEquipmentPage
from apps.categorized_tags.models import CategorizedTag, TagCategory
from django.db import connection

def check_categorized_tags_db():
    """
    Check the database tables directly for tag relationships
    """
    print("\nDIRECT DB QUERY: Product Category and Application Tags")
    print("-" * 70)
    
    # Get all tag categories
    tag_categories = TagCategory.objects.all()
    for category in tag_categories:
        print(f"\nCategory: {category.name} (ID: {category.id})")
        
        # Get all tags in this category
        tags = CategorizedTag.objects.filter(category=category.name)
        print(f"  Total tags in category: {tags.count()}")
        
        # Check the relationships directly using raw SQL
        with connection.cursor() as cursor:
            # Look for tag relationships involving this category
            cursor.execute("""
                SELECT ct.name, ct.id, COUNT(cpt.id)
                FROM categorized_tags_categorizedtag ct
                LEFT JOIN categorized_tags_categorizedpagetag cpt ON ct.id = cpt.tag_id
                WHERE ct.category = %s
                GROUP BY ct.name, ct.id
                ORDER BY ct.name
            """, [category.name])
            
            rows = cursor.fetchall()
            
            if rows:
                print(f"  Tags with relationship counts:")
                for row in rows:
                    tag_name, tag_id, rel_count = row
                    print(f"    - {tag_name} (ID: {tag_id}): {rel_count} relationships")
                    
                    # If there are relationships, show a sample page
                    if rel_count > 0:
                        cursor.execute("""
                            SELECT wp.title, lep.page_ptr_id, lep.airscience_url
                            FROM categorized_tags_categorizedpagetag cpt
                            JOIN wagtailcore_page wp ON cpt.content_object_id = wp.id
                            JOIN base_site_labequipmentpage lep ON wp.id = lep.page_ptr_id
                            WHERE cpt.tag_id = %s
                            LIMIT 1
                        """, [tag_id])
                        
                        page_samples = cursor.fetchall()
                        for page in page_samples:
                            title, page_id, url = page
                            print(f"      Sample page: {title} (ID: {page_id}, URL: {url})")

    # Check recently added relationships
    print("\nMost recent tag relationships added:")
    print("-" * 70)
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT cpt.id, ct.category, ct.name, wp.title, lep.page_ptr_id
            FROM categorized_tags_categorizedpagetag cpt
            JOIN categorized_tags_categorizedtag ct ON cpt.tag_id = ct.id
            JOIN wagtailcore_page wp ON cpt.content_object_id = wp.id
            JOIN base_site_labequipmentpage lep ON wp.id = lep.page_ptr_id
            ORDER BY cpt.id DESC
            LIMIT 10
        """)
        
        rows = cursor.fetchall()
        
        if rows:
            for row in rows:
                rel_id, category, tag_name, page_title, page_id = row
                print(f"Relationship ID: {rel_id}")
                print(f"  Tag: {category}: {tag_name}")
                print(f"  Page: {page_title} (ID: {page_id})")
                print("-" * 30)

    # Check for mismatch between page_ptr_id and content_object_id
    print("\nChecking for mismatches between page_ptr_id and content_object_id:")
    print("-" * 70)
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) 
            FROM categorized_tags_categorizedpagetag cpt
            LEFT JOIN base_site_labequipmentpage lep ON cpt.content_object_id = lep.page_ptr_id
            WHERE lep.page_ptr_id IS NULL
        """)
        
        mismatch_count = cursor.fetchone()[0]
        print(f"Found {mismatch_count} tag relationships with no matching page_ptr_id")
        
        if mismatch_count > 0:
            cursor.execute("""
                SELECT cpt.id, cpt.content_object_id, ct.category, ct.name
                FROM categorized_tags_categorizedpagetag cpt
                JOIN categorized_tags_categorizedtag ct ON cpt.tag_id = ct.id
                LEFT JOIN base_site_labequipmentpage lep ON cpt.content_object_id = lep.page_ptr_id
                WHERE lep.page_ptr_id IS NULL
                LIMIT 10
            """)
            
            rows = cursor.fetchall()
            for row in rows:
                rel_id, content_id, category, tag_name = row
                print(f"Relationship ID: {rel_id}")
                print(f"  content_object_id: {content_id}")
                print(f"  Tag: {category}: {tag_name}")
                print("-" * 30)

if __name__ == "__main__":
    check_categorized_tags_db() 