"""
Content Extractor Views

Views for managing site configuration and XPath selectors.
Handles API endpoints for saving and retrieving field configurations.

Created by: Silver Raven  
Date: 2025-01-22
Project: Triad Docker Base - Site Configuration System
"""

import json
import logging
from urllib.parse import urlparse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate
from django.utils import timezone
from .models import SiteConfiguration, FieldConfiguration
from apps.base_site.models import APIToken
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


def authenticate_request(request):
    """
    Authenticate API requests using either session authentication or API token.
    
    Returns:
        User object if authenticated, None otherwise
    """
    # Check session authentication first
    if request.user.is_authenticated:
        return request.user
    
    # Check for API token in Authorization header
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if auth_header.startswith('Token '):
        token_key = auth_header[6:]  # Remove 'Token ' prefix
        
        # For development: allow placeholder token
        if token_key == 'PLACEHOLDER_TOKEN_NEEDS_DYNAMIC_GENERATION':
            admin_user = User.objects.filter(is_superuser=True).first()
            if admin_user:
                logger.info(f"Development: Using placeholder token authentication for user: {admin_user.username}")
                return admin_user
            else:
                # If no admin user exists, create a default one for development
                staff_user = User.objects.filter(is_staff=True).first()
                if staff_user:
                    logger.info(f"Development: Using placeholder token authentication for staff user: {staff_user.username}")
                    return staff_user
                else:
                    # Create a temporary superuser for development
                    logger.info("Development: Creating temporary superuser for placeholder token authentication")
                    temp_user = User.objects.create_user(
                        username='dev_user',
                        email='dev@example.com',
                        is_superuser=True,
                        is_staff=True
                    )
                    return temp_user
        
        try:
            # Check permanent tokens
            api_token = APIToken.objects.get(
                token=token_key,
                is_active=True
            )
            # Since APIToken doesn't have a user field, return first admin user for development
            admin_user = User.objects.filter(is_superuser=True).first()
            if admin_user:
                return admin_user
            else:
                # If no admin user exists, create a default one for development
                return User.objects.filter(is_staff=True).first()
        except APIToken.DoesNotExist:
            # Check temporary tokens
            try:
                api_token = APIToken.objects.get(
                    token=token_key,
                    is_active=True,
                    is_temporary=True,
                    expires_at__gt=timezone.now()
                )
                # Since APIToken doesn't have a user field, return first admin user for development
                admin_user = User.objects.filter(is_superuser=True).first()
                if admin_user:
                    return admin_user
                else:
                    # If no admin user exists, create a default one for development
                    return User.objects.filter(is_staff=True).first()
            except APIToken.DoesNotExist:
                pass
    
    return None


