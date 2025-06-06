import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction
from wagtail.models import Page

from .auth import token_required
from .models import (
    LabEquipmentPage, EquipmentModel, LabEquipmentPageSpecGroup,
    Spec, EquipmentFeature, LabEquipmentGalleryImage, EquipmentModelSpecGroup
)
from apps.categorized_tags.models import CategorizedTag
from apps.ai_processing.utils import fix_rich_text_html

logger = logging.getLogger(__name__)

def process_tags(tags_data):
    """
    Process tag data and return CategorizedTag objects.
    
    Accepts tags in either format:
    1. Array of objects with category and name: [{"category": "Manufacturer", "name": "Horiba"}, ...]
    2. Array of strings (legacy): ["Manufacturer: Horiba", ...] - these will be parsed
    
    Returns a list of CategorizedTag objects.
    """
    processed_tags = []
    
    for tag_data in tags_data:
        if isinstance(tag_data, dict) and 'category' in tag_data and 'name' in tag_data:
            # Process structured tag data
            category = tag_data['category'].strip()
            name = tag_data['name'].strip()
            
            # Additional check - if name contains category, split it
            if ':' in name and not category:
                parts = name.split(':', 1)
                if len(parts) == 2:
                    category = parts[0].strip()
                    name = parts[1].strip()
                    logger.info(f"Extracted category from name: '{category}' and '{name}'")
            
            # Check if tag exists (ignoring case)
            existing_tag = CategorizedTag.objects.filter(
                category__iexact=category,
                name__iexact=name
            ).first()
            
            if existing_tag:
                # Use existing tag
                processed_tags.append(existing_tag)
                logger.info(f"Using existing tag: {existing_tag}")
            else:
                # Check if a malformed version of this tag exists (full string in name, empty category)
                potential_malformed = None
                if ':' in tag_data['name']:
                    # Try to find a tag with the entire string as name and empty category
                    potential_malformed = CategorizedTag.objects.filter(
                        name__iexact=tag_data['name'].strip(),
                        category__exact=''
                    ).first()
                
                if potential_malformed:
                    # Fix and use the malformed tag
                    potential_malformed.category = category
                    potential_malformed.name = name
                    potential_malformed.save()
                    processed_tags.append(potential_malformed)
                    logger.info(f"Fixed and using tag: {potential_malformed}")
                else:
                    # Create new tag
                    try:
                        tag = CategorizedTag.objects.create(
                            category=category,
                            name=name
                        )
                        processed_tags.append(tag)
                        logger.info(f"Created new tag: {tag}")
                    except Exception as e:
                        logger.warning(f"Error creating tag {category}:{name} - {e}")
                        # If we can't create it, try to get it again (in case of race condition or slug collision)
                        existing_tag = CategorizedTag.objects.filter(
                            category__iexact=category,
                            name__iexact=name
                        ).first()
                        
                        if existing_tag:
                            processed_tags.append(existing_tag)
                            logger.info(f"Using existing tag after creation failed: {existing_tag}")
                        else:
                            # Try creating with a modified slug if it might be a slug collision
                            try:
                                import random
                                # Generate a unique suffix for the slug
                                suffix = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=5))
                                # Pre-generate the slug to avoid collision
                                from django.utils.text import slugify
                                slug = f"{slugify(f'{category}-{name}')}-{suffix}"
                                
                                tag = CategorizedTag.objects.create(
                                    category=category,
                                    name=name,
                                    slug=slug
                                )
                                processed_tags.append(tag)
                                logger.info(f"Created new tag with modified slug: {tag}")
                            except Exception as e2:
                                logger.error(f"Failed to create tag even with modified slug: {category}:{name} - {e2}")
        elif isinstance(tag_data, str):
            # Legacy string format (for backward compatibility)
            if ':' in tag_data:
                category, name = [part.strip() for part in tag_data.split(':', 1)]
                
                # Additional check - handle Manufacturer-style tags that might already exist
                # Check first if there's an existing tag with the full string as name and empty category
                potential_malformed_tag = CategorizedTag.objects.filter(
                    name__iexact=tag_data.strip(),
                    category__exact=''
                ).first()
                
                if potential_malformed_tag:
                    # Update the malformed tag to have proper category/name structure
                    potential_malformed_tag.category = category
                    potential_malformed_tag.name = name
                    potential_malformed_tag.save()
                    processed_tags.append(potential_malformed_tag)
                    logger.info(f"Fixed and using tag: {potential_malformed_tag}")
                    continue
                
                # Check if a proper tag exists (ignoring case)
                existing_tag = CategorizedTag.objects.filter(
                    category__iexact=category,
                    name__iexact=name
                ).first()
                
                if existing_tag:
                    # Use existing tag
                    processed_tags.append(existing_tag)
                    logger.info(f"Using existing tag: {existing_tag}")
                else:
                    # Create new tag
                    try:
                        tag = CategorizedTag.objects.create(
                            category=category,
                            name=name
                        )
                        processed_tags.append(tag)
                        logger.info(f"Created new tag: {tag}")
                    except Exception as e:
                        logger.warning(f"Error creating tag {category}:{name} - {e}")
                        # If we can't create it, try to get it again (in case of race condition or slug collision)
                        existing_tag = CategorizedTag.objects.filter(
                            category__iexact=category,
                            name__iexact=name
                        ).first()
                        
                        if existing_tag:
                            processed_tags.append(existing_tag)
                            logger.info(f"Using existing tag after creation failed: {existing_tag}")
                        else:
                            # Try creating with a modified slug if it might be a slug collision
                            try:
                                import random
                                # Generate a unique suffix for the slug
                                suffix = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=5))
                                # Pre-generate the slug to avoid collision
                                from django.utils.text import slugify
                                slug = f"{slugify(f'{category}-{name}')}-{suffix}"
                                
                                tag = CategorizedTag.objects.create(
                                    category=category,
                                    name=name,
                                    slug=slug
                                )
                                processed_tags.append(tag)
                                logger.info(f"Created new tag with modified slug: {tag}")
                            except Exception as e2:
                                logger.error(f"Failed to create tag even with modified slug: {category}:{name} - {e2}")
            else:
                # If no category is specified, use "General" as default
                name = tag_data.strip()
                
                # Check if tag exists (ignoring case)
                existing_tag = CategorizedTag.objects.filter(
                    category__iexact="General",
                    name__iexact=name
                ).first()
                
                if existing_tag:
                    # Use existing tag
                    processed_tags.append(existing_tag)
                    logger.info(f"Using existing tag: {existing_tag}")
                else:
                    # Create new tag
                    try:
                        tag = CategorizedTag.objects.create(
                            category="General",
                            name=name
                        )
                        processed_tags.append(tag)
                        logger.info(f"Created new tag: {tag}")
                    except Exception as e:
                        logger.warning(f"Error creating tag General:{name} - {e}")
                        # If we can't create it, try to get it again (in case of race condition or slug collision)
                        existing_tag = CategorizedTag.objects.filter(
                            category__iexact="General",
                            name__iexact=name
                        ).first()
                        
                        if existing_tag:
                            processed_tags.append(existing_tag)
                            logger.info(f"Using existing tag after creation failed: {existing_tag}")
                        else:
                            # Try creating with a modified slug if it might be a slug collision
                            try:
                                import random
                                # Generate a unique suffix for the slug
                                suffix = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=5))
                                # Pre-generate the slug to avoid collision
                                from django.utils.text import slugify
                                slug = f"{slugify(f'General-{name}')}-{suffix}"
                                
                                tag = CategorizedTag.objects.create(
                                    category="General",
                                    name=name,
                                    slug=slug
                                )
                                processed_tags.append(tag)
                                logger.info(f"Created new tag with modified slug: {tag}")
                            except Exception as e2:
                                logger.error(f"Failed to create tag even with modified slug: General:{name} - {e2}")
    
    return processed_tags

