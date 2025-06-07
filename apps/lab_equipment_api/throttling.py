"""
Lab Equipment API v2 Throttling - Simplified rate limiting with admin vs non-admin tiers.

Created by: Noble Harbor
Date: 2025-01-19
Project: Triad Docker Base
"""

from rest_framework.throttling import UserRateThrottle, AnonRateThrottle, BaseThrottle
from django.core.cache import cache
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class BasicUserThrottle(UserRateThrottle):
    """
    Simplified throttle with two tiers: admin vs non-admin users.
    
    Rate limits:
    - Anonymous users: 100 requests/hour
    - Authenticated non-admin users: 1000 requests/hour  
    - Admin users (staff/superuser): 10000 requests/hour
    """
    
    scope = 'user_basic'
    
    def get_rate(self):
        """
        Get rate limit based on user admin status.
        Returns rate in 'num/period' format (e.g., '1000/hour').
        """
        if not hasattr(self, 'request') or not self.request.user.is_authenticated:
            return '100/hour'  # Anonymous users
        
        user = self.request.user
        
        # Admin users (staff or superuser) get high quota
        if user.is_staff or user.is_superuser:
            return '10000/hour'
        
        # All other authenticated users get standard quota
        return '1000/hour'
    
    def allow_request(self, request, view):
        """
        Enhanced allow_request with user-specific quota logic.
        """
        self.request = request  # Store request for get_rate() method
        
        # Call parent method for standard throttling logic
        allowed = super().allow_request(request, view)
        
        # Log throttle events
        if not allowed:
            self.log_throttle_hit(request, view, quota_exceeded=True)
        
        return allowed
    
    def log_throttle_hit(self, request, view, quota_exceeded=False):
        """Enhanced logging with user details."""
        user_info = (f"User: {request.user.username} (ID: {request.user.pk})" 
                    if request.user.is_authenticated else "Anonymous")
        rate = self.get_rate()
        
        logger.warning(f"Rate limit {'exceeded' if quota_exceeded else 'checked'}: "
                      f"{user_info} - Rate: {rate} - Endpoint: {request.path} - "
                      f"Method: {request.method}")


class BatchOperationThrottle(BaseThrottle):
    """
    Special throttling for batch operations to prevent system overload.
    
    Conservative limits for batch operations:
    - Non-admin users: 10 batch operations per hour
    - Admin users: 50 batch operations per hour
    """
    
    scope = 'batch_operation'
    
    def allow_request(self, request, view):
        """
        Custom allow_request logic for batch operations.
        """
        if not request.user.is_authenticated:
            return False  # Batch operations require authentication
        
        # Determine rate based on admin status
        if request.user.is_staff or request.user.is_superuser:
            max_requests = 50
        else:
            max_requests = 10
        
        # Create cache key
        cache_key = f"batch_throttle_{request.user.pk}"
        
        # Use cache to track requests
        now = timezone.now()
        window_start = now - timedelta(hours=1)
        
        # Get current request count
        request_times = cache.get(cache_key, [])
        request_times = [time for time in request_times if time > window_start]
        
        # Check if limit exceeded
        if len(request_times) >= max_requests:
            self.log_throttle_hit(request, view, quota_exceeded=True, rate=f"{max_requests}/hour")
            return False
        
        # Add current request time
        request_times.append(now)
        cache.set(cache_key, request_times, 3600)  # 1 hour cache
        
        return True
    
    def log_throttle_hit(self, request, view, quota_exceeded=False, rate=None):
        """Log batch throttle events."""
        user_info = f"User: {request.user.username} (ID: {request.user.pk})"
        rate_info = f"Rate: {rate}" if rate else ""
        
        logger.warning(f"Batch throttle {'exceeded' if quota_exceeded else 'checked'}: "
                      f"{user_info} - {rate_info} - "
                      f"Endpoint: {request.path}")


# Throttle class mappings for easy reference
THROTTLE_CLASSES = {
    'user_basic': BasicUserThrottle,
    'batch_operation': BatchOperationThrottle,
}


def get_throttle_class(throttle_name):
    """
    Helper function to get throttle class by name.
    
    Args:
        throttle_name (str): Name of the throttle class
        
    Returns:
        Throttle class or None if not found
    """
    return THROTTLE_CLASSES.get(throttle_name.lower())


def get_user_rate_limits(user):
    """
    Get all applicable rate limits for a user.
    
    Args:
        user (User): Django user instance
        
    Returns:
        dict: Dictionary of throttle types and their rates
    """
    limits = {}
    
    # Basic user throttle
    user_throttle = BasicUserThrottle()
    user_throttle.request = type('Request', (), {'user': user})()
    limits['user_basic'] = user_throttle.get_rate()
    
    # Batch operation limits
    if user.is_staff or user.is_superuser:
        limits['batch_operations'] = '50/hour'
    else:
        limits['batch_operations'] = '10/hour'
    
    return limits 