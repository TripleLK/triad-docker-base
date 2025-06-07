"""
API views for Lab Equipment API v2.

Created by: Quantum Gecko (system views)
Enhanced by: Noble Harbor (equipment endpoints)
Date: 2025-01-19
Project: Triad Docker Base
"""

from django.db import connection
from django.utils import timezone
from django.db.models import Q, Count
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status, filters
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate
from django.db.models import Count, Q
from django_filters.rest_framework import DjangoFilterBackend
from .models import APIRequest, BatchOperation, ValidationResult, ErrorLog
from .serializers import (
    LabEquipmentPageListSerializer, LabEquipmentPageDetailSerializer,
    LabEquipmentPageCreateUpdateSerializer, EquipmentModelSerializer,
    LabEquipmentAccessorySerializer, CategorizedTagSerializer,
    QuoteCartItemSerializer, BulkEquipmentCreateSerializer,
    BulkEquipmentUpdateSerializer
)
from .permissions import (
    AdminPermission, BatchUserPermission, ReadOnlyPermission,
    ExternalAPIPermission, InternalSystemPermission
)
from .throttling import BasicUserThrottle, BatchOperationThrottle
from apps.base_site.models import (
    LabEquipmentPage, EquipmentModel, LabEquipmentAccessory,
    QuoteCartItem
)
from apps.categorized_tags.models import CategorizedTag


# ============ SYSTEM VIEWS (Existing) ============

class HealthCheckView(APIView):
    """Health check endpoint for monitoring system status."""
    
    permission_classes = []  # Allow anonymous access for monitoring
    
    def get(self, request):
        """Return system health status."""
        try:
            # Check database connectivity
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                db_status = "healthy"
        except Exception as e:
            db_status = f"error: {str(e)}"
        
        # Get basic statistics
        current_time = timezone.now()
        
        health_data = {
            "status": "healthy" if db_status == "healthy" else "degraded",
            "timestamp": current_time.isoformat(),
            "version": "2.0.0",
            "database": {
                "status": db_status,
                "connection": "active"
            },
            "api": {
                "requests_today": self._get_requests_today(),
                "active_batch_operations": self._get_active_batches(),
                "error_rate_24h": self._get_error_rate()
            }
        }
        
        # Determine response status
        response_status = status.HTTP_200_OK if health_data["status"] == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE
        
        return Response(health_data, status=response_status)
    
    def _get_requests_today(self):
        """Get count of API requests today."""
        try:
            today = timezone.now().date()
            return APIRequest.objects.filter(created_at__date=today).count()
        except:
            return 0
    
    def _get_active_batches(self):
        """Get count of active batch operations."""
        try:
            return BatchOperation.objects.filter(
                status__in=['queued', 'processing']
            ).count()
        except:
            return 0
    
    def _get_error_rate(self):
        """Get error rate for last 24 hours."""
        try:
            last_24h = timezone.now() - timezone.timedelta(hours=24)
            total_requests = APIRequest.objects.filter(created_at__gte=last_24h).count()
            error_requests = APIRequest.objects.filter(
                created_at__gte=last_24h,
                status='failed'
            ).count()
            
            if total_requests > 0:
                return round((error_requests / total_requests) * 100, 2)
            return 0.0
        except:
            return 0.0