@csrf_exempt
@token_required
@require_http_methods(["POST"])
def create_or_update_lab_equipment(request):
    """
    Create or update a lab equipment page based on JSON data
    """
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['title', 'short_description']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return JsonResponse({
                'success': False,
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }, status=400)
        
        # Check if we're updating an existing page or creating a new one
        slug = data.get('slug')
        existing_page = None
        
        if slug:
            try:
                existing_page = LabEquipmentPage.objects.get(slug=slug)
            except LabEquipmentPage.DoesNotExist:
                pass
        
        # Process tags separately before entering transaction
        if 'tags' in data and data['tags']:
            try:
                processed_tags = process_tags(data['tags'])
                # Replace original tags data with processed tag IDs
                data['processed_tag_ids'] = [tag.id for tag in processed_tags]
            except Exception as e:
                logger.exception("Error processing tags")
                return JsonResponse({
                    'success': False,
                    'error': f'Error processing tags: {str(e)}'
                }, status=400)
        
        # Begin transaction to ensure data consistency
        with transaction.atomic():
            if existing_page:
                # Update existing page
                result = update_lab_equipment_page(existing_page, data)
                status_code = 200
                action = "updated"
            else:
                # Create new page
                result = create_lab_equipment_page(data)
                status_code = 201  # Created
                action = "created"
            
            if not result['success']:
                return JsonResponse(result, status=400)
            
            return JsonResponse({
                'success': True,
                'message': f'Lab equipment page {action} successfully',
                'page_id': result['page_id'],
                'page_slug': result['page_slug']
            }, status=status_code)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON format in request body'
        }, status=400)
    except Exception as e:
        logger.exception("Error processing lab equipment data")
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }, status=500)

