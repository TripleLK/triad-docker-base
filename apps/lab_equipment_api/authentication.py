"""
Lab Equipment API v2 Authentication - Enhanced token authentication with advanced features.

Created by: Noble Harbor
Date: 2025-01-19
Project: Triad Docker Base
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db import models, transaction
from django.core.cache import cache
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed
from rest_framework import status
import logging
import uuid

logger = logging.getLogger(__name__)


class APIToken(models.Model):
    """
    Enhanced token model with expiration, refresh, and scoping capabilities.
    
    Extends the basic DRF token functionality with:
    - Token expiration and automatic refresh
    - Multi-device token management
    - Permission scoping and metadata
    - Usage tracking and analytics
    """
    
    # Token identification
    key = models.CharField(max_length=40, unique=True, primary_key=True)
    refresh_key = models.CharField(max_length=40, unique=True, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_tokens')
    
    # Token lifecycle
    created = models.DateTimeField(auto_now_add=True)
    expires = models.DateTimeField()
    last_used = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Device and session management
    device_id = models.CharField(max_length=255, null=True, blank=True,
                                help_text="Unique identifier for the device/client")
    device_name = models.CharField(max_length=255, null=True, blank=True,
                                  help_text="Human-readable device name")
    user_agent = models.TextField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    # Permission scoping
    scopes = models.JSONField(default=list, 
                             help_text="List of permission scopes this token grants")
    permission_level = models.CharField(max_length=50, default='read_only',
                                       choices=[
                                           ('admin', 'Administrator'),
                                           ('batch_user', 'Batch User'),
                                           ('read_only', 'Read Only'),
                                           ('external_api', 'External API'),
                                           ('internal_system', 'Internal System'),
                                       ])
    
    # Usage tracking
    usage_count = models.PositiveIntegerField(default=0)
    metadata = models.JSONField(default=dict,
                               help_text="Additional token metadata and tracking info")
    
    class Meta:
        app_label = 'lab_equipment_api'
        db_table = 'lab_equipment_api_tokens'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['expires', 'is_active']),
            models.Index(fields=['device_id']),
        ]
    
    def save(self, *args, **kwargs):
        """Override save to generate token keys and set expiration."""
        if not self.key:
            self.key = self.generate_key()
        if not self.refresh_key:
            self.refresh_key = self.generate_key()
        if not self.expires:
            self.expires = timezone.now() + timedelta(hours=24)  # Default 24 hour expiration
        super().save(*args, **kwargs)
    
    @classmethod
    def generate_key(cls):
        """Generate a secure random token key."""
        return secrets.token_hex(20)  # 40 character hex string
    
    def is_expired(self):
        """Check if token is expired."""
        return timezone.now() > self.expires
    
    def is_valid(self):
        """Check if token is valid and usable."""
        return self.is_active and not self.is_expired()
    
    def refresh_token(self, extend_hours=24):
        """
        Refresh the token with a new expiration time.
        
        Args:
            extend_hours (int): Hours to extend the token expiration
            
        Returns:
            bool: True if refresh was successful
        """
        if not self.is_active:
            return False
        
        # Generate new keys
        old_key = self.key
        self.key = self.generate_key()
        self.refresh_key = self.generate_key()
        
        # Extend expiration
        self.expires = timezone.now() + timedelta(hours=extend_hours)
        self.last_used = timezone.now()
        
        # Update metadata
        self.metadata['refresh_history'] = self.metadata.get('refresh_history', [])
        self.metadata['refresh_history'].append({
            'timestamp': timezone.now().isoformat(),
            'old_key': old_key[:8] + '...',  # Store partial key for tracking
            'extended_hours': extend_hours
        })
        
        self.save()
        logger.info(f"Token refreshed for user {self.user.username} (device: {self.device_name})")
        return True
    
    def revoke(self, reason='manual'):
        """
        Revoke the token, making it unusable.
        
        Args:
            reason (str): Reason for revocation
        """
        self.is_active = False
        self.metadata['revocation'] = {
            'timestamp': timezone.now().isoformat(),
            'reason': reason
        }
        self.save()
        logger.warning(f"Token revoked for user {self.user.username}: {reason}")
    
    def update_usage(self, request=None):
        """
        Update usage statistics for the token.
        
        Args:
            request: Django request object (optional)
        """
        self.usage_count += 1
        self.last_used = timezone.now()
        
        if request:
            # Update IP and user agent if they've changed
            current_ip = self.get_client_ip(request)
            current_ua = request.META.get('HTTP_USER_AGENT', '')
            
            if current_ip != self.ip_address:
                self.metadata['ip_history'] = self.metadata.get('ip_history', [])
                self.metadata['ip_history'].append({
                    'timestamp': timezone.now().isoformat(),
                    'ip': current_ip
                })
                self.ip_address = current_ip
            
            if current_ua != self.user_agent:
                self.user_agent = current_ua
        
        self.save()
    
    def get_client_ip(self, request):
        """Extract client IP from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')
    
    def get_scope_permissions(self):
        """
        Get list of permissions based on token scopes.
        
        Returns:
            list: List of permission strings
        """
        scope_permissions = {
            'read': ['lab_equipment_api.view_equipment'],
            'write': ['lab_equipment_api.add_equipment', 'lab_equipment_api.change_equipment'],
            'delete': ['lab_equipment_api.delete_equipment'],
            'batch': ['lab_equipment_api.can_batch_operations'],
            'admin': ['lab_equipment_api.admin_access'],
            'external': ['lab_equipment_api.external_api_access'],
            'internal': ['lab_equipment_api.internal_system_access'],
        }
        
        permissions = []
        for scope in self.scopes:
            if scope in scope_permissions:
                permissions.extend(scope_permissions[scope])
        
        return permissions
    
    def __str__(self):
        """String representation of the token."""
        status = "active" if self.is_valid() else "inactive"
        return f"APIToken({self.user.username}, {self.device_name}, {status})"