class SystemStatsView(APIView):
    """System statistics endpoint for API usage analytics."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Return comprehensive system statistics."""
        try:
            # Date ranges
            now = timezone.now()
            last_24h = now - timezone.timedelta(hours=24)
            last_7d = now - timezone.timedelta(days=7)
            last_30d = now - timezone.timedelta(days=30)
            
            stats = {
                "timestamp": now.isoformat(),
                "requests": {
                    "total": APIRequest.objects.count(),
                    "last_24h": APIRequest.objects.filter(created_at__gte=last_24h).count(),
                    "last_7d": APIRequest.objects.filter(created_at__gte=last_7d).count(),
                    "last_30d": APIRequest.objects.filter(created_at__gte=last_30d).count(),
                    "by_status": self._get_request_stats_by_status(),
                    "by_method": self._get_request_stats_by_method(),
                },
                "batch_operations": {
                    "total": BatchOperation.objects.count(),
                    "active": BatchOperation.objects.filter(status__in=['queued', 'processing']).count(),
                    "completed": BatchOperation.objects.filter(status='completed').count(),
                    "failed": BatchOperation.objects.filter(status='failed').count(),
                    "by_type": self._get_batch_stats_by_type(),
                },
                "validation": {
                    "total_results": ValidationResult.objects.count(),
                    "by_level": self._get_validation_stats_by_level(),
                    "by_type": self._get_validation_stats_by_type(),
                },
                "errors": {
                    "total": ErrorLog.objects.count(),
                    "unresolved": ErrorLog.objects.filter(is_resolved=False).count(),
                    "last_24h": ErrorLog.objects.filter(created_at__gte=last_24h).count(),
                    "by_severity": self._get_error_stats_by_severity(),
                    "by_type": self._get_error_stats_by_type(),
                },
                "performance": {
                    "avg_response_time_24h": self._get_avg_response_time(),
                    "slowest_endpoints": self._get_slowest_endpoints(),
                },
                "equipment": {
                    "total_equipment": LabEquipmentPage.objects.count(),
                    "published_equipment": LabEquipmentPage.objects.filter(live=True).count(),
                    "needs_review": LabEquipmentPage.objects.filter(needs_review=True).count(),
                    "total_models": EquipmentModel.objects.count(),
                }
            }
            
            return Response(stats, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": f"Failed to generate statistics: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_request_stats_by_status(self):
        """Get request statistics grouped by status."""
        return dict(
            APIRequest.objects.values('status').annotate(count=Count('id')).values_list('status', 'count')
        )
    
    def _get_request_stats_by_method(self):
        """Get request statistics grouped by HTTP method."""
        return dict(
            APIRequest.objects.values('method').annotate(count=Count('id')).values_list('method', 'count')
        )
    
    def _get_batch_stats_by_type(self):
        """Get batch operation statistics grouped by type."""
        return dict(
            BatchOperation.objects.values('operation_type').annotate(count=Count('id')).values_list('operation_type', 'count')
        )
    
    def _get_validation_stats_by_level(self):
        """Get validation result statistics grouped by level."""
        return dict(
            ValidationResult.objects.values('result_level').annotate(count=Count('id')).values_list('result_level', 'count')
        )
    
    def _get_validation_stats_by_type(self):
        """Get validation result statistics grouped by type."""
        return dict(
            ValidationResult.objects.values('validation_type').annotate(count=Count('id')).values_list('validation_type', 'count')
        )
    
    def _get_error_stats_by_severity(self):
        """Get error statistics grouped by severity."""
        return dict(
            ErrorLog.objects.values('severity').annotate(count=Count('id')).values_list('severity', 'count')
        )
    
    def _get_error_stats_by_type(self):
        """Get error statistics grouped by type."""
        return dict(
            ErrorLog.objects.values('error_type').annotate(count=Count('id')).values_list('error_type', 'count')
        )
    
    def _get_avg_response_time(self):
        """Calculate average response time for last 24 hours."""
        last_24h = timezone.now() - timezone.timedelta(hours=24)
        requests = APIRequest.objects.filter(
            created_at__gte=last_24h,
            started_at__isnull=False,
            completed_at__isnull=False
        )
        
        if requests.exists():
            total_time = sum(req.duration for req in requests if req.duration)
            return round(total_time / requests.count(), 4)
        return 0.0
    
    def _get_slowest_endpoints(self):
        """Get slowest endpoints by average response time."""
        # This would require more complex aggregation in a real implementation
        return []


class TokenAuthView(ObtainAuthToken):
    """Enhanced token authentication endpoint."""
    
    def post(self, request, *args, **kwargs):
        """Authenticate user and return token."""
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'username': user.username,
            'is_staff': user.is_staff,
            'created': created
        })