@csrf_exempt
@token_required
@require_http_methods(["POST"])
def approve_review_item(request):
    """
    Mark a lab equipment page as reviewed (no longer needs review)
    """
    try:
        data = json.loads(request.body)
        
        if 'item_id' not in data:
            return JsonResponse({
                'success': False,
                'error': 'Missing item_id field'
            }, status=400)
        
        item_id = data['item_id']
        
        try:
            item = LabEquipmentPage.objects.get(id=item_id)
        except LabEquipmentPage.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': f'Item with id {item_id} not found'
            }, status=404)
        
        # Update the needs_review flag
        item.needs_review = False
        
        # Save and publish
        rev = item.save_revision()
        rev.publish()
        
        return JsonResponse({
            'success': True,
            'message': f'Item {item_id} marked as reviewed'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON format in request body'
        }, status=400)
    except Exception as e:
        logger.exception("Error approving review item")
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }, status=500)

def evaluate_data_quality(data):
    """
    Evaluates the quality and completeness of the provided data.
    Returns a dict with data quality metrics.
    """
    quality_metrics = {
        'source_type': 'unknown',
        'data_completeness': 1.0,
        'specification_confidence': 'high',
        'needs_review': False
    }
    
    # Check if source_type is already provided
    if 'source_type' in data:
        quality_metrics['source_type'] = data['source_type']
    else:
        # Try to infer source_type from title or description
        title = data.get('title', '').lower()
        desc = data.get('short_description', '').lower() + data.get('full_description', '').lower()
        
        if any(term in title or term in desc for term in ['used', 'refurbished', 'pre-owned', 'secondhand']):
            if 'refurbished' in title or 'refurbished' in desc:
                quality_metrics['source_type'] = 'refurbished'
            else:
                quality_metrics['source_type'] = 'used'
        else:
            quality_metrics['source_type'] = 'new'
    
    # Calculate completeness score
    completeness_checks = [
        0.2 if data.get('title') else 0,
        0.1 if data.get('short_description') else 0,
        0.1 if data.get('full_description') else 0,
        0.2 if data.get('models') and len(data.get('models', [])) > 0 else 0,
        0.2 if data.get('specifications') and len(data.get('specifications', [])) > 0 else 0,
        0.1 if data.get('images') and len(data.get('images', [])) > 0 else 0,
        0.1 if data.get('source_url') else 0
    ]
    
    quality_metrics['data_completeness'] = sum(completeness_checks)
    
    # Determine specification confidence
    if quality_metrics['source_type'] in ['used', 'refurbished']:
        # Used equipment listings often have less reliable specs
        spec_count = sum(len(group.get('specs', [])) for group in data.get('specifications', []))
        model_count = len(data.get('models', []))
        
        if spec_count < 3 or model_count == 0:
            quality_metrics['specification_confidence'] = 'low'
        elif spec_count < 8:
            quality_metrics['specification_confidence'] = 'medium'
        else:
            quality_metrics['specification_confidence'] = 'high'
    
    # Override specification_confidence if provided
    if 'specification_confidence' in data:
        quality_metrics['specification_confidence'] = data['specification_confidence']
        
    # Flag for review if completeness is low, confidence is medium/low, or equipment is used/refurbished
    if (quality_metrics['data_completeness'] < 0.7 or 
        quality_metrics['specification_confidence'] in ['low', 'medium'] or
        quality_metrics['source_type'] in ['used', 'refurbished']):
        quality_metrics['needs_review'] = True
    
    # Override needs_review if explicitly provided
    if 'needs_review' in data:
        quality_metrics['needs_review'] = data['needs_review']
    
    return quality_metrics

