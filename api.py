"""
Main Django Ninja API Router - Lab Equipment API v3

Created by: Steady Circuit
Date: 2025-01-08
Project: Triad Docker Base

This is the main API router for the Django Ninja implementation,
replacing the DRF-based v2 API to resolve Wagtail compatibility issues.
"""

from django.http import HttpRequest
from django.utils import timezone
from django.db.models import Q
from ninja import NinjaAPI
from ninja.security import HttpBearer
from typing import List, Optional

from apps.base_site.models import LabEquipmentPage, EquipmentModel, LabEquipmentAccessory
from apps.categorized_tags.models import CategorizedTag, CategorizedPageTag
from apps.lab_equipment_api.ninja_schemas import (
    LabEquipmentPageListSchema, LabEquipmentPageDetailSchema,
    EquipmentModelSchema, LabEquipmentAccessorySchema, CategorizedTagSchema,
    RelatedEquipmentResponseSchema, EquipmentSearchSchema, ErrorResponseSchema
)

api = NinjaAPI(
    title="Lab Equipment API v3",
    version="3.0.0",
    description="Django Ninja-based Lab Equipment API with Wagtail compatibility",
    docs_url="/docs/",
)


class AuthBearer(HttpBearer):
    """Token-based authentication for Django Ninja."""
    
    def authenticate(self, request: HttpRequest, token: str):
        """Authenticate using Django REST Framework tokens."""
        from rest_framework.authtoken.models import Token
        from django.contrib.auth.models import User
        
        try:
            auth_token = Token.objects.select_related('user').get(key=token)
            return auth_token.user
        except Token.DoesNotExist:
            return None


auth = AuthBearer()


# ============ SYSTEM ENDPOINTS ============

@api.get("/health", tags=["System"])
def health_check(request):
    """Health check endpoint for monitoring system status."""
    from django.db import connection
    
    try:
        # Check database connectivity
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            db_status = "healthy"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "timestamp": timezone.now().isoformat(),
        "version": "3.0.0",
        "framework": "Django Ninja",
        "database": {
            "status": db_status,
            "connection": "active"
        }
    }


@api.get("/test", tags=["System"])
def test_endpoint(request):
    """Test endpoint for development and debugging."""
    return {
        "message": "Django Ninja API v3 is working!",
        "timestamp": timezone.now().isoformat(),
        "framework": "Django Ninja",
        "wagtail_compatible": True
    }


# ============ EQUIPMENT ENDPOINTS ============

@api.get("/equipment", response=List[LabEquipmentPageListSchema], tags=["Equipment"])
def list_equipment(request, limit: int = 50, offset: int = 0):
    """List lab equipment with pagination."""
    # Validate parameters
    if offset < 0:
        return api.create_response(
            request,
            {"error": "Invalid offset", "message": "Offset cannot be negative"},
            status=422
        )
    
    if limit < 1:
        return api.create_response(
            request,
            {"error": "Invalid limit", "message": "Limit must be positive"},
            status=422
        )
    
    queryset = LabEquipmentPage.objects.all().order_by('-first_published_at')
    total_count = queryset.count()
    
    # Apply pagination
    equipment_list = list(queryset[offset:offset + limit])
    
    return equipment_list


@api.get("/equipment/{equipment_id}", response=LabEquipmentPageDetailSchema, tags=["Equipment"])
def get_equipment_detail(request, equipment_id: int):
    """Get detailed information about a specific piece of equipment."""
    try:
        # Use id for Wagtail Page model compatibility (page_ptr.id)
        equipment = LabEquipmentPage.objects.get(id=equipment_id)
        return equipment
    except LabEquipmentPage.DoesNotExist:
        return api.create_response(
            request,
            {"error": "Equipment not found", "message": f"Equipment with ID {equipment_id} does not exist"},
            status=404
        )


@api.get("/equipment/search", response=List[LabEquipmentPageListSchema], tags=["Equipment"])
def search_equipment(request, q: Optional[str] = None, tags: Optional[str] = None, 
                    specs: Optional[str] = None, min_completeness: Optional[float] = None,
                    source_type: Optional[str] = None, needs_review: Optional[bool] = None,
                    limit: int = 50, offset: int = 0):
    """Advanced search for equipment with multiple criteria."""
    # Validate parameters
    if offset < 0:
        return api.create_response(
            request,
            {"error": "Invalid offset", "message": "Offset cannot be negative"},
            status=422
        )
    
    if limit < 1:
        return api.create_response(
            request,
            {"error": "Invalid limit", "message": "Limit must be positive"},
            status=422
        )
    
    queryset = LabEquipmentPage.objects.all()
    
    # Text search
    if q:
        queryset = queryset.filter(
            Q(title__icontains=q) |
            Q(short_description__icontains=q) |
            Q(full_description__icontains=q)
        )
    
    # Tag search
    if tags:
        tag_list = [tag.strip() for tag in tags.split(',')]
        queryset = queryset.filter(categorized_tags__name__in=tag_list).distinct()
    
    # Specification search
    if specs:
        queryset = queryset.filter(
            Q(spec_groups__specs__key__icontains=specs) |
            Q(spec_groups__specs__value__icontains=specs)
        ).distinct()
    
    # Data quality filters
    if min_completeness is not None:
        queryset = queryset.filter(data_completeness__gte=min_completeness)
    
    if source_type:
        queryset = queryset.filter(source_type=source_type)
    
    if needs_review is not None:
        queryset = queryset.filter(needs_review=needs_review)
    
    # Apply ordering and pagination
    queryset = queryset.order_by('-first_published_at')
    equipment_list = list(queryset[offset:offset + limit])
    
    return equipment_list