class EnhancedTokenAuthentication(TokenAuthentication):
    """
    Enhanced token authentication with expiration, scoping, and advanced features.
    
    Extends DRF TokenAuthentication to use APIToken model with:
    - Automatic token expiration checking
    - Usage tracking and analytics
    - Permission scoping validation
    - Multi-device token management
    """
    
    model = APIToken
    keyword = 'Bearer'  # Use Bearer instead of Token
    
    def authenticate_credentials(self, key):
        """
        Authenticate the token and return user and token.
        
        Args:
            key (str): Token key to authenticate
            
        Returns:
            tuple: (user, token) if valid, None otherwise
            
        Raises:
            AuthenticationFailed: If token is invalid or expired
        """
        model = self.get_model()
        try:
            token = model.objects.select_related('user').get(key=key)
        except model.DoesNotExist:
            raise AuthenticationFailed('Invalid token.')
        
        # Check if token is active
        if not token.is_active:
            raise AuthenticationFailed('Token has been revoked.')
        
        # Check if token is expired
        if token.is_expired():
            # Attempt automatic refresh if refresh key is available
            if token.refresh_key and self.can_auto_refresh(token):
                if token.refresh_token():
                    logger.info(f"Token auto-refreshed for user {token.user.username}")
                else:
                    raise AuthenticationFailed('Token expired and refresh failed.')
            else:
                raise AuthenticationFailed('Token expired.')
        
        # Check if user is active
        if not token.user.is_active:
            raise AuthenticationFailed('User inactive or deleted.')
        
        return (token.user, token)
    
    def can_auto_refresh(self, token):
        """
        Check if token can be automatically refreshed.
        
        Args:
            token (APIToken): Token to check
            
        Returns:
            bool: True if token can be auto-refreshed
        """
        # Don't auto-refresh if token has been expired for more than 7 days
        expiry_grace_period = timedelta(days=7)
        if timezone.now() > token.expires + expiry_grace_period:
            return False
        
        # Check if auto-refresh is enabled for this token type
        auto_refresh_enabled = token.metadata.get('auto_refresh', True)
        return auto_refresh_enabled
    
    def authenticate(self, request):
        """
        Authenticate the request and update token usage.
        
        Args:
            request: Django request object
            
        Returns:
            tuple: (user, token) if authenticated, None otherwise
        """
        auth = super().authenticate(request)
        
        if auth is not None:
            user, token = auth
            # Update token usage statistics
            token.update_usage(request)
            
            # Add token to request for later use
            request.auth_token = token
        
        return auth