def create_lab_equipment_page(data):
    """
    Create a new lab equipment page from the provided data
    """
    try:
        # Find the parent page - assuming the first MultiProductPage as parent
        from wagtail.models import Site
        site = Site.objects.first()
        root_page = site.root_page
        
        # Try to find a MultiProductPage to use as parent
        from .models import MultiProductPage
        parent_pages = MultiProductPage.objects.live()
        
        if not parent_pages.exists():
            # Fallback to the root page if no MultiProductPage exists
            parent_page = root_page
        else:
            parent_page = parent_pages.first()
            
        # Evaluate data quality if not already provided
        quality_metrics = evaluate_data_quality(data)
        
        # Fix any HTML issues in the full description
        full_description = fix_rich_text_html(data.get('full_description', ''))
        
        # Create the basic page
        page = LabEquipmentPage(
            title=data['title'],
            short_description=data.get('short_description', ''),
            full_description=full_description,
            source_url=data.get('source_url', ''),
            source_type=data.get('source_type', quality_metrics['source_type']),
            data_completeness=data.get('data_completeness', quality_metrics['data_completeness']),
            specification_confidence=data.get('specification_confidence', quality_metrics['specification_confidence']),
            needs_review=data.get('needs_review', quality_metrics['needs_review']),
            live=False  # Explicitly set as not live
        )
        
        # Set slug if provided, otherwise it will be auto-generated
        if data.get('slug'):
            page.slug = data['slug']
            
        # Add to parent page
        parent_page.add_child(instance=page)
        
        # Save to generate initial revision
        rev = page.save_revision()
        
        # Check if we should publish or keep as draft
        # Default to draft for AI-created pages (only publish if explicitly requested)
        is_published = data.get('is_published', False)
        if is_published:
            rev.publish()
        
        # Add categorized tags if provided
        if 'processed_tag_ids' in data and data['processed_tag_ids']:
            # Get tags by pre-processed IDs
            from apps.categorized_tags.models import CategorizedTag
            tags = CategorizedTag.objects.filter(id__in=data['processed_tag_ids'])
            if tags.exists():
                page.categorized_tags.add(*tags)
                page.save()
        
        # Add specifications
        if 'specifications' in data and data['specifications']:
            add_specifications(page, data['specifications'])
        
        # Add models
        if 'models' in data and data['models']:
            add_models(page, data['models'])
        
        # Add gallery images
        if 'images' in data and data['images']:
            add_gallery_images(page, data['images'])
        
        # Final save - make sure to NOT publish
        rev = page.save_revision()
        if is_published:
            rev.publish()
        else:
            # Make sure the page is not live
            if page.live:
                page.live = False
                page.save()
        
        return {
            'success': True,
            'page_id': page.id,
            'page_slug': page.slug
        }
        
    except Exception as e:
        logger.exception("Error creating lab equipment page")
        return {
            'success': False,
            'error': f'Error creating lab equipment page: {str(e)}'
        }

def update_lab_equipment_page(page, data):
    """
    Update an existing lab equipment page with the provided data
    """
    try:
        # Evaluate data quality if not already provided
        quality_metrics = evaluate_data_quality(data)
        
        # Update basic fields
        if 'title' in data:
            page.title = data['title']
        
        if 'short_description' in data:
            page.short_description = data['short_description']
        
        if 'full_description' in data:
            # Fix any HTML issues in the full description
            fixed_description = fix_rich_text_html(data['full_description'])
            page.full_description = fixed_description
            
        if 'source_url' in data:
            page.source_url = data['source_url']
            
        # Update quality fields
        if 'source_type' in data:
            page.source_type = data['source_type']
        else:
            page.source_type = quality_metrics['source_type']
            
        if 'data_completeness' in data:
            page.data_completeness = data['data_completeness']
        else:
            page.data_completeness = quality_metrics['data_completeness']
            
        if 'specification_confidence' in data:
            page.specification_confidence = data['specification_confidence']
        else:
            page.specification_confidence = quality_metrics['specification_confidence']
            
        if 'needs_review' in data:
            page.needs_review = data['needs_review']
        else:
            page.needs_review = quality_metrics['needs_review']

        # Set the page as draft (not live) unless explicitly requested to publish
        is_published = data.get('is_published', False)
        if not is_published:
            page.live = False
            
        # Save the page
        rev = page.save_revision()
        
        # Check if we should publish or keep as draft
        # Default to draft for AI-created pages (only publish if explicitly requested)
        if is_published:
            rev.publish()
        
        # Update categorized tags if provided
        if 'processed_tag_ids' in data and data['processed_tag_ids']:
            from apps.categorized_tags.models import CategorizedTag
            
            # Clear existing tags first
            page.categorized_tags.clear()
            
            # Get tags by pre-processed IDs
            tags = CategorizedTag.objects.filter(id__in=data['processed_tag_ids'])
            if tags.exists():
                page.categorized_tags.add(*tags)
                page.save()
        
        # Clear and re-add specifications
        if 'specifications' in data:
            # Clear existing specs
            for spec_group in page.spec_groups.all():
                spec_group.delete()
            
            # Add new specs
            if data['specifications']:
                add_specifications(page, data['specifications'])
        
        # Clear and re-add models
        if 'models' in data:
            # Clear existing models
            for model in page.models.all():
                model.delete()
            
            # Add new models
            if data['models']:
                add_models(page, data['models'])
        
        # Clear and re-add images
        if 'images' in data:
            # Clear existing images
            page.gallery_images.all().delete()
            
            # Add new images
            if data['images']:
                add_gallery_images(page, data['images'])
        
        # Final save - make sure it stays as a draft unless explicitly requested to publish
        rev = page.save_revision()
        if is_published:
            rev.publish()
        else:
            # Double-check that the page is not live
            if page.live:
                page.live = False
                page.save()
        
        return {
            'success': True,
            'page_id': page.id,
            'page_slug': page.slug
        }
        
    except Exception as e:
        logger.exception("Error updating lab equipment page")
        return {
            'success': False,
            'error': f'Error updating lab equipment page: {str(e)}'
        }

