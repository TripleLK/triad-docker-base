#!/usr/bin/env python
import os
import django

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.base")
django.setup()

# Import models
from apps.base_site.models import LabEquipmentPage
from apps.categorized_tags.models import CategorizedTag, CategorizedPageTag
from django.db import connection

def examine_tag_relationships():
    print("\nCounts:")
    print("-" * 50)
    print(f"LabEquipmentPage count: {LabEquipmentPage.objects.count()}")
    print(f"CategorizedTag count: {CategorizedTag.objects.count()}")
    print(f"CategorizedPageTag count: {CategorizedPageTag.objects.count()}")

    print("\nCategorizedPageTag Records:")
    print("-" * 50)
    for tag_rel in CategorizedPageTag.objects.all()[:5]:
        print(f"ID: {tag_rel.id}")
        print(f"  Content Object ID: {tag_rel.content_object_id}")
        print(f"  Tag ID: {tag_rel.tag_id}")
        print(f"  Tag: {tag_rel.tag}")
        print("-" * 30)

    print("\nDirect DB Query:")
    print("-" * 50)
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT cpt.id, cpt.content_object_id, cpt.tag_id, ct.name, ct.category 
            FROM categorized_tags_categorizedpagetag cpt
            JOIN categorized_tags_categorizedtag ct ON cpt.tag_id = ct.id
            LIMIT 5
        """)
        rows = cursor.fetchall()
        for row in rows:
            print(f"ID: {row[0]}")
            print(f"  Content Object ID: {row[1]}")
            print(f"  Tag ID: {row[2]}")
            print(f"  Tag Name: {row[3]}")
            print(f"  Tag Category: {row[4]}")
            print("-" * 30)

    print("\nPages with airscience_url:")
    print("-" * 50)
    pages_with_url = LabEquipmentPage.objects.exclude(airscience_url__isnull=True).exclude(airscience_url='')
    print(f"Count: {pages_with_url.count()}")
    for page in pages_with_url[:5]:
        print(f"Page ID: {page.page_ptr_id}")
        print(f"  Title: {page.title}")
        print(f"  URL: {page.airscience_url}")
        print(f"  Tags: {page.categorized_tags.count()}")
        try:
            for tag in page.categorized_tags.all():
                print(f"    - {tag.category}: {tag.name}")
        except Exception as e:
            print(f"  Error getting tags: {str(e)}")
        print("-" * 30)

    # Check for data in content_object_id
    print("\nChecking content_object_id values against page_ptr_id:")
    print("-" * 50)
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT cpt.content_object_id, COUNT(*)
            FROM categorized_tags_categorizedpagetag cpt
            GROUP BY cpt.content_object_id
            LIMIT 10
        """)
        rows = cursor.fetchall()
        print(f"Found {len(rows)} distinct content_object_id values")
        
        for row in rows:
            content_id = row[0]
            count = row[1]
            cursor.execute("""
                SELECT EXISTS(
                    SELECT 1 FROM base_site_labequipmentpage 
                    WHERE page_ptr_id = %s
                )
            """, [content_id])
            exists = cursor.fetchone()[0]
            print(f"Content ID: {content_id}, Tag count: {count}, Exists as page_ptr_id: {exists}")

if __name__ == "__main__":
    examine_tag_relationships() 