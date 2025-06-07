"""
Lab Equipment API v2 Serializers - DRF serializers for lab equipment models.

Created by: Noble Harbor
Date: 2025-01-19
Project: Triad Docker Base
"""

from rest_framework import serializers
from apps.base_site.models import (
    LabEquipmentPage, EquipmentModel, LabEquipmentPageSpecGroup, 
    EquipmentModelSpecGroup, Spec, EquipmentFeature, 
    LabEquipmentAccessory, QuoteCartItem, CategorizedPageTag
)
from apps.categorized_tags.models import CategorizedTag
from taggit.models import Tag
from django.utils.text import slugify
import time


class SpecSerializer(serializers.ModelSerializer):
    """Serializer for individual specifications."""
    
    class Meta:
        model = Spec
        fields = ['id', 'key', 'value']


class LabEquipmentPageSpecGroupSerializer(serializers.ModelSerializer):
    """Serializer for specification groups on lab equipment pages."""
    
    specs = SpecSerializer(many=True, read_only=True)
    
    class Meta:
        model = LabEquipmentPageSpecGroup
        fields = ['id', 'name', 'specs']


class EquipmentModelSpecGroupSerializer(serializers.ModelSerializer):
    """Serializer for specification groups on equipment models."""
    
    specs = SpecSerializer(many=True, read_only=True)
    
    class Meta:
        model = EquipmentModelSpecGroup
        fields = ['id', 'name', 'specs']


class EquipmentModelSerializer(serializers.ModelSerializer):
    """Serializer for equipment models."""
    
    spec_groups = EquipmentModelSpecGroupSerializer(many=True, read_only=True)
    merged_spec_groups = serializers.SerializerMethodField()
    
    class Meta:
        model = EquipmentModel
        fields = ['id', 'name', 'model_number', 'spec_groups', 'merged_spec_groups']
    
    def get_merged_spec_groups(self, obj):
        """Get merged spec groups from the model."""
        merged_groups = obj.merged_spec_groups
        # Convert to serializable format
        return [
            {
                'name': group['name'],
                'specs': [{'key': spec.key, 'value': spec.value} for spec in group['specs']]
            }
            for group in merged_groups
        ]


class EquipmentFeatureSerializer(serializers.ModelSerializer):
    """Serializer for equipment features."""
    
    class Meta:
        model = EquipmentFeature
        fields = ['id', 'feature']


class CategorizedTagSerializer(serializers.ModelSerializer):
    """Serializer for categorized tags."""
    
    class Meta:
        model = CategorizedTag
        fields = ['id', 'name', 'category']


class LabEquipmentAccessorySerializer(serializers.ModelSerializer):
    """Serializer for lab equipment accessories."""
    
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = LabEquipmentAccessory
        fields = ['id', 'name', 'model_number', 'image_url']
    
    def get_image_url(self, obj):
        """Get the image URL for the accessory."""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.file.url)
            return obj.image.file.url
        return None


class LabEquipmentPageListSerializer(serializers.ModelSerializer):
    """Serializer for lab equipment page list view (simplified)."""
    
    main_image_url = serializers.SerializerMethodField()
    categorized_tags = CategorizedTagSerializer(many=True, read_only=True)
    model_count = serializers.SerializerMethodField()
    
    class Meta:
        model = LabEquipmentPage
        fields = [
            'page_ptr_id', 'title', 'slug', 'short_description', 'source_type', 
            'data_completeness', 'specification_confidence', 'needs_review',
            'main_image_url', 'categorized_tags', 'model_count', 'live', 'first_published_at'
        ]
    
    def get_main_image_url(self, obj):
        """Get the main image URL."""
        main_image = obj.main_image()
        if main_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(main_image)
            return main_image
        return None
    
    def get_model_count(self, obj):
        """Get the number of models for this equipment."""
        return obj.models.count()