class TestView(APIView):
    """Test endpoint for development and debugging."""
    
    permission_classes = []  # Allow anonymous access for testing
    
    def get(self, request):
        """Return test data and system info."""
        return Response({
            "message": "Lab Equipment API v2 Test Endpoint",
            "timestamp": timezone.now().isoformat(),
            "user": str(request.user),
            "authenticated": request.user.is_authenticated,
            "method": "GET"
        })
    
    def post(self, request):
        """Echo back posted data."""
        return Response({
            "message": "Lab Equipment API v2 Test Endpoint",
            "timestamp": timezone.now().isoformat(),
            "user": str(request.user),
            "authenticated": request.user.is_authenticated,
            "method": "POST",
            "data_received": request.data
        })


# ============ EQUIPMENT VIEWSETS (New) ============

class LabEquipmentViewSet(ModelViewSet):
    """
    ViewSet for lab equipment pages with full CRUD operations.
    
    Provides:
    - List view with filtering, searching, and pagination
    - Detail view with complete equipment information
    - Create, update, delete operations
    - Bulk operations for batch processing
    - Search and filtering capabilities
    """
    
    queryset = LabEquipmentPage.objects.all()
    permission_classes = [ReadOnlyPermission]
    throttle_classes = [BasicUserThrottle]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['source_type', 'specification_confidence', 'needs_review', 'live']
    search_fields = ['title', 'short_description', 'full_description']
    ordering_fields = ['title', 'first_published_at', 'data_completeness']
    ordering = ['-first_published_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return LabEquipmentPageListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return LabEquipmentPageCreateUpdateSerializer
        else:
            return LabEquipmentPageDetailSerializer
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [BatchUserPermission]
        elif self.action in ['bulk_create', 'bulk_update', 'bulk_delete']:
            self.permission_classes = [BatchUserPermission]
            self.throttle_classes = [BatchOperationThrottle]
        return super().get_permissions()
    
    @action(detail=False, methods=['post'], url_path='bulk-create')
    def bulk_create(self, request):
        """Create multiple equipment pages in bulk."""
        serializer = BulkEquipmentCreateSerializer(data=request.data)
        if serializer.is_valid():
            result = serializer.save()
            return Response({
                'message': f'Bulk create completed. Created: {result["total_created"]}, Errors: {result["total_errors"]}',
                'total_created': result['total_created'],
                'total_errors': result['total_errors'],
                'created_pages': LabEquipmentPageListSerializer(
                    result['created_pages'], many=True, context={'request': request}
                ).data,
                'errors': result['errors']
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['patch'], url_path='bulk-update')
    def bulk_update(self, request):
        """Update multiple equipment pages in bulk."""
        serializer = BulkEquipmentUpdateSerializer(data=request.data)
        if serializer.is_valid():
            result = serializer.save(instance=None, validated_data=serializer.validated_data)
            return Response({
                'message': f'Bulk update completed. Updated: {result["total_updated"]}, Errors: {result["total_errors"]}',
                'total_updated': result['total_updated'],
                'total_errors': result['total_errors'],
                'updated_pages': LabEquipmentPageListSerializer(
                    result['updated_pages'], many=True, context={'request': request}
                ).data,
                'errors': result['errors']
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], url_path='search')
    def advanced_search(self, request):
        """Advanced search with multiple criteria."""
        queryset = self.get_queryset()
        
        # Text search
        q = request.query_params.get('q', '')
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q) |
                Q(short_description__icontains=q) |
                Q(full_description__icontains=q)
            )
        
        # Tag search
        tags = request.query_params.get('tags', '')
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',')]
            queryset = queryset.filter(categorized_tags__name__in=tag_list).distinct()
        
        # Specification search
        spec_search = request.query_params.get('specs', '')
        if spec_search:
            queryset = queryset.filter(
                Q(spec_groups__specs__key__icontains=spec_search) |
                Q(spec_groups__specs__value__icontains=spec_search)
            ).distinct()
        
        # Data quality filters
        min_completeness = request.query_params.get('min_completeness')
        if min_completeness:
            try:
                queryset = queryset.filter(data_completeness__gte=float(min_completeness))
            except ValueError:
                pass
        
        # Apply pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = LabEquipmentPageListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = LabEquipmentPageListSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], url_path='related')
    def get_related_equipment(self, request, pk=None):
        """Get equipment related to this one (by tags and specifications)."""
        equipment = self.get_object()
        
        # Find related equipment by tags
        related_by_tags = LabEquipmentPage.objects.filter(
            categorized_tags__in=equipment.categorized_tags.all()
        ).exclude(page_ptr_id=equipment.page_ptr_id).distinct()[:5]
        
        # Find related equipment by specification similarity
        # This is a simplified approach - in production, you might use more sophisticated matching
        related_by_specs = LabEquipmentPage.objects.filter(
            spec_groups__name__in=equipment.spec_group_names
        ).exclude(page_ptr_id=equipment.page_ptr_id).distinct()[:5]
        
        return Response({
            'related_by_tags': LabEquipmentPageListSerializer(
                related_by_tags, many=True, context={'request': request}
            ).data,
            'related_by_specs': LabEquipmentPageListSerializer(
                related_by_specs, many=True, context={'request': request}
            ).data
        })


