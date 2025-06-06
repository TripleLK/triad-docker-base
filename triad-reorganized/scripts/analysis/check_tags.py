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

def print_tag_counts():
    print("\nTAG COUNTS using Raw SQL:")
    print("-" * 50)
    
    # Use raw SQL to avoid the ORM issue
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT ct.category, ct.name, COUNT(*)
            FROM categorized_tags_categorizedtag ct
            JOIN categorized_tags_categorizedpagetag cpt ON ct.id = cpt.tag_id
            JOIN wagtailcore_page wp ON cpt.content_object_id = wp.id
            JOIN base_site_labequipmentpage lep ON wp.id = lep.page_ptr_id
            GROUP BY ct.category, ct.name
            ORDER BY ct.category, ct.name
        """)
        rows = cursor.fetchall()
        
        for row in rows:
            category, name, count = row
            print(f"{category}: {name} - {count} products")

def print_sample_products():
    print("\nSAMPLE PRODUCTS WITH TAGS using Raw SQL:")
    print("-" * 50)
    
    # Use raw SQL to get products with tags
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT lep.page_ptr_id, wp.title, lep.airscience_url
            FROM base_site_labequipmentpage lep
            JOIN wagtailcore_page wp ON lep.page_ptr_id = wp.id
            JOIN categorized_tags_categorizedpagetag cpt ON wp.id = cpt.content_object_id
            GROUP BY lep.page_ptr_id, wp.title, lep.airscience_url
            LIMIT 5
        """)
        products = cursor.fetchall()
        
        for product in products:
            page_id, title, url = product
            print(f"Product: {title}")
            print(f"ID: {page_id}")
            print(f"URL: {url}")
            print("Tags:")
            
            # Get tags for this product
            cursor.execute("""
                SELECT ct.category, ct.name
                FROM categorized_tags_categorizedtag ct
                JOIN categorized_tags_categorizedpagetag cpt ON ct.id = cpt.tag_id
                WHERE cpt.content_object_id = %s
                ORDER BY ct.category, ct.name
            """, [page_id])
            tags = cursor.fetchall()
            
            for tag in tags:
                category, name = tag
                print(f"  - {category}: {name}")
            print("-" * 30)

def print_tag_categories():
    print("\nTAG CATEGORIES:")
    print("-" * 50)
    
    categories = TagCategory.objects.all().order_by('name')
    for category in categories:
        print(f"Category: {category.name} (ID: {category.id})")
        # Count tags in this category
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*)
                FROM categorized_tags_categorizedtag
                WHERE category = %s
            """, [category.name])
            tag_count = cursor.fetchone()[0]
            
            # Count products with tags in this category
            cursor.execute("""
                SELECT COUNT(DISTINCT cpt.content_object_id)
                FROM categorized_tags_categorizedtag ct
                JOIN categorized_tags_categorizedpagetag cpt ON ct.id = cpt.tag_id
                WHERE ct.category = %s
            """, [category.name])
            product_count = cursor.fetchone()[0]
            
            print(f"  Tags: {tag_count}")
            print(f"  Products: {product_count}")
        print()

def check_categorized_page_tag_table():
    print("\nDIRECT CATEGORIZED_PAGE_TAG TABLE DUMP:")
    print("-" * 50)
    
    with connection.cursor() as cursor:
        # Get the total count
        cursor.execute("""
            SELECT COUNT(*)
            FROM categorized_tags_categorizedpagetag
        """)
        count = cursor.fetchone()[0]
        print(f"Total CategorizedPageTag entries: {count}")
        
        # Get category stats
        cursor.execute("""
            SELECT ct.category, COUNT(*)
            FROM categorized_tags_categorizedtag ct
            JOIN categorized_tags_categorizedpagetag cpt ON ct.id = cpt.tag_id
            GROUP BY ct.category
            ORDER BY ct.category
        """)
        cat_stats = cursor.fetchall()
        print("\nTag Category Stats:")
        for cat, count in cat_stats:
            print(f"  {cat}: {count} entries")
        
        # Get a sample of the raw data
        cursor.execute("""
            SELECT cpt.id, cpt.content_object_id, wp.title, ct.category, ct.name
            FROM categorized_tags_categorizedpagetag cpt
            JOIN categorized_tags_categorizedtag ct ON cpt.tag_id = ct.id
            JOIN wagtailcore_page wp ON cpt.content_object_id = wp.id
            ORDER BY cpt.id
            LIMIT 20
        """)
        rows = cursor.fetchall()
        
        print("\nSample Tag Entries:")
        for row in rows:
            id, content_id, title, category, name = row
            print(f"  ID: {id}, Page: {title} (ID: {content_id}), Tag: {category}: {name}")

if __name__ == "__main__":
    print_tag_categories()
    print_tag_counts()
    print_sample_products()
    check_categorized_page_tag_table() 