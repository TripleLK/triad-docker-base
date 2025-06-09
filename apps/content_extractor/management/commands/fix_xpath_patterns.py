"""
Django management command to fix malformed XPath patterns in FieldConfiguration model.

Created by: Stellar Hawk  
Date: 2025-01-22
Project: Triad Docker Base - XPath Pattern Correction
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.content_extractor.models import FieldConfiguration, SiteConfiguration


class Command(BaseCommand):
    help = 'Fix malformed XPath patterns in FieldConfiguration model'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making changes',
        )
        parser.add_argument(
            '--domain',
            type=str,
            help='Only fix patterns for specific domain (e.g., airscience.com)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        target_domain = options.get('domain')
        
        self.stdout.write(f"{'DRY RUN: ' if dry_run else ''}Fixing malformed XPath patterns...")
        
        # Build query
        query = FieldConfiguration.objects.select_related('site_config')
        if target_domain:
            query = query.filter(site_config__site_domain=target_domain)
        
        field_configs = query.all()
        
        fixed_count = 0
        total_patterns_fixed = 0
        
        for field_config in field_configs:
            site_domain = field_config.site_config.site_domain
            field_name = field_config.lab_equipment_field
            
            if not field_config.xpath_selectors:
                continue
                
            original_selectors = field_config.xpath_selectors.copy()
            updated_selectors = []
            patterns_changed = False
            
            for xpath in field_config.xpath_selectors:
                # Fix tab[X] pattern - convert to proper XPath
                if 'tab[X]' in xpath:
                    # Convert //[@id="tab[X]"] to //div[starts-with(@id, "tab")]
                    fixed_xpath = xpath.replace('[@id="tab[X]"]', '[starts-with(@id, "tab")]')
                    # Also ensure we have a proper element selector if missing
                    if fixed_xpath.startswith('//['):
                        fixed_xpath = fixed_xpath.replace('//[', '//div[')
                    updated_selectors.append(fixed_xpath)
                    patterns_changed = True
                    self.stdout.write(
                        f"  {site_domain} - {field_name}: "
                        f"'{xpath}' → '{fixed_xpath}'"
                    )
                else:
                    updated_selectors.append(xpath)
            
            if patterns_changed:
                if not dry_run:
                    with transaction.atomic():
                        field_config.xpath_selectors = updated_selectors
                        field_config.save()
                        
                fixed_count += 1
                total_patterns_fixed += len([x for x in original_selectors if 'tab[X]' in x])
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f"{'Would fix' if dry_run else 'Fixed'} {field_name} field for {site_domain}"
                    )
                )
        
        if fixed_count == 0:
            self.stdout.write(self.style.WARNING("No malformed XPath patterns found."))
        else:
            action = "Would fix" if dry_run else "Fixed"
            self.stdout.write(
                self.style.SUCCESS(
                    f"{action} {total_patterns_fixed} XPath pattern(s) "
                    f"across {fixed_count} field configuration(s)."
                )
            )
            
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "This was a dry run. Use without --dry-run to apply changes."
                )
            ) 