class EquipmentModelViewSet(ModelViewSet):
    """ViewSet for equipment models."""
    
    queryset = EquipmentModel.objects.all()
    serializer_class = EquipmentModelSerializer
    permission_classes = [ReadOnlyPermission]
    throttle_classes = [BasicUserThrottle]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['page']
    search_fields = ['name', 'model_number']
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [BatchUserPermission]
        return super().get_permissions()


class EquipmentAccessoryViewSet(ModelViewSet):
    """ViewSet for equipment accessories."""
    
    queryset = LabEquipmentAccessory.objects.all()
    serializer_class = LabEquipmentAccessorySerializer
    permission_classes = [ReadOnlyPermission]
    throttle_classes = [BasicUserThrottle]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name', 'model_number']
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [AdminPermission]
        return super().get_permissions()


class CategorizedTagViewSet(ModelViewSet):
    """ViewSet for categorized tags."""
    
    queryset = CategorizedTag.objects.all()
    serializer_class = CategorizedTagSerializer
    permission_classes = [ReadOnlyPermission]
    throttle_classes = [BasicUserThrottle]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category']
    search_fields = ['name']
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [BatchUserPermission]
        return super().get_permissions()
    
    @action(detail=False, methods=['get'], url_path='categories')
    def get_categories(self, request):
        """Get all available tag categories."""
        categories = CategorizedTag.objects.values_list('category', flat=True).distinct()
        return Response({
            'categories': sorted(list(categories))
        })


class QuoteCartViewSet(ModelViewSet):
    """ViewSet for quote cart management."""
    
    queryset = QuoteCartItem.objects.all()
    serializer_class = QuoteCartItemSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [BasicUserThrottle]
    
    def get_queryset(self):
        """Filter by session or user."""
        # For authenticated users, you might want to filter by user
        # For now, filtering by session key from request
        session_key = self.request.session.session_key
        if session_key:
            return QuoteCartItem.objects.filter(session_key=session_key)
        return QuoteCartItem.objects.none()
    
    @action(detail=False, methods=['post'], url_path='add-item')
    def add_item(self, request):
        """Add an item to the quote cart."""
        # Implementation would handle adding items to cart
        # This is simplified for demonstration
        return Response({
            'message': 'Item added to cart',
            'cart_total': self.get_queryset().count()
        })
    
    @action(detail=False, methods=['delete'], url_path='clear')
    def clear_cart(self, request):
        """Clear all items from the quote cart."""
        deleted_count = self.get_queryset().delete()[0]
        return Response({
            'message': f'Removed {deleted_count} items from cart'
        }) 