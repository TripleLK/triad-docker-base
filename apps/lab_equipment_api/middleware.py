"""
Lab Equipment API v2 Audit Logging Middleware - Comprehensive audit logging for all API operations.

Created by: Noble Harbor
Date: 2025-01-19
Project: Triad Docker Base
"""

import json
import time
import logging
from datetime import datetime, timedelta
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.conf import settings
from .models import APIRequest, ErrorLog
import uuid

# Set up dedicated logger for audit events
audit_logger = logging.getLogger('lab_equipment_api.audit')


class AuditLoggingMiddleware(MiddlewareMixin):
    """
    Comprehensive audit logging middleware for Lab Equipment API v2.
    
    Logs all API requests with full context including:
    - Request details (method, path, headers, body)
    - User information and authentication status
    - Response details (status, headers, body)
    - Timing information (duration, timestamps)
    - Data modification tracking
    - Security events (auth failures, permission denials)
    """
    
    def __init__(self, get_response):
        """Initialize middleware with configuration."""
        self.get_response = get_response
        self.log_request_body = getattr(settings, 'AUDIT_LOG_REQUEST_BODY', True)
        self.log_response_body = getattr(settings, 'AUDIT_LOG_RESPONSE_BODY', True)
        self.max_body_size = getattr(settings, 'AUDIT_MAX_BODY_SIZE', 10000)  # 10KB default
        self.sensitive_headers = getattr(settings, 'AUDIT_SENSITIVE_HEADERS', [
            'authorization', 'cookie', 'x-api-key', 'x-auth-token'
        ])
        super().__init__(get_response)
    
    def __call__(self, request):
        """Main middleware processing."""
        # Skip non-API requests unless specifically configured
        if not self.should_log_request(request):
            return self.get_response(request)
        
        # Generate unique request ID for tracking
        request.audit_id = str(uuid.uuid4())
        
        # Record request start time
        start_time = time.time()
        request.audit_start_time = start_time
        
        # Log request details
        request_data = self.extract_request_data(request)
        
        try:
            # Process the request
            response = self.get_response(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Extract response data
            response_data = self.extract_response_data(response, duration)
            
            # Log the complete request/response cycle
            self.log_api_request(request, request_data, response_data)
            
            # Check for security events
            self.check_security_events(request, response, request_data, response_data)
            
            return response
            
        except Exception as e:
            # Log errors and exceptions
            duration = time.time() - start_time
            error_data = {
                'error_type': type(e).__name__,
                'error_message': str(e),
                'duration': duration
            }
            
            self.log_api_error(request, request_data, error_data)
            self.log_security_event(request, 'API_ERROR', {
                'error': str(e),
                'request_path': request.path
            })
            
            raise  # Re-raise the exception
    
    def should_log_request(self, request):
        """
        Determine if request should be logged.
        
        Args:
            request: Django request object
            
        Returns:
            bool: True if request should be logged
        """
        # Always log API requests (starting with /api/)
        if request.path.startswith('/api/'):
            return True
        
        # Log admin requests if configured
        if hasattr(settings, 'AUDIT_LOG_ADMIN') and settings.AUDIT_LOG_ADMIN:
            if request.path.startswith('/admin/'):
                return True
        
        # Log specific paths if configured
        if hasattr(settings, 'AUDIT_LOG_PATHS'):
            for path_pattern in settings.AUDIT_LOG_PATHS:
                if request.path.startswith(path_pattern):
                    return True
        
        return False
    
    def extract_request_data(self, request):
        """
        Extract comprehensive request data for logging.
        
        Args:
            request: Django request object
            
        Returns:
            dict: Request data for logging
        """
        # Basic request information
        data = {
            'audit_id': request.audit_id,
            'timestamp': timezone.now().isoformat(),
            'method': request.method,
            'path': request.path,
            'query_string': request.META.get('QUERY_STRING', ''),
            'content_type': request.content_type,
            'remote_addr': self.get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        }
        
        # User information
        if hasattr(request, 'user') and request.user.is_authenticated:
            data['user'] = {
                'id': request.user.pk,
                'username': request.user.username,
                'email': request.user.email,
                'is_staff': request.user.is_staff,
                'is_superuser': request.user.is_superuser,
                'groups': list(request.user.groups.values_list('name', flat=True)),
            }
        else:
            data['user'] = {'type': 'anonymous'}
        
        # Headers (filtered for sensitive information)
        data['headers'] = self.filter_sensitive_headers(dict(request.headers))
        
        # Request body (if configured and within size limits)
        if self.log_request_body and hasattr(request, 'body'):
            body = request.body
            if len(body) <= self.max_body_size:
                try:
                    # Try to decode as JSON first
                    if request.content_type == 'application/json':
                        data['body'] = json.loads(body.decode('utf-8'))
                    else:
                        data['body'] = body.decode('utf-8')
                except (UnicodeDecodeError, json.JSONDecodeError):
                    data['body'] = f"<binary data: {len(body)} bytes>"
            else:
                data['body'] = f"<data too large: {len(body)} bytes>"
        
        return data
    
    def extract_response_data(self, response, duration):
        """
        Extract response data for logging.
        
        Args:
            response: Django response object
            duration: Request processing duration in seconds
            
        Returns:
            dict: Response data for logging
        """
        data = {
            'status_code': response.status_code,
            'duration': round(duration, 4),
            'content_type': response.get('Content-Type', ''),
        }
        
        # Response headers (filtered)
        if hasattr(response, 'headers'):
            data['headers'] = dict(response.headers)
        
        # Response body (if configured and within size limits)
        if self.log_response_body and hasattr(response, 'content'):
            content = response.content
            if len(content) <= self.max_body_size:
                try:
                    # Try to decode as JSON first
                    if 'application/json' in response.get('Content-Type', ''):
                        data['body'] = json.loads(content.decode('utf-8'))
                    else:
                        data['body'] = content.decode('utf-8')
                except (UnicodeDecodeError, json.JSONDecodeError):
                    data['body'] = f"<binary data: {len(content)} bytes>"
            else:
                data['body'] = f"<response too large: {len(content)} bytes>"
        
        return data
    
    def log_api_request(self, request, request_data, response_data):
        """
        Log complete API request/response cycle.
        
        Args:
            request: Django request object
            request_data: Extracted request data
            response_data: Extracted response data
        """
        # Create comprehensive log entry
        log_entry = {
            'audit_id': request.audit_id,
            'event_type': 'API_REQUEST',
            'timestamp': timezone.now().isoformat(),
            'request': request_data,
            'response': response_data,
        }
        
        # Log to file/console
        audit_logger.info(f"API Request: {request.method} {request.path}", extra={
            'audit_data': log_entry
        })
        
        # Store in database (async to avoid blocking)
        try:
            with transaction.atomic():
                api_request = APIRequest(
                    user=request.user if request.user.is_authenticated else None,
                    method=request.method,
                    endpoint=request.path,
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    status_code=response_data['status_code'],
                    response_time=response_data['duration'],
                    request_size=len(str(request_data)),
                    response_size=len(str(response_data)),
                    metadata=log_entry
                )
                api_request.save()
        except Exception as e:
            # Log database errors but don't fail the request
            audit_logger.error(f"Failed to save API request to database: {e}")
    
    def log_api_error(self, request, request_data, error_data):
        """
        Log API errors and exceptions.
        
        Args:
            request: Django request object
            request_data: Extracted request data
            error_data: Error information
        """
        log_entry = {
            'audit_id': request.audit_id,
            'event_type': 'API_ERROR',
            'timestamp': timezone.now().isoformat(),
            'request': request_data,
            'error': error_data,
        }
        
        audit_logger.error(f"API Error: {request.method} {request.path}", extra={
            'audit_data': log_entry
        })
        
        # Store error in database
        try:
            with transaction.atomic():
                error_log = ErrorLog(
                    user=request.user if request.user.is_authenticated else None,
                    error_type=error_data['error_type'],
                    error_message=error_data['error_message'],
                    endpoint=request.path,
                    request_data=request_data,
                    traceback=error_data.get('traceback', ''),
                    metadata={'audit_id': request.audit_id}
                )
                error_log.save()
        except Exception as e:
            audit_logger.error(f"Failed to save error log to database: {e}")
    
    def check_security_events(self, request, response, request_data, response_data):
        """
        Check for and log security events.
        
        Args:
            request: Django request object
            response: Django response object
            request_data: Extracted request data
            response_data: Extracted response data
        """
        # Authentication failures
        if response.status_code == 401:
            self.log_security_event(request, 'AUTH_FAILURE', {
                'endpoint': request.path,
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'ip_address': self.get_client_ip(request)
            })
        
        # Permission denied
        if response.status_code == 403:
            self.log_security_event(request, 'PERMISSION_DENIED', {
                'endpoint': request.path,
                'user': request.user.username if request.user.is_authenticated else 'anonymous',
                'user_groups': list(request.user.groups.values_list('name', flat=True)) if request.user.is_authenticated else []
            })
        
        # Rate limit exceeded
        if response.status_code == 429:
            self.log_security_event(request, 'RATE_LIMIT_EXCEEDED', {
                'endpoint': request.path,
                'user': request.user.username if request.user.is_authenticated else 'anonymous',
                'ip_address': self.get_client_ip(request)
            })
        
        # Suspicious patterns (multiple failed requests from same IP)
        self.check_suspicious_patterns(request, response)
    
    def log_security_event(self, request, event_type, details):
        """
        Log security events with enhanced details.
        
        Args:
            request: Django request object
            event_type: Type of security event
            details: Additional event details
        """
        log_entry = {
            'audit_id': getattr(request, 'audit_id', str(uuid.uuid4())),
            'event_type': f'SECURITY_{event_type}',
            'timestamp': timezone.now().isoformat(),
            'ip_address': self.get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'details': details
        }
        
        if hasattr(request, 'user') and request.user.is_authenticated:
            log_entry['user'] = {
                'id': request.user.pk,
                'username': request.user.username,
            }
        
        audit_logger.warning(f"Security Event: {event_type}", extra={
            'audit_data': log_entry
        })
    
    def check_suspicious_patterns(self, request, response):
        """
        Check for suspicious request patterns that might indicate attacks.
        
        Args:
            request: Django request object
            response: Django response object
        """
        client_ip = self.get_client_ip(request)
        
        # Check for excessive failed authentication attempts
        if response.status_code in [401, 403]:
            cache_key = f"failed_auth_{client_ip}"
            from django.core.cache import cache
            
            failed_attempts = cache.get(cache_key, 0) + 1
            cache.set(cache_key, failed_attempts, 3600)  # 1 hour
            
            if failed_attempts >= 10:  # Configurable threshold
                self.log_security_event(request, 'SUSPICIOUS_ACTIVITY', {
                    'pattern': 'excessive_auth_failures',
                    'failed_attempts': failed_attempts,
                    'time_window': '1 hour'
                })
    
    def get_client_ip(self, request):
        """
        Get the real client IP address, handling proxies and load balancers.
        
        Args:
            request: Django request object
            
        Returns:
            str: Client IP address
        """
        # Check for forwarded IP addresses
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # Take the first IP in the chain
            return x_forwarded_for.split(',')[0].strip()
        
        x_real_ip = request.META.get('HTTP_X_REAL_IP')
        if x_real_ip:
            return x_real_ip
        
        return request.META.get('REMOTE_ADDR', '')
    
    def filter_sensitive_headers(self, headers):
        """
        Filter out sensitive headers from logging.
        
        Args:
            headers: Dictionary of HTTP headers
            
        Returns:
            dict: Filtered headers with sensitive values masked
        """
        filtered = {}
        for key, value in headers.items():
            if key.lower() in self.sensitive_headers:
                filtered[key] = '<REDACTED>'
            else:
                filtered[key] = value
        return filtered


class DataModificationTracker:
    """
    Utility class for tracking data modifications in API operations.
    
    Can be used in views and serializers to track what data was changed,
    providing detailed audit trails for equipment modifications.
    """
    
    def __init__(self, user, operation_type, model_name):
        """
        Initialize modification tracker.
        
        Args:
            user: Django user performing the operation
            operation_type: Type of operation (CREATE, UPDATE, DELETE)
            model_name: Name of the model being modified
        """
        self.user = user
        self.operation_type = operation_type
        self.model_name = model_name
        self.changes = []
        self.audit_id = str(uuid.uuid4())
    
    def track_field_change(self, field_name, old_value, new_value):
        """
        Track a field change.
        
        Args:
            field_name: Name of the field that changed
            old_value: Previous value
            new_value: New value
        """
        self.changes.append({
            'field': field_name,
            'old_value': old_value,
            'new_value': new_value,
            'timestamp': timezone.now().isoformat()
        })
    
    def log_modification(self, instance_id=None, additional_context=None):
        """
        Log the complete modification event.
        
        Args:
            instance_id: ID of the model instance (if applicable)
            additional_context: Additional context information
        """
        log_entry = {
            'audit_id': self.audit_id,
            'event_type': 'DATA_MODIFICATION',
            'timestamp': timezone.now().isoformat(),
            'user': {
                'id': self.user.pk,
                'username': self.user.username,
            } if self.user.is_authenticated else {'type': 'system'},
            'operation': self.operation_type,
            'model': self.model_name,
            'instance_id': instance_id,
            'changes': self.changes,
            'context': additional_context or {}
        }
        
        audit_logger.info(f"Data Modification: {self.operation_type} {self.model_name}", extra={
            'audit_data': log_entry
        })
    
    @classmethod
    def track_model_save(cls, sender, instance, created, **kwargs):
        """
        Django signal handler for tracking model saves.
        Can be connected to post_save signals for automatic tracking.
        """
        # This would be connected in apps.py or models.py
        operation_type = 'CREATE' if created else 'UPDATE'
        # Implementation would depend on accessing the current user context
        pass 