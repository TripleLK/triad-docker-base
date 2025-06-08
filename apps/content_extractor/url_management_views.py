"""
URL Management Views for Content Extractor

API endpoints for managing test URLs in the interactive selector interface.

Created by: Quantum Pulse
Date: 2025-01-22
Project: Triad Docker Base - Multi-URL Testing UX Improvements
"""

import json
import logging
from urllib.parse import urlparse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User

from .models import SiteConfiguration, FieldConfiguration
from apps.base_site.models import APIToken

logger = logging.getLogger(__name__)


def authenticate_request(request):
    """
    Custom authentication that supports both session and API token authentication.
    Now includes validation of temporary tokens with expiration checking.
    
    Returns:
        User: Authenticated user or None if authentication fails
    """
    # Check for session authentication first
    if request.user.is_authenticated:
        return request.user
    
    # Check for API token authentication
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if auth_header.startswith('Token '):
        token = auth_header.split(' ')[1]
        try:
            api_token = APIToken.objects.get(token=token, is_active=True)
            
            # Check if token is expired (handles both permanent and temporary tokens)
            if not api_token.is_valid():
                logger.warning(f"Attempted authentication with expired/invalid token: {api_token.name}")
                return None
            
            # For API token auth, we'll use a system user or create one
            system_user, created = User.objects.get_or_create(
                username='interactive_selector_system',
                defaults={
                    'first_name': 'Interactive',
                    'last_name': 'Selector',
                    'email': 'system@triad.com',
                    'is_active': True,
                    'is_staff': False,
                }
            )
            
            logger.info(f"Authenticated with {'temporary' if api_token.is_temporary else 'permanent'} token: {api_token.name}")
            return system_user
            
        except APIToken.DoesNotExist:
            logger.warning(f"Authentication failed - invalid token provided")
            pass
    
    return None


@csrf_exempt
@require_http_methods(["POST"])
def add_test_url_view(request):
    """
    Add a test URL to the current site configuration.
    
    Expected POST data:
    {
        "url": "https://example.com/test-page",
        "current_domain": "example.com"
    }
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
        
        new_url = data.get('url', '').strip()
        current_domain = data.get('current_domain', '').strip()
        
        if not new_url or not current_domain:
            return JsonResponse({
                'success': False,
                'error': 'URL and current_domain are required'
            }, status=400)
        
        # Parse and validate the new URL
        try:
            parsed_url = urlparse(new_url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise ValueError("Invalid URL format")
            
            # Check if the new URL belongs to the same domain
            new_domain = parsed_url.netloc.lower()
            if not new_domain.endswith(current_domain.lower()) and current_domain.lower() not in new_domain:
                return JsonResponse({
                    'success': False,
                    'error': f'URL must belong to the current domain ({current_domain})'
                }, status=400)
                
        except ValueError as e:
            return JsonResponse({
                'success': False,
                'error': f'Invalid URL: {str(e)}'
            }, status=400)
        
        # Get the site configuration for the current domain
        try:
            site_config = SiteConfiguration.objects.get(site_domain=current_domain)
        except SiteConfiguration.DoesNotExist:
            # Create new site configuration if it doesn't exist
            site_config = SiteConfiguration.objects.create(
                site_domain=current_domain,
                site_name=f"Site {current_domain}",
                is_active=True,
                created_by=user
            )
            logger.info(f"Created new SiteConfiguration for domain: {current_domain}")
        
        # Add the test URL
        result = site_config.add_test_url(new_url)
        
        if result['success']:
            return JsonResponse({
                'success': True,
                'message': result['message'],
                'test_urls': site_config.get_valid_test_urls(),
                'total_urls': len(site_config.get_valid_test_urls())
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result['message']
            }, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Error adding test URL: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        }, status=500)


@csrf_exempt  
@require_http_methods(["POST"])
def switch_url_view(request, direction):
    """
    Switch to next/previous test URL.
    
    Args:
        direction: 'next' or 'previous'
        
    Expected POST data:
    {
        "current_url": "https://example.com/current-page",
        "domain": "example.com"
    }
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
        
        current_url = data.get('current_url', '').strip()
        domain = data.get('domain', '').strip()
        
        if not current_url or not domain:
            return JsonResponse({
                'success': False,
                'error': 'current_url and domain are required'
            }, status=400)
        
        # Get the site configuration
        try:
            site_config = SiteConfiguration.objects.get(site_domain=domain)
        except SiteConfiguration.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': f'No site configuration found for domain: {domain}'
            }, status=404)
        
        # Get available test URLs
        test_urls = site_config.get_valid_test_urls()
        if len(test_urls) < 2:
            return JsonResponse({
                'success': False,
                'error': 'At least 2 test URLs are required for switching'
            }, status=400)
        
        # Find current URL index
        try:
            current_index = test_urls.index(current_url)
        except ValueError:
            return JsonResponse({
                'success': False,
                'error': 'Current URL not found in test URLs list'
            }, status=400)
        
        # Calculate next URL index
        if direction == 'next':
            next_index = (current_index + 1) % len(test_urls)
        elif direction == 'previous':
            next_index = (current_index - 1) % len(test_urls)
        else:
            return JsonResponse({
                'success': False,
                'error': 'Direction must be "next" or "previous"'
            }, status=400)
        
        next_url = test_urls[next_index]
        
        return JsonResponse({
            'success': True,
            'next_url': next_url,
            'current_index': current_index,
            'next_index': next_index,
            'total_urls': len(test_urls),
            'all_urls': test_urls
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Error switching URL: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_test_urls_view(request):
    """
    Get test URLs for the current domain.
    
    Query parameters:
        domain: The domain to get test URLs for
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
        test_urls = site_config.get_valid_test_urls()
        
        return JsonResponse({
            'success': True,
            'test_urls': test_urls,
            'total_urls': len(test_urls),
            'site_name': site_config.site_name,
            'domain': site_config.site_domain
        })
        
    except SiteConfiguration.DoesNotExist:
        return JsonResponse({
            'success': True,
            'test_urls': [],
            'total_urls': 0,
            'site_name': domain,
            'domain': domain,
            'message': 'No site configuration found - URLs can be added'
        })
    except Exception as e:
        logger.error(f"Error getting test URLs: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        }, status=500) 