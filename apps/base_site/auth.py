from functools import wraps
from django.http import JsonResponse
from .models import APIToken

def token_required(view_func):
    """
    Decorator to check if the request has a valid API token.
    Usage: @token_required
    """
    @wraps(view_func)
    def decorated_view(request, *args, **kwargs):
        # Check for the token in the Authorization header
        auth_header = request.headers.get('Authorization', '')
        
        # Also check in query parameters for testing
        query_token = request.GET.get('token')
        
        # Extract token from Authorization header
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        elif query_token:
            token = query_token
        else:
            return JsonResponse({
                'success': False,
                'error': 'API token is missing. Provide a token in the Authorization header.'
            }, status=401)
        
        # Validate token
        try:
            token_obj = APIToken.objects.get(token=token, is_active=True)
        except APIToken.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Invalid or inactive API token.'
            }, status=401)
            
        # Add token to request for potential logging
        request.api_token = token_obj
        
        # Continue to the view
        return view_func(request, *args, **kwargs)
    
    return decorated_view 