class TokenManager:
    """
    Utility class for managing API tokens.
    
    Provides methods for:
    - Creating tokens with specific scopes and permissions
    - Managing multi-device tokens for users
    - Bulk token operations (revoke, refresh, cleanup)
    - Token analytics and reporting
    """
    
    @classmethod
    def create_token(cls, user, device_name=None, device_id=None, 
                     permission_level='read_only', scopes=None, 
                     expires_hours=24, metadata=None, request=None):
        """
        Create a new API token for a user.
        
        Args:
            user (User): Django user
            device_name (str): Human-readable device name
            device_id (str): Unique device identifier
            permission_level (str): Permission level for the token
            scopes (list): List of permission scopes
            expires_hours (int): Hours until token expires
            metadata (dict): Additional metadata
            request: Django request object (optional)
            
        Returns:
            APIToken: Created token
        """
        if scopes is None:
            scopes = cls.get_default_scopes(permission_level)
        
        if metadata is None:
            metadata = {}
        
        # Add creation metadata
        metadata.update({
            'created_by': 'token_manager',
            'creation_timestamp': timezone.now().isoformat(),
            'permission_level': permission_level,
        })
        
        # Extract request information if available
        user_agent = None
        ip_address = None
        if request:
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            ip_address = cls.get_client_ip(request)
        
        with transaction.atomic():
            token = APIToken.objects.create(
                user=user,
                device_name=device_name or 'Unknown Device',
                device_id=device_id or str(uuid.uuid4()),
                permission_level=permission_level,
                scopes=scopes,
                expires=timezone.now() + timedelta(hours=expires_hours),
                metadata=metadata,
                user_agent=user_agent,
                ip_address=ip_address,
            )
        
        logger.info(f"Created API token for user {user.username} "
                   f"(device: {device_name}, level: {permission_level})")
        
        return token
    
    @classmethod
    def get_default_scopes(cls, permission_level):
        """
        Get default scopes for a permission level.
        
        Args:
            permission_level (str): Permission level
            
        Returns:
            list: Default scopes for the permission level
        """
        scope_mappings = {
            'admin': ['read', 'write', 'delete', 'batch', 'admin'],
            'batch_user': ['read', 'write', 'batch'],
            'read_only': ['read'],
            'external_api': ['read', 'external'],
            'internal_system': ['read', 'write', 'internal'],
        }
        
        return scope_mappings.get(permission_level, ['read'])
    
    @classmethod
    def get_user_tokens(cls, user, active_only=True):
        """
        Get all tokens for a user.
        
        Args:
            user (User): Django user
            active_only (bool): Only return active tokens
            
        Returns:
            QuerySet: User's tokens
        """
        queryset = APIToken.objects.filter(user=user)
        if active_only:
            queryset = queryset.filter(is_active=True, expires__gt=timezone.now())
        return queryset.order_by('-created')
    
    @classmethod
    def revoke_user_tokens(cls, user, device_id=None, reason='manual_revocation'):
        """
        Revoke tokens for a user.
        
        Args:
            user (User): Django user
            device_id (str): Specific device ID to revoke (optional)
            reason (str): Revocation reason
            
        Returns:
            int: Number of tokens revoked
        """
        queryset = APIToken.objects.filter(user=user, is_active=True)
        if device_id:
            queryset = queryset.filter(device_id=device_id)
        
        count = 0
        for token in queryset:
            token.revoke(reason)
            count += 1
        
        logger.info(f"Revoked {count} tokens for user {user.username} "
                   f"(device: {device_id or 'all'}, reason: {reason})")
        
        return count
    
    @classmethod
    def cleanup_expired_tokens(cls, days_old=30):
        """
        Clean up expired and old tokens.
        
        Args:
            days_old (int): Delete tokens older than this many days
            
        Returns:
            int: Number of tokens deleted
        """
        cutoff_date = timezone.now() - timedelta(days=days_old)
        
        # Delete very old expired tokens
        old_tokens = APIToken.objects.filter(
            expires__lt=cutoff_date,
            is_active=False
        )
        count = old_tokens.count()
        old_tokens.delete()
        
        # Deactivate recently expired tokens (don't delete yet)
        expired_tokens = APIToken.objects.filter(
            expires__lt=timezone.now(),
            is_active=True
        )
        
        for token in expired_tokens:
            token.revoke('automatic_expiry')
        
        logger.info(f"Cleanup: deleted {count} old tokens, "
                   f"deactivated {expired_tokens.count()} expired tokens")
        
        return count
    
    @classmethod
    def get_client_ip(cls, request):
        """Extract client IP from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')
    
    @classmethod
    def get_token_analytics(cls, user=None, days=30):
        """
        Get analytics for token usage.
        
        Args:
            user (User): Specific user (optional, None for all users)
            days (int): Number of days to analyze
            
        Returns:
            dict: Analytics data
        """
        from django.db.models import Count, Avg, Sum
        from django.utils import timezone
        
        start_date = timezone.now() - timedelta(days=days)
        
        queryset = APIToken.objects.filter(created__gte=start_date)
        if user:
            queryset = queryset.filter(user=user)
        
        analytics = {
            'total_tokens': queryset.count(),
            'active_tokens': queryset.filter(is_active=True, expires__gt=timezone.now()).count(),
            'expired_tokens': queryset.filter(expires__lt=timezone.now()).count(),
            'revoked_tokens': queryset.filter(is_active=False).count(),
            'total_usage': queryset.aggregate(Sum('usage_count'))['usage_count__sum'] or 0,
            'avg_usage_per_token': queryset.aggregate(Avg('usage_count'))['usage_count__avg'] or 0,
            'tokens_by_permission_level': list(
                queryset.values('permission_level').annotate(count=Count('permission_level'))
            ),
            'tokens_by_device': list(
                queryset.values('device_name').annotate(count=Count('device_name'))[:10]
            ),
        }
        
        return analytics


def create_api_token_view(request):
    """
    API view function for creating tokens.
    Can be used in views.py to provide token creation endpoint.
    """
    # Implementation would go in views.py
    pass 