class LabEquipmentPageDetailSerializer(serializers.ModelSerializer):
    """Serializer for lab equipment page detail view (complete)."""
    
    spec_groups = LabEquipmentPageSpecGroupSerializer(many=True, read_only=True)
    models = EquipmentModelSerializer(many=True, read_only=True)
    features = EquipmentFeatureSerializer(many=True, read_only=True)
    accessories = LabEquipmentAccessorySerializer(many=True, read_only=True)
    categorized_tags = CategorizedTagSerializer(many=True, read_only=True)
    
    # Gallery images
    gallery_images = serializers.SerializerMethodField()
    main_image_url = serializers.SerializerMethodField()
    
    # Computed fields
    spec_group_names = serializers.ReadOnlyField()
    
    class Meta:
        model = LabEquipmentPage
        fields = [
            'page_ptr_id', 'title', 'slug', 'short_description', 'full_description',
            'source_url', 'source_type', 'data_completeness', 
            'specification_confidence', 'needs_review',
            'spec_groups', 'models', 'features', 'accessories', 
            'categorized_tags', 'gallery_images', 'main_image_url',
            'spec_group_names', 'live', 'first_published_at', 'last_published_at'
        ]
    
    def get_gallery_images(self, obj):
        """Get all gallery images with URLs."""
        images = []
        for gallery_item in obj.gallery_images.all():
            image_url = gallery_item.get_image_url
            if image_url:
                request = self.context.get('request')
                if request:
                    image_url = request.build_absolute_uri(image_url)
                images.append({
                    'id': gallery_item.id,
                    'url': image_url,
                    'caption': getattr(gallery_item, 'caption', '')
                })
        return images
    
    def get_main_image_url(self, obj):
        """Get the main image URL."""
        main_image = obj.main_image()
        if main_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(main_image)
            return main_image
        return None


class LabEquipmentPageCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating lab equipment pages."""
    
    categorized_tags = serializers.SlugRelatedField(
        many=True, slug_field='name', queryset=CategorizedTag.objects.all(), required=False
    )
    
    # Nested creation fields
    specifications = serializers.JSONField(required=False, help_text="Specifications in JSON format")
    models_data = serializers.JSONField(required=False, help_text="Models in JSON format")
    features_data = serializers.ListField(
        child=serializers.CharField(), required=False, help_text="List of feature strings"
    )
    
    class Meta:
        model = LabEquipmentPage  
        fields = [
            'page_ptr_id', 'title', 'slug', 'short_description', 'full_description',
            'source_url', 'source_type', 'data_completeness',
            'specification_confidence', 'needs_review',
            'categorized_tags', 'specifications', 'models_data', 'features_data'
        ]
        extra_kwargs = {
            'slug': {'required': False}
        }
    
    def create(self, validated_data):
        """Create a new lab equipment page with nested data."""
        # Extract nested data
        specifications = validated_data.pop('specifications', [])
        models_data = validated_data.pop('models_data', [])
        features_data = validated_data.pop('features_data', [])
        categorized_tags = validated_data.pop('categorized_tags', [])
        
        # Find the parent page - assuming the first MultiProductPage as parent
        from wagtail.models import Site
        from apps.base_site.models import MultiProductPage
        
        try:
            site = Site.objects.first()
            root_page = site.root_page
            
            # Try to find a MultiProductPage to use as parent
            parent_pages = MultiProductPage.objects.live()
            if parent_pages.exists():
                parent_page = parent_pages.first()
            else:
                parent_page = root_page
            
            # Create the page
            page = LabEquipmentPage(
                title=validated_data['title'],
                short_description=validated_data.get('short_description', ''),
                full_description=validated_data.get('full_description', ''),
                source_url=validated_data.get('source_url', ''),
                source_type=validated_data.get('source_type', 'new'),
                data_completeness=validated_data.get('data_completeness', 0.5),
                specification_confidence=validated_data.get('specification_confidence', 0.5),
                needs_review=validated_data.get('needs_review', True),
                live=False  # Explicitly set as not live
            )
            
            # Auto-generate slug if not provided
            if not page.slug:
                base_slug = slugify(page.title)
                page.slug = f"{base_slug}-{int(time.time())}"
            
            # Add to parent page
            parent_page.add_child(instance=page)
            
            # Save to generate initial revision
            page.save_revision()
            
            # Add categorized tags if provided
            if categorized_tags:
                page.categorized_tags.set(categorized_tags)
                page.save()
            
            # TODO: Add specifications, models, and features processing here if needed
            # For now, we'll create basic pages without these complex nested structures
            
            return page
            
        except Exception as e:
            raise serializers.ValidationError(f'Error creating lab equipment page: {str(e)}')
    
    def update(self, instance, validated_data):
        """Update an existing lab equipment page."""
        # Extract nested data
        specifications = validated_data.pop('specifications', None)
        models_data = validated_data.pop('models_data', None)
        features_data = validated_data.pop('features_data', None)
        categorized_tags = validated_data.pop('categorized_tags', None)
        
        # Update basic fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Update tags if provided
        if categorized_tags is not None:
            instance.categorized_tags.set(categorized_tags)
        
        # Note: For specifications, models, and features updates,
        # we would need more complex logic to handle the nested relationships
        # This is simplified for now
        
        instance.save()
        return instance


class QuoteCartItemSerializer(serializers.ModelSerializer):
    """Serializer for quote cart items."""
    
    equipment_page = LabEquipmentPageListSerializer(read_only=True)
    equipment_model = EquipmentModelSerializer(read_only=True)
    
    class Meta:
        model = QuoteCartItem
        fields = [
            'id', 'equipment_page_id', 'equipment_model_id', 'model_name',
            'quantity', 'date_added', 'equipment_page', 'equipment_model'
        ]


# Batch operation serializers
class BulkEquipmentCreateSerializer(serializers.Serializer):
    """Serializer for bulk equipment creation operations."""
    
    equipment_list = LabEquipmentPageCreateUpdateSerializer(many=True)
    
    def create(self, validated_data):
        """Create multiple equipment pages in bulk."""
        equipment_list = validated_data['equipment_list']
        created_pages = []
        errors = []
        
        for i, equipment_data in enumerate(equipment_list):
            try:
                serializer = LabEquipmentPageCreateUpdateSerializer(data=equipment_data)
                if serializer.is_valid():
                    page = serializer.save()
                    created_pages.append(page)
                else:
                    errors.append({
                        'index': i,
                        'errors': serializer.errors
                    })
            except Exception as e:
                errors.append({
                    'index': i,
                    'error': str(e)
                })
        
        return {
            'created_pages': created_pages,
            'errors': errors,
            'total_created': len(created_pages),
            'total_errors': len(errors)
        }


class BulkEquipmentUpdateSerializer(serializers.Serializer):
    """Serializer for bulk equipment update operations."""
    
    updates = serializers.ListField(
        child=serializers.DictField(), 
        help_text="List of updates with 'page_ptr_id' and 'data' fields"
    )
    
    def update(self, instance, validated_data):
        """Update multiple equipment pages in bulk."""
        updates = validated_data['updates']
        updated_pages = []
        errors = []
        
        for i, update_item in enumerate(updates):
            try:
                page_ptr_id = update_item.get('page_ptr_id')
                update_data = update_item.get('data', {})
                
                page = LabEquipmentPage.objects.get(page_ptr_id=page_ptr_id)
                serializer = LabEquipmentPageCreateUpdateSerializer(
                    page, data=update_data, partial=True
                )
                
                if serializer.is_valid():
                    updated_page = serializer.save()
                    updated_pages.append(updated_page)
                else:
                    errors.append({
                        'index': i,
                        'page_ptr_id': page_ptr_id,
                        'errors': serializer.errors
                    })
            except LabEquipmentPage.DoesNotExist:
                errors.append({
                    'index': i,
                    'page_ptr_id': page_ptr_id,
                    'error': 'Page not found'
                })
            except Exception as e:
                errors.append({
                    'index': i,
                    'page_ptr_id': page_ptr_id,
                    'error': str(e)
                })
        
        return {
            'updated_pages': updated_pages,
            'errors': errors,
            'total_updated': len(updated_pages),
            'total_errors': len(errors)
        } 