def add_specifications(page, specifications):
    """Add specification groups and specs to a page"""
    for group_data in specifications:
        if 'name' not in group_data or 'specs' not in group_data:
            continue
            
        # Create spec group
        spec_group = LabEquipmentPageSpecGroup.objects.create(
            LabEquipmentPage=page,
            name=group_data['name']
        )
        
        # Add specs to the group
        for spec_data in group_data['specs']:
            if 'key' not in spec_data or 'value' not in spec_data:
                continue
                
            Spec.objects.create(
                spec_group=spec_group,
                key=spec_data['key'],
                value=spec_data['value']
            )

def add_models(page, models_data):
    """Add equipment models to a page"""
    logger.info(f"Adding {len(models_data)} models to page '{page.title}' (ID: {page.id})")
    models_created = 0
    
    for i, model_data in enumerate(models_data):
        model_name = model_data.get('name', f'[No name {i}]')
        logger.info(f"Processing model {i+1}: {model_name}")
        
        if 'name' not in model_data:
            logger.warning(f"Skipping model {i+1} because it has no name")
            continue
            
        # Create model
        try:
            equipment_model = EquipmentModel.objects.create(
                page=page,
                name=model_data['name']
            )
            models_created += 1
            logger.info(f"Created equipment model: {model_data['name']}")
            
            # Add specifications if provided
            if 'specifications' in model_data and model_data['specifications']:
                spec_groups_created = 0
                
                for group_data in model_data['specifications']:
                    if 'name' not in group_data or 'specs' not in group_data:
                        logger.warning(f"Skipping spec group in model {model_data['name']} - missing name or specs")
                        continue
                        
                    # Create spec group
                    spec_group = EquipmentModelSpecGroup.objects.create(
                        equipment_model=equipment_model,
                        name=group_data['name']
                    )
                    spec_groups_created += 1
                    
                    # Add specs to the group
                    specs_created = 0
                    for spec_data in group_data['specs']:
                        if 'key' not in spec_data or 'value' not in spec_data:
                            logger.warning(f"Skipping spec in group {group_data['name']} - missing key or value")
                            continue
                            
                        Spec.objects.create(
                            spec_group=spec_group,
                            key=spec_data['key'],
                            value=spec_data['value']
                        )
                        specs_created += 1
                    
                    logger.debug(f"Added {specs_created} specs to group '{group_data['name']}' for model '{model_data['name']}'")
                
                logger.info(f"Added {spec_groups_created} specification groups to model '{model_data['name']}'")
            else:
                logger.debug(f"No specifications provided for model '{model_data['name']}'")
        except Exception as e:
            logger.error(f"Error creating model '{model_data['name']}': {str(e)}")
    
    logger.info(f"Created {models_created} models for page '{page.title}' (ID: {page.id})")
    return models_created

def add_gallery_images(page, images):
    """Add gallery images to a page"""
    for image_data in images:
        # Check if it's an external URL
        if isinstance(image_data, str):
            # It's a URL string
            LabEquipmentGalleryImage.objects.create(
                page=page,
                external_image_url=image_data
            )
        elif isinstance(image_data, dict):
            # It's a dict with either internal_image or external_image_url
            gallery_image = LabEquipmentGalleryImage(page=page)
            
            if 'internal_image' in image_data and image_data['internal_image']:
                # This requires handling the image upload separately
                # For now, we'll skip internal images in the API
                pass
            
            if 'external_image_url' in image_data and image_data['external_image_url']:
                gallery_image.external_image_url = image_data['external_image_url']
                gallery_image.save() 