@api.get("/equipment/{equipment_id}/related", response=RelatedEquipmentResponseSchema, tags=["Equipment"])
def get_related_equipment(request, equipment_id: int):
    """
    Get equipment related to this one (by tags and specifications).
    
    This endpoint works around Wagtail Page inheritance issues by starting from tags
    and working backwards to find equipment, avoiding complex joins.
    """
    try:
        # Use id for Wagtail Page model compatibility (page_ptr.id)
        equipment = LabEquipmentPage.objects.get(id=equipment_id)
        
        # Find related equipment by tags - work backwards from tags to equipment
        from apps.categorized_tags.models import CategorizedPageTag
        equipment_tag_ids = list(equipment.categorized_tags.values_list('id', flat=True))
        
        related_by_tags = []
        if equipment_tag_ids:
            # Find all content_object_ids (Page IDs) that have these tags
            related_page_ids = CategorizedPageTag.objects.filter(
                tag_id__in=equipment_tag_ids
            ).exclude(
                content_object_id=equipment_id  # Exclude current equipment
            ).values_list('content_object_id', flat=True).distinct()[:10]
            
            # Filter to only LabEquipmentPage instances
            if related_page_ids:
                related_by_tags = LabEquipmentPage.objects.filter(
                    id__in=related_page_ids
                )[:5]
                related_by_tags = list(related_by_tags)
        
        # Find related equipment by specification similarity
        # For now, skip specs as they might have similar inheritance issues
        related_by_specs = []
        
        return {
            "related_by_tags": related_by_tags,
            "related_by_specs": related_by_specs
        }
        
    except LabEquipmentPage.DoesNotExist:
        return api.create_response(
            request,
            {"error": "Equipment not found", "message": f"Equipment with ID {equipment_id} does not exist"},
            status=404
        )


# ============ MODEL ENDPOINTS ============

@api.get("/models", response=List[EquipmentModelSchema], tags=["Models"])
def list_equipment_models(request, equipment_id: Optional[int] = None, limit: int = 50, offset: int = 0):
    """List equipment models, optionally filtered by equipment."""
    # Validate parameters
    if offset < 0:
        return api.create_response(
            request,
            {"error": "Invalid offset", "message": "Offset cannot be negative"},
            status=422
        )
    
    if limit < 1:
        return api.create_response(
            request,
            {"error": "Invalid limit", "message": "Limit must be positive"},
            status=422
        )
    
    queryset = EquipmentModel.objects.all()
    
    if equipment_id:
        # Filter by equipment using id (page__id is equivalent to page__page_ptr__id)
        queryset = queryset.filter(page__id=equipment_id)
    
    models_list = list(queryset[offset:offset + limit])
    return models_list


@api.get("/models/{model_id}", response=EquipmentModelSchema, tags=["Models"])
def get_equipment_model(request, model_id: int):
    """Get detailed information about a specific equipment model."""
    try:
        model = EquipmentModel.objects.get(id=model_id)
        return model
    except EquipmentModel.DoesNotExist:
        return api.create_response(
            request,
            {"error": "Model not found", "message": f"Model with ID {model_id} does not exist"},
            status=404
        )


# ============ ACCESSORY ENDPOINTS ============

@api.get("/accessories", response=List[LabEquipmentAccessorySchema], tags=["Accessories"])
def list_accessories(request, limit: int = 50, offset: int = 0):
    """List lab equipment accessories."""
    # Validate parameters
    if offset < 0:
        return api.create_response(
            request,
            {"error": "Invalid offset", "message": "Offset cannot be negative"},
            status=422
        )
    
    if limit < 1:
        return api.create_response(
            request,
            {"error": "Invalid limit", "message": "Limit must be positive"},
            status=422
        )
    
    queryset = LabEquipmentAccessory.objects.all()
    accessories_list = list(queryset[offset:offset + limit])
    return accessories_list


# ============ TAG ENDPOINTS ============

@api.get("/tags", response=List[CategorizedTagSchema], tags=["Tags"])
def list_tags(request, category: Optional[str] = None, limit: int = 100, offset: int = 0):
    """List categorized tags, optionally filtered by category."""
    # Validate parameters
    if offset < 0:
        return api.create_response(
            request,
            {"error": "Invalid offset", "message": "Offset cannot be negative"},
            status=422
        )
    
    if limit < 1:
        return api.create_response(
            request,
            {"error": "Invalid limit", "message": "Limit must be positive"},
            status=422
        )
    
    queryset = CategorizedTag.objects.all()
    
    if category:
        queryset = queryset.filter(category__iexact=category)
    
    tags_list = list(queryset[offset:offset + limit])
    return tags_list


@api.get("/tags/categories", tags=["Tags"])
def get_tag_categories(request):
    """Get all available tag categories."""
    categories = CategorizedTag.objects.values_list('category', flat=True).distinct()
    return {
        'categories': sorted(list(categories))
    }