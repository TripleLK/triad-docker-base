"""
Lab Equipment API v2 Permissions - Custom permission classes for different access levels.

Created by: Noble Harbor
Date: 2025-01-19
Project: Triad Docker Base
"""

from rest_framework.permissions import BasePermission, IsAuthenticated
from django.contrib.auth.models import User


class APIBasePermission(BasePermission):
    """
    Base permission class with common functionality for Lab Equipment API v2.
    
    Provides foundation for all custom permission classes with shared validation
    methods and error messaging.
    """
    
    def has_permission(self, request, view):
        """
        Default permission check - requires authentication.
        Override in subclasses for specific permission logic.
        """
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """
        Default object-level permission check.
        Override in subclasses for specific object permissions.
        """
        return self.has_permission(request, view)
    
    def get_permission_denied_message(self):
        """
        Custom error message for permission denied scenarios.
        Override in subclasses for specific messaging.
        """
        return "You do not have permission to perform this action on the Lab Equipment API."


class AdminPermission(APIBasePermission):
    """
    Full access permission for administrators.
    
    Grants complete access to all API operations including:
    - All CRUD operations on equipment, tags, specifications, models
    - Batch operations management and monitoring
    - System configuration and settings
    - User management and audit logs
    - Advanced analytics and reporting
    """
    
    def has_permission(self, request, view):
        """Admin permission requires superuser or staff status."""
        return (
            request.user and 
            request.user.is_authenticated and 
            (request.user.is_superuser or request.user.is_staff)
        )
    
    def get_permission_denied_message(self):
        return "Administrator privileges required for this operation."


class BatchUserPermission(APIBasePermission):
    """
    Permission for users who can create and manage batch operations.
    
    Grants access to:
    - Batch equipment creation, updates, and deletions
    - Batch operation monitoring and progress tracking
    - Validation result review and error resolution
    - Equipment CRUD operations (individual and batch)
    - Tag and specification management
    """
    
    def has_permission(self, request, view):
        """
        Batch user permission requires authentication and either:
        - Staff status
        - Membership in 'batch_users' group
        - Custom 'can_batch_operations' permission
        """
        if not (request.user and request.user.is_authenticated):
            return False
            
        # Staff users automatically have batch permissions
        if request.user.is_staff or request.user.is_superuser:
            return True
            
        # Check for batch_users group membership
        if request.user.groups.filter(name='batch_users').exists():
            return True
            
        # Check for custom permission
        return request.user.has_perm('lab_equipment_api.can_batch_operations')
    
    def has_object_permission(self, request, view, obj):
        """
        Object-level permission for batch operations.
        Users can manage their own batch operations.
        """
        if not self.has_permission(request, view):
            return False
            
        # Staff can access all batch operations
        if request.user.is_staff or request.user.is_superuser:
            return True
            
        # Users can only access their own batch operations
        if hasattr(obj, 'api_request') and hasattr(obj.api_request, 'user'):
            return obj.api_request.user == request.user
            
        return False
    
    def get_permission_denied_message(self):
        return "Batch operation permissions required. Contact administrator for access."


class ReadOnlyPermission(APIBasePermission):
    """
    Read-only permission for viewing equipment data.
    
    Grants access to:
    - View equipment, tags, specifications, and models
    - Search and filter operations
    - Export data in various formats
    - Basic statistics and reports
    
    Denies access to:
    - Creating, updating, or deleting equipment
    - Batch operations
    - System configuration changes
    """
    
    def has_permission(self, request, view):
        """Read-only permission allows authenticated users for safe methods."""
        if not (request.user and request.user.is_authenticated):
            return False
            
        # Allow read operations for all authenticated users
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
            
        # Staff can perform write operations
        if request.user.is_staff or request.user.is_superuser:
            return True
            
        # Check for specific write permissions
        return request.user.has_perm('lab_equipment_api.can_modify_equipment')
    
    def get_permission_denied_message(self):
        return "Read-only access granted. Contact administrator for modification permissions."


class ExternalAPIPermission(APIBasePermission):
    """
    Limited permission for external integrations and third-party systems.
    
    Grants access to:
    - Equipment data viewing with rate limiting
    - Specific API endpoints designed for external access
    - Basic search and filtering capabilities
    
    Denies access to:
    - Sensitive system information
    - User management functions
    - Administrative operations
    - Unrestricted batch operations
    """
    
    def has_permission(self, request, view):
        """
        External API permission requires authentication and specific group membership.
        Designed for service accounts and external integrations.
        """
        if not (request.user and request.user.is_authenticated):
            return False
            
        # Check for external_api_users group membership
        if request.user.groups.filter(name='external_api_users').exists():
            return True
            
        # Check for specific external API permission
        return request.user.has_perm('lab_equipment_api.external_api_access')
    
    def has_object_permission(self, request, view, obj):
        """
        Object-level permission for external API access.
        Restricted to non-sensitive data only.
        """
        if not self.has_permission(request, view):
            return False
            
        # External APIs cannot access error logs or sensitive audit data
        sensitive_models = ['ErrorLog', 'APIRequest']
        if obj.__class__.__name__ in sensitive_models:
            return False
            
        return True
    
    def get_permission_denied_message(self):
        return "External API access limited. Contact administrator for expanded permissions."


class InternalSystemPermission(APIBasePermission):
    """
    High-level permission for internal system operations.
    
    Grants access to:
    - System health monitoring and diagnostics
    - Internal API operations and maintenance
    - Cross-system integration endpoints
    - Performance monitoring and optimization
    
    Intended for:
    - Internal microservices
    - System monitoring tools
    - Administrative automation
    - Health check systems
    """
    
    def has_permission(self, request, view):
        """
        Internal system permission requires authentication and specific group membership.
        Designed for internal services and system accounts.
        """
        if not (request.user and request.user.is_authenticated):
            return False
            
        # Superusers automatically have internal system access
        if request.user.is_superuser:
            return True
            
        # Check for internal_systems group membership
        if request.user.groups.filter(name='internal_systems').exists():
            return True
            
        # Check for specific internal system permission
        return request.user.has_perm('lab_equipment_api.internal_system_access')
    
    def get_permission_denied_message(self):
        return "Internal system access required. This endpoint is restricted to system operations."


# Permission class mappings for easy reference
PERMISSION_CLASSES = {
    'admin': AdminPermission,
    'batch_user': BatchUserPermission,
    'read_only': ReadOnlyPermission,
    'external_api': ExternalAPIPermission,
    'internal_system': InternalSystemPermission,
}


def get_permission_class(permission_name):
    """
    Helper function to get permission class by name.
    
    Args:
        permission_name (str): Name of the permission class
        
    Returns:
        Permission class or None if not found
    """
    return PERMISSION_CLASSES.get(permission_name.lower())


def user_has_permission_level(user, permission_level):
    """
    Check if a user has a specific permission level.
    
    Args:
        user (User): Django user instance
        permission_level (str): Permission level to check
        
    Returns:
        bool: True if user has the permission level
    """
    if not user or not user.is_authenticated:
        return False
        
    permission_class = get_permission_class(permission_level)
    if not permission_class:
        return False
        
    # Create a mock request to test permission
    class MockRequest:
        def __init__(self, user):
            self.user = user
            self.method = 'GET'
    
    mock_request = MockRequest(user)
    permission_instance = permission_class()
    
    return permission_instance.has_permission(mock_request, None) 