@csrf_exempt
@require_http_methods(["POST"])
def save_xpath_configuration(request):
    """
    Save XPath configuration for field(s) on a specific site domain.
    
    Supports two data formats:
    
    Single field format:
    {
        "domain": "example.com",
        "field": "title",
        "xpath": "//h1[@class='product-title']",
        "comment": "Main product title"
    }
    
    Multiple fields format (from frontend):
    {
        "domain": "example.com",
        "site_name": "Site Name",
        "field_mappings": {
            "title": {
                "xpath_selectors": ["//h1"],
                "comment": "Title field"
            }
        }
    }
    
    Returns:
        JSON response with success status and details
    """
    # Authenticate the request
    user = authenticate_request(request)
    if not user:
        return JsonResponse({
            'success': False,
            'error': 'Authentication required. Please login or provide API token.'
        }, status=401)
    
    try:
        data = json.loads(request.body)
        logger.info(f"Received save configuration request: {data}")
        
        domain = data.get('domain', '').strip()
        if not domain:
            return JsonResponse({
                'success': False,
                'error': 'domain is required'
            }, status=400)
        
        # Check if this is the new frontend format with field_mappings
        if 'field_mappings' in data:
            # Handle multiple field mappings format from frontend
            field_mappings = data.get('field_mappings', {})
            site_name = data.get('site_name', f"Site {domain}")
            
            if not field_mappings:
                return JsonResponse({
                    'success': False,
                    'error': 'field_mappings is required and cannot be empty'
                }, status=400)
            
            # Get or create site configuration
            site_config, created = SiteConfiguration.objects.get_or_create(
                site_domain=domain,
                defaults={
                    'site_name': site_name,
                    'is_active': True,
                    'created_by': user
                }
            )
            
            if created:
                logger.info(f"Created new SiteConfiguration for domain: {domain}")
            elif site_name and site_config.site_name != site_name:
                # Update site name if provided and different
                site_config.site_name = site_name
                site_config.save()
            
            # ARCTIC STORM: Auto-delete missing fields
            # Get all existing field configurations for this site
            existing_field_configs = FieldConfiguration.objects.filter(
                site_config=site_config,
                is_active=True
            )
            
            # Determine which fields should be deleted (were saved before but not in current request)
            current_fields = set(field_mappings.keys())
            existing_fields = set(config.lab_equipment_field for config in existing_field_configs)
            fields_to_delete = existing_fields - current_fields
            
            deleted_fields = []
            if fields_to_delete:
                logger.info(f"ARCTIC STORM: Auto-deleting missing fields for {domain}: {fields_to_delete}")
                for field_name in fields_to_delete:
                    try:
                        deleted_count, _ = FieldConfiguration.objects.filter(
                            site_config=site_config,
                            lab_equipment_field=field_name,
                            is_active=True
                        ).update(is_active=False)
                        
                        if deleted_count > 0:
                            deleted_fields.append(field_name)
                            logger.info(f"ARCTIC STORM: Deleted field configuration for {field_name}")
                        
                    except Exception as delete_error:
                        logger.error(f"ARCTIC STORM: Error deleting field {field_name}: {delete_error}")
                        errors.append(f'Error deleting field "{field_name}": {str(delete_error)}')
            
            # Process provided field mappings
            saved_fields = []
            updated_fields = []
            errors = []
            
            for field_name, field_data in field_mappings.items():
                try:
                    # Validate field is a valid LabEquipmentPage field
                    valid_fields = [choice[0] for choice in FieldConfiguration.LAB_EQUIPMENT_FIELD_CHOICES]
                    if field_name not in valid_fields:
                        errors.append(f'Invalid field "{field_name}". Valid fields are: {", ".join(valid_fields)}')
                        continue
                    
                    xpath_selectors = field_data.get('xpath_selectors', [])
                    comment = field_data.get('comment', '')
                    
                    if not xpath_selectors:
                        errors.append(f'Field "{field_name}" has no xpath_selectors')
                        continue
                    
                    # Get or create field configuration
                    field_config, created = FieldConfiguration.objects.get_or_create(
                        site_config=site_config,
                        lab_equipment_field=field_name,
                        defaults={
                            'xpath_selectors': xpath_selectors,
                            'comment': comment,
                            'is_active': True,
                            'created_by': user
                        }
                    )
                    
                    if not created:
                        # Update existing field configuration
                        field_config.xpath_selectors = xpath_selectors
                        field_config.comment = comment
                        field_config.save()
                        logger.info(f"Updated FieldConfiguration for {domain} - {field_name}")
                        updated_fields.append(field_name)
                    else:
                        logger.info(f"Created new FieldConfiguration for {domain} - {field_name}")
                    
                    saved_fields.append({
                        'field': field_name,
                        'xpath_count': len(xpath_selectors),
                        'field_config_id': field_config.id
                    })
                    
                except Exception as field_error:
                    errors.append(f'Error processing field "{field_name}": {str(field_error)}')
            
            if errors and not saved_fields:
                return JsonResponse({
                    'success': False,
                    'error': f'Failed to save any fields: {"; ".join(errors)}'
                }, status=400)
            
            # ARCTIC STORM: Enhanced response with deletion info
            total_operations = len(saved_fields) + len(deleted_fields) + len(updated_fields)
            message_parts = []
            
            if saved_fields:
                new_count = len([f for f in saved_fields if f['field'] not in updated_fields])
                message_parts.append(f'{new_count} new field(s)')
            if updated_fields:
                message_parts.append(f'{len(updated_fields)} updated field(s)')
            if deleted_fields:
                message_parts.append(f'{len(deleted_fields)} deleted field(s)')
            
            message = f'Configuration processed: {", ".join(message_parts)} for {domain}'
            
            return JsonResponse({
                'success': True,
                'message': message,
                'domain': domain,
                'site_name': site_config.site_name,
                'saved_fields': saved_fields,
                'updated_fields': updated_fields,
                'deleted_fields': deleted_fields,
                'total_fields': site_config.configured_fields_count,
                'site_config_id': site_config.id,
                'configured_fields': site_config.configured_fields_count,
                'errors': errors if errors else None
            })
        
        else:
            # Handle original single field format
            field = data.get('field', '').strip()
            xpath = data.get('xpath', '').strip()
            comment = data.get('comment', '').strip()
            
            if not all([field, xpath]):
                return JsonResponse({
                    'success': False,
                    'error': 'field and xpath are required'
                }, status=400)
            
            # Validate field is a valid LabEquipmentPage field
            valid_fields = [choice[0] for choice in FieldConfiguration.LAB_EQUIPMENT_FIELD_CHOICES]
            if field not in valid_fields:
                return JsonResponse({
                    'success': False,
                    'error': f'Invalid field. Valid fields are: {", ".join(valid_fields)}'
                }, status=400)
            
            # Get or create site configuration
            site_config, created = SiteConfiguration.objects.get_or_create(
                site_domain=domain,
                defaults={
                    'site_name': f"Site {domain}",
                    'is_active': True,
                    'created_by': user
                }
            )
            
            if created:
                logger.info(f"Created new SiteConfiguration for domain: {domain}")
            
            # Get or create field configuration
            field_config, created = FieldConfiguration.objects.get_or_create(
                site_config=site_config,
                lab_equipment_field=field,
                defaults={
                    'xpath_selectors': [xpath],
                    'comment': comment,
                    'is_active': True,
                    'created_by': user
                }
            )
            
            if not created:
                # Update existing field configuration
                if not field_config.xpath_selectors:
                    field_config.xpath_selectors = []
                
                # Add xpath if not already present
                if xpath not in field_config.xpath_selectors:
                    field_config.xpath_selectors.append(xpath)
                
                # Update comment if provided
                if comment:
                    field_config.comment = comment
                
                field_config.save()
                logger.info(f"Updated FieldConfiguration for {domain} - {field}")
            else:
                logger.info(f"Created new FieldConfiguration for {domain} - {field}")
            
            return JsonResponse({
                'success': True,
                'message': f'XPath configuration saved for {field} on {domain}',
                'field_config_id': field_config.id,
                'xpath_count': len(field_config.xpath_selectors),
                'site_config_id': site_config.id,
                'configured_fields': site_config.configured_fields_count
            })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Error saving XPath configuration: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_site_configuration(request):
    """
    Get site configuration and field mappings for a specific domain.
    
    Query parameters:
        domain: The domain to get configuration for
    
    Returns:
        JSON response with field mappings and site configuration
    """
    # Authenticate the request
    user = authenticate_request(request)
    if not user:
        return JsonResponse({
            'success': False,
            'error': 'Authentication required. Please login or provide API token.'
        }, status=401)
    
    domain = request.GET.get('domain', '').strip()
    if not domain:
        return JsonResponse({
            'success': False,
            'error': 'domain parameter is required'
        }, status=400)
    
    try:
        site_config = SiteConfiguration.objects.get(site_domain=domain)
        
        # Get all field configurations for this site
        field_configs = FieldConfiguration.objects.filter(
            site_config=site_config,
            is_active=True
        ).select_related('site_config')
        
        # Build field mappings
        field_mappings = {}
        for field_config in field_configs:
            field_mappings[field_config.lab_equipment_field] = {
                'xpath_selectors': field_config.xpath_selectors,
                'comment': field_config.comment,
                'field_display_name': field_config.get_lab_equipment_field_display(),
                'xpath_count': field_config.xpath_count,
                'created_at': field_config.created_at.isoformat(),
                'updated_at': field_config.updated_at.isoformat()
            }
        
        return JsonResponse({
            'success': True,
            'domain': domain,
            'site_name': site_config.site_name,
            'field_mappings': field_mappings,
            'configured_fields_count': len(field_mappings),
            'site_is_active': site_config.is_active,
            'site_notes': site_config.notes,
            'site_created_at': site_config.created_at.isoformat(),
            'site_updated_at': site_config.updated_at.isoformat()
        })
        
    except SiteConfiguration.DoesNotExist:
        return JsonResponse({
            'success': True,
            'domain': domain,
            'site_name': f"Site {domain}",
            'field_mappings': {},
            'configured_fields_count': 0,
            'message': 'No site configuration found for this domain'
        })
    except Exception as e:
        logger.error(f"Error getting site configuration: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def delete_xpath_configuration(request):
    """
    Delete XPath configuration for a specific field on a domain.
    
    Expected format:
    {
        "domain": "example.com",
        "field": "title",
        "xpath": "//h1[@class='product-title']"  // optional - if not provided, clears all selectors for field
    }
    
    Returns:
        JSON response with success status and details
    """
    # Authenticate the request
    user = authenticate_request(request)
    if not user:
        return JsonResponse({
            'success': False,
            'error': 'Authentication required. Please login or provide API token.'
        }, status=401)
    
    try:
        data = json.loads(request.body)
        logger.info(f"Received delete configuration request: {data}")
        
        domain = data.get('domain', '').strip()
        field = data.get('field', '').strip()
        xpath_to_remove = data.get('xpath', '').strip()
        
        if not all([domain, field]):
            return JsonResponse({
                'success': False,
                'error': 'domain and field are required'
            }, status=400)
        
        # Validate field is a valid LabEquipmentPage field
        valid_fields = [choice[0] for choice in FieldConfiguration.LAB_EQUIPMENT_FIELD_CHOICES]
        if field not in valid_fields:
            return JsonResponse({
                'success': False,
                'error': f'Invalid field. Valid fields are: {", ".join(valid_fields)}'
            }, status=400)
        
        try:
            site_config = SiteConfiguration.objects.get(site_domain=domain)
            field_config = FieldConfiguration.objects.get(
                site_config=site_config,
                lab_equipment_field=field
            )
            
            if xpath_to_remove:
                # Remove specific XPath selector
                if field_config.xpath_selectors and xpath_to_remove in field_config.xpath_selectors:
                    field_config.xpath_selectors.remove(xpath_to_remove)
                    field_config.save()
                    
                    if field_config.xpath_selectors:
                        message = f'Removed XPath selector for {field} on {domain}'
                        remaining_count = len(field_config.xpath_selectors)
                    else:
                        # If no selectors left, deactivate the field configuration
                        field_config.is_active = False
                        field_config.save()
                        message = f'Removed last XPath selector for {field} on {domain} - field deactivated'
                        remaining_count = 0
                    
                    logger.info(f"Removed XPath selector: {xpath_to_remove} for {domain}/{field}")
                    return JsonResponse({
                        'success': True,
                        'message': message,
                        'field': field,
                        'domain': domain,
                        'removed_xpath': xpath_to_remove,
                        'remaining_xpath_count': remaining_count,
                        'field_active': field_config.is_active
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': f'XPath selector not found in field configuration: {xpath_to_remove}'
                    }, status=404)
            else:
                # Clear all XPath selectors for the field
                removed_count = len(field_config.xpath_selectors) if field_config.xpath_selectors else 0
                field_config.xpath_selectors = []
                field_config.is_active = False
                field_config.save()
                
                logger.info(f"Cleared all XPath selectors for {domain}/{field}")
                return JsonResponse({
                    'success': True,
                    'message': f'Cleared all XPath selectors for {field} on {domain}',
                    'field': field,
                    'domain': domain,
                    'removed_xpath_count': removed_count,
                    'remaining_xpath_count': 0,
                    'field_active': False
                })
                
        except SiteConfiguration.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': f'Site configuration not found for domain: {domain}'
            }, status=404)
        except FieldConfiguration.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': f'Field configuration not found for {field} on domain: {domain}'
            }, status=404)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Error deleting XPath configuration: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        }, status=500)
