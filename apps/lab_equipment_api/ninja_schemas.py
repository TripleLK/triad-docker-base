"""
Django Ninja Pydantic Schemas for Lab Equipment API v3

Created by: Steady Circuit
Date: 2025-01-08
Project: Triad Docker Base

These schemas replace DRF serializers and provide native Wagtail Page model support,
resolving the page_ptr_id vs id compatibility issues.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import Field, computed_field
from ninja import ModelSchema, Schema

from apps.base_site.models import (
    LabEquipmentPage, EquipmentModel, LabEquipmentPageSpecGroup,
    EquipmentModelSpecGroup, Spec, EquipmentFeature, LabEquipmentAccessory, QuoteCartItem
)
from apps.categorized_tags.models import CategorizedTag


# ============ BASE SCHEMAS ============

class SpecSchema(ModelSchema):
    """Schema for individual specifications."""
    
    class Config:
        model = Spec
        model_fields = ["id", "key", "value"]


class CategorizedTagSchema(ModelSchema):
    """Schema for categorized tags."""
    
    class Config:
        model = CategorizedTag
        model_fields = ["id", "name", "category"]


class EquipmentFeatureSchema(ModelSchema):
    """Schema for equipment features."""
    
    class Config:
        model = EquipmentFeature
        model_fields = ["id", "feature"]


# ============ SPECIFICATION GROUP SCHEMAS ============

class LabEquipmentPageSpecGroupSchema(ModelSchema):
    """Schema for specification groups on lab equipment pages."""
    
    specs: List[SpecSchema] = []
    
    class Config:
        model = LabEquipmentPageSpecGroup
        model_fields = ["id", "name"]

    @staticmethod
    def resolve_specs(obj):
        """Resolve specs for the spec group."""
        return [SpecSchema.from_orm(spec) for spec in obj.specs.all()]


class EquipmentModelSpecGroupSchema(ModelSchema):
    """Schema for specification groups on equipment models."""
    
    specs: List[SpecSchema] = []
    
    class Config:
        model = EquipmentModelSpecGroup
        model_fields = ["id", "name"]

    @staticmethod
    def resolve_specs(obj):
        """Resolve specs for the spec group."""
        return [SpecSchema.from_orm(spec) for spec in obj.specs.all()]


# ============ EQUIPMENT MODEL SCHEMAS ============

class EquipmentModelSchema(ModelSchema):
    """Schema for equipment models."""
    
    spec_groups: List[EquipmentModelSpecGroupSchema] = []
    merged_spec_groups: List[Dict[str, Any]] = []
    
    class Config:
        model = EquipmentModel
        model_fields = ["id", "name"]

    @staticmethod
    def resolve_spec_groups(obj):
        """Resolve spec groups for the model."""
        return [EquipmentModelSpecGroupSchema.from_orm(group) for group in obj.spec_groups.all()]

    @staticmethod
    def resolve_merged_spec_groups(obj):
        """Get merged spec groups from the model."""
        merged_groups = obj.merged_spec_groups
        return [
            {
                'name': group['name'],
                'specs': [{'key': spec.key, 'value': spec.value} for spec in group['specs']]
            }
            for group in merged_groups
        ]


# ============ ACCESSORY SCHEMAS ============

class LabEquipmentAccessorySchema(ModelSchema):
    """Schema for lab equipment accessories."""
    
    image_url: Optional[str] = None
    
    class Config:
        model = LabEquipmentAccessory
        model_fields = ["id", "name", "model_number"]

    @staticmethod
    def resolve_image_url(obj, context=None):
        """Get the image URL for the accessory."""
        if obj.image:
            # In Django Ninja, request context is handled differently
            return obj.image.file.url
        return None


# ============ LAB EQUIPMENT PAGE SCHEMAS ============

class LabEquipmentPageListSchema(ModelSchema):
    """
    Schema for lab equipment page list view (simplified).
    
    This schema handles Wagtail Page models correctly by using page_ptr.id
    as the primary identifier, resolving the DRF compatibility issue.
    """
    
    # Use page_ptr.id to get the actual integer ID value
    id: int = Field(alias="page_ptr.id")
    main_image_url: Optional[str] = None
    categorized_tags: List[CategorizedTagSchema] = []
    model_count: int = 0
    
    class Config:
        model = LabEquipmentPage
        model_fields = [
            "page_ptr", "title", "slug", "short_description", "source_type",
            "data_completeness", "specification_confidence", "needs_review",
            "live", "first_published_at"
        ]

    @staticmethod
    def resolve_main_image_url(obj, context=None):
        """Get the main image URL."""
        main_image = obj.main_image()
        return main_image if main_image else None

    @staticmethod
    def resolve_categorized_tags(obj):
        """Resolve categorized tags for the equipment."""
        return [CategorizedTagSchema.from_orm(tag) for tag in obj.categorized_tags.all()]

    @staticmethod
    def resolve_model_count(obj):
        """Get the number of models for this equipment."""
        return obj.models.count()


class LabEquipmentPageDetailSchema(ModelSchema):
    """
    Schema for lab equipment page detail view (complete).
    
    This schema provides full equipment details with native Wagtail compatibility.
    """
    
    # Use page_ptr.id to get the actual integer ID value
    id: int = Field(alias="page_ptr.id")
    spec_groups: List[LabEquipmentPageSpecGroupSchema] = []
    models: List[EquipmentModelSchema] = []
    features: List[EquipmentFeatureSchema] = []
    accessories: List[LabEquipmentAccessorySchema] = []
    categorized_tags: List[CategorizedTagSchema] = []
    gallery_images: List[Dict[str, Any]] = []
    main_image_url: Optional[str] = None
    spec_group_names: List[str] = []
    
    # SEO helper methods
    meta_title_computed: Optional[str] = None
    meta_description_computed: Optional[str] = None
    structured_data_computed: Dict[str, Any] = {}
    
    class Config:
        model = LabEquipmentPage
        model_fields = [
            "page_ptr", "title", "slug", "short_description", "full_description",
            "source_url", "source_type", "data_completeness",
            "specification_confidence", "needs_review",
            # SEO Fields
            "meta_title", "meta_description", "meta_keywords", "seo_content",
            "target_keywords", "related_keywords", "technical_keywords",
            "applications", "technical_specifications", "structured_data",
            "page_content_sections", "alt_text_suggestions",
            # Standard fields
            "live", "first_published_at", "last_published_at"
        ]

    @staticmethod
    def resolve_spec_groups(obj):
        """Resolve spec groups for the equipment."""
        return [LabEquipmentPageSpecGroupSchema.from_orm(group) for group in obj.spec_groups.all()]

    @staticmethod
    def resolve_models(obj):
        """Resolve models for the equipment."""
        return [EquipmentModelSchema.from_orm(model) for model in obj.models.all()]

    @staticmethod
    def resolve_features(obj):
        """Resolve features for the equipment."""
        return [EquipmentFeatureSchema.from_orm(feature) for feature in obj.features.all()]

    @staticmethod
    def resolve_accessories(obj):
        """Resolve accessories for the equipment."""
        return [LabEquipmentAccessorySchema.from_orm(accessory) for accessory in obj.accessories.all()]

    @staticmethod
    def resolve_categorized_tags(obj):
        """Resolve categorized tags for the equipment."""
        return [CategorizedTagSchema.from_orm(tag) for tag in obj.categorized_tags.all()]

    @staticmethod
    def resolve_gallery_images(obj):
        """Get all gallery images with URLs."""
        images = []
        for gallery_item in obj.gallery_images.all():
            image_url = gallery_item.get_image_url
            if image_url:
                images.append({
                    'id': gallery_item.id,
                    'url': image_url,
                    'caption': getattr(gallery_item, 'caption', '')
                })
        return images

    @staticmethod
    def resolve_main_image_url(obj, context=None):
        """Get the main image URL."""
        main_image = obj.main_image()
        return main_image if main_image else None

    @staticmethod
    def resolve_spec_group_names(obj):
        """Get spec group names."""
        return obj.spec_group_names
    
    @staticmethod
    def resolve_meta_title_computed(obj):
        """Get computed meta title."""
        return obj.get_meta_title()
    
    @staticmethod
    def resolve_meta_description_computed(obj):
        """Get computed meta description."""
        return obj.get_meta_description()
    
    @staticmethod
    def resolve_structured_data_computed(obj):
        """Get computed structured data."""
        return obj.get_structured_data()


# ============ QUOTE CART SCHEMAS ============

class QuoteCartItemSchema(ModelSchema):
    """Schema for quote cart items."""
    
    equipment_page: Optional[LabEquipmentPageListSchema] = None
    equipment_model: Optional[EquipmentModelSchema] = None
    
    class Config:
        model = QuoteCartItem
        model_fields = [
            "id", "session_key", "equipment_page_id", "equipment_model_id", 
            "model_name", "quantity", "date_added"
        ]

    @staticmethod
    def resolve_equipment_page(obj):
        """Resolve the equipment page."""
        try:
            equipment_page = LabEquipmentPage.objects.get(id=obj.equipment_page_id)
            return LabEquipmentPageListSchema.from_orm(equipment_page)
        except LabEquipmentPage.DoesNotExist:
            return None

    @staticmethod
    def resolve_equipment_model(obj):
        """Resolve the equipment model."""
        if obj.equipment_model_id:
            try:
                equipment_model = EquipmentModel.objects.get(id=obj.equipment_model_id)
                return EquipmentModelSchema.from_orm(equipment_model)
            except EquipmentModel.DoesNotExist:
                return None
        return None


# ============ REQUEST/RESPONSE SCHEMAS ============

class EquipmentSearchSchema(Schema):
    """Schema for equipment search requests."""
    
    q: Optional[str] = Field(None, description="Text search query")
    tags: Optional[str] = Field(None, description="Comma-separated tag names")
    specs: Optional[str] = Field(None, description="Specification search")
    min_completeness: Optional[float] = Field(None, description="Minimum data completeness")
    source_type: Optional[str] = Field(None, description="Equipment source type")
    needs_review: Optional[bool] = Field(None, description="Filter by review status")


class RelatedEquipmentResponseSchema(Schema):
    """Schema for related equipment API response."""
    
    related_by_tags: List[LabEquipmentPageListSchema]
    related_by_specs: List[LabEquipmentPageListSchema]


class PaginatedEquipmentResponseSchema(Schema):
    """Schema for paginated equipment responses."""
    
    count: int
    next: Optional[str] = None
    previous: Optional[str] = None
    results: List[LabEquipmentPageListSchema]


# ============ ERROR SCHEMAS ============

class ErrorResponseSchema(Schema):
    """Schema for error responses."""
    
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None 