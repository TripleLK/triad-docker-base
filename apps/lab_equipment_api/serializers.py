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
import logging


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
        fields = ['id', 'name', 'spec_groups', 'merged_spec_groups']
    
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
    
    # SEO helper methods
    meta_title_computed = serializers.SerializerMethodField()
    meta_description_computed = serializers.SerializerMethodField()
    structured_data_computed = serializers.SerializerMethodField()
    
    class Meta:
        model = LabEquipmentPage
        fields = [
            'page_ptr_id', 'title', 'slug', 'short_description', 'full_description',
            'source_url', 'source_type', 'data_completeness', 
            'specification_confidence', 'needs_review',
            # SEO Fields
            'meta_title', 'meta_description', 'meta_keywords', 'seo_content',
            'target_keywords', 'related_keywords', 'technical_keywords',
            'applications', 'technical_specifications', 'structured_data',
            'page_content_sections', 'alt_text_suggestions',
            # Computed SEO fields
            'meta_title_computed', 'meta_description_computed', 'structured_data_computed',
            # Related objects
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
    
    def get_meta_title_computed(self, obj):
        """Get computed meta title."""
        return obj.get_meta_title()
    
    def get_meta_description_computed(self, obj):
        """Get computed meta description."""
        return obj.get_meta_description()
    
    def get_structured_data_computed(self, obj):
        """Get computed structured data."""
        return obj.get_structured_data()


class LabEquipmentPageCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating lab equipment pages."""
    
    categorized_tags = serializers.SlugRelatedField(
        many=True, slug_field='name', queryset=CategorizedTag.objects.all(), required=False
    )
    
    # Nested creation fields
    specifications = serializers.JSONField(required=False, help_text="Specifications in JSON format")
    models_data = serializers.JSONField(required=False, help_text="Models in JSON format")
    features_data = serializers.JSONField(required=False, help_text="Features in JSON format")
    
    # Image processing fields
    image_urls = serializers.ListField(
        child=serializers.URLField(), required=False, 
        help_text="List of image URLs to download and add to gallery"
    )
    base_url = serializers.URLField(
        required=False, 
        help_text="Base URL for converting relative image URLs to absolute URLs"
    )
    
    class Meta:
        model = LabEquipmentPage  
        fields = [
            'page_ptr_id', 'title', 'slug', 'short_description', 'full_description',
            'source_url', 'source_type', 'data_completeness',
            'specification_confidence', 'needs_review',
            # SEO Fields
            'meta_title', 'meta_description', 'meta_keywords', 'seo_content',
            'target_keywords', 'related_keywords', 'technical_keywords',
            'applications', 'technical_specifications', 'structured_data',
            'page_content_sections', 'alt_text_suggestions',
            # Creation fields
            'categorized_tags', 'specifications', 'models_data', 'features_data',
            # Image processing fields
            'image_urls', 'base_url'
        ]
        extra_kwargs = {
            'slug': {'required': False},
            'page_ptr_id': {'read_only': True},
        }
    
    def create(self, validated_data):
        """Create a new lab equipment page with nested data."""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"=== Starting LabEquipmentPage creation ===")
        logger.info(f"Validated data keys: {list(validated_data.keys())}")
        
        # Extract nested data
        specifications = validated_data.pop('specifications', {})
        models_data = validated_data.pop('models_data', [])
        features_data = validated_data.pop('features_data', [])
        categorized_tags = validated_data.pop('categorized_tags', [])
        
        # Extract image processing data
        image_urls = validated_data.pop('image_urls', [])
        base_url = validated_data.pop('base_url', None)
        alt_text_suggestions = validated_data.get('alt_text_suggestions', [])
        
        # Store whether the page should be published at the end
        should_be_published = validated_data.pop('should_be_published', False)
        
        logger.info(f"Extracted specifications: {len(specifications) if specifications else 0} groups")
        logger.info(f"Extracted models_data: {len(models_data) if models_data else 0} models")
        logger.info(f"Extracted features_data: {len(features_data) if features_data else 0} features") 
        logger.info(f"Extracted categorized_tags: {len(categorized_tags) if categorized_tags else 0} tags")
        logger.info(f"Extracted image_urls: {len(image_urls) if image_urls else 0} URLs")
        
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
            
            # Create the page with all the validated data
            page = LabEquipmentPage(**validated_data)
            
            # Auto-generate slug if not provided
            if not page.slug:
                base_slug = slugify(page.title)
                page.slug = f"{base_slug}-{int(time.time())}"
            
            # Set as live initially to ensure relationships are properly saved
            page.live = True
            
            # Add to parent page
            parent_page.add_child(instance=page)
            
            # Save and publish to generate initial revision and ensure proper DB relationships
            revision = page.save_revision()
            revision.publish()
            logger.info(f"Initial page created and published with ID: {page.id}")
            
            # Add categorized tags if provided
            if categorized_tags:
                page.categorized_tags.set(categorized_tags)
                page.save()
            
            # Process specifications if provided
            if specifications:
                logger.info(f"Calling create_specification_groups with {len(specifications)} groups")
                self.create_specification_groups(page, specifications)
            else:
                logger.info("No specifications to create")
            
            # Process models if provided
            if models_data:
                logger.info(f"Calling create_models with {len(models_data)} models")
                self.create_models(page, models_data)
            else:
                logger.info("No models to create")
            
            # Process features if provided  
            if features_data:
                logger.info(f"Calling create_features with {len(features_data)} features")
                self.create_features(page, features_data)
            else:
                logger.info("No features to create")
            
            # Process images if provided
            if image_urls:
                logger.info(f"Processing {len(image_urls)} images for gallery")
                self.process_images(page, image_urls, alt_text_suggestions, base_url)
            else:
                logger.info("No images to process")
            
            # Save and publish again to ensure all relationships are properly saved
            revision = page.save_revision()
            revision.publish()
            logger.info("Page published with all relationships")
            
            # If the page should not be published at the end, unpublish it
            if not should_be_published:
                page.live = False
                page.save_revision().publish()
                logger.info("Page unpublished as requested")
            
            return page
            
        except Exception as e:
            logger.error(f"Error creating lab equipment page: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise serializers.ValidationError(f'Error creating lab equipment page: {str(e)}')
    
    def create_specification_groups(self, page, specifications):
        """Create specification groups from JSON data."""
        from apps.base_site.models import LabEquipmentPageSpecGroup, Spec
        
        for group_name, specs in specifications.items():
            spec_group = LabEquipmentPageSpecGroup.objects.create(
                LabEquipmentPage=page,
                name=group_name
            )
            
            for key, value in specs.items():
                Spec.objects.create(
                    spec_group=spec_group,
                    key=key,
                    value=str(value)
                )
    
    def create_models(self, page, models_data):
        """Create equipment models from JSON data."""
        from apps.base_site.models import EquipmentModel, EquipmentModelSpecGroup, Spec
        
        logger = logging.getLogger(__name__)
        
        logger.info(f"Creating models for page: {page.title}")
        logger.info(f"Models data type: {type(models_data)}")
        logger.info(f"Models data length: {len(models_data) if hasattr(models_data, '__len__') else 'No length'}")
        
        if not models_data:
            logger.warning("No models data provided")
            return
            
        if not isinstance(models_data, list):
            logger.error(f"Models data should be list, got: {type(models_data)}")
            return
        
        for i, model_data in enumerate(models_data):
            logger.info(f"Processing model {i+1}: {model_data.get('model_name', 'Unknown')}")
            
            try:
                # Prepare model creation kwargs
                model_kwargs = {
                    'page': page,
                    'name': model_data.get('model_name', ''),
                }
                
                # Only add model_number if it exists in the data
                if model_data.get('model_number'):
                    model_kwargs['model_number'] = model_data['model_number']
                
                logger.info(f"Creating EquipmentModel with kwargs: {model_kwargs}")
                model = EquipmentModel.objects.create(**model_kwargs)
                logger.info(f"Created model: {model.id} - {model.name}")
                
                # Create model-specific specification groups
                model_specs = model_data.get('specifications', {})
                logger.info(f"Creating {len(model_specs)} spec groups for model {model.name}")
                
                for group_name, specs in model_specs.items():
                    spec_group = EquipmentModelSpecGroup.objects.create(
                        equipment_model=model,
                        name=group_name
                    )
                    logger.info(f"Created spec group: {spec_group.name}")
                    
                    for key, value in specs.items():
                        spec = Spec.objects.create(
                            spec_group=spec_group,
                            key=key,
                            value=str(value)
                        )
                        logger.info(f"  Created spec: {key} = {value}")
                        
            except Exception as e:
                logger.error(f"Error creating model {i+1}: {e}")
                import traceback
                logger.error(traceback.format_exc())
    
    def create_features(self, page, features_data):
        """Create equipment features from JSON data."""
        from apps.base_site.models import EquipmentFeature
        
        # Handle both list of strings and list of objects
        if isinstance(features_data, list):
            for i, feature in enumerate(features_data):
                if isinstance(feature, str):
                    feature_text = feature
                elif isinstance(feature, dict):
                    feature_text = feature.get('feature', str(feature))
                else:
                    feature_text = str(feature)
                
                EquipmentFeature.objects.create(
                    page=page,
                    feature=feature_text,
                    sort_order=i
                )
    
    def process_images(self, page, image_urls, alt_text_suggestions=None, base_url=None):
        """Process image URLs and create gallery images for the page."""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            from apps.base_site.utils.image_utils import process_image_urls, create_gallery_images
            
            logger.info(f"Processing {len(image_urls)} images for page: {page.title}")
            
            # Download images from URLs
            images = process_image_urls(
                image_urls=image_urls,
                alt_texts=alt_text_suggestions,
                base_url=base_url
            )
            
            if images:
                # Create gallery images
                gallery_images = create_gallery_images(
                    page=page,
                    images=images,
                    alt_texts=alt_text_suggestions
                )
                
                logger.info(f"Successfully created {len(gallery_images)} gallery images")
            else:
                logger.warning("No images were successfully downloaded")
                
        except Exception as e:
            logger.error(f"Error processing images for page {page.title}: {str(e)}")
            # Don't raise exception - allow page creation to continue even if images fail
    
    def update(self, instance, validated_data):
        """Update an existing lab equipment page."""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"=== Starting LabEquipmentPage update for: {instance.title} ===")
        
        # Extract nested data
        specifications = validated_data.pop('specifications', None)
        models_data = validated_data.pop('models_data', None)
        features_data = validated_data.pop('features_data', None)
        categorized_tags = validated_data.pop('categorized_tags', None)
        
        # Extract image processing data
        image_urls = validated_data.pop('image_urls', None)
        base_url = validated_data.pop('base_url', None)
        alt_text_suggestions = validated_data.get('alt_text_suggestions', [])
        
        # Store whether the page should be published at the end
        should_be_published = validated_data.pop('should_be_published', instance.live)
        was_live = instance.live
        
        logger.info(f"Update data - specs: {len(specifications) if specifications else 0}, models: {len(models_data) if models_data else 0}, features: {len(features_data) if features_data else 0}, tags: {len(categorized_tags) if categorized_tags else 0}, images: {len(image_urls) if image_urls else 0}")
        
        # Update basic fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Make sure the page is live for the update to ensure relationships are properly saved
        if not instance.live:
            instance.live = True
            logger.info("Temporarily setting page to live for update")
        
        # Save and publish the initial changes
        revision = instance.save_revision()
        revision.publish()
        logger.info("Initial page updates published")
        
        # Update categorized tags if provided
        if categorized_tags is not None:
            logger.info(f"Updating categorized tags: {categorized_tags}")
            instance.categorized_tags.set(categorized_tags)
        
        # Handle nested objects - clear existing and recreate
        if specifications is not None:
            logger.info("Clearing existing specification groups and recreating")
            # Clear existing spec groups
            instance.spec_groups.all().delete()
            # Recreate from new data
            if specifications:
                self.create_specification_groups(instance, specifications)
        
        if models_data is not None:
            logger.info("Clearing existing models and recreating")
            # Clear existing models (this will cascade to their spec groups)
            instance.models.all().delete()
            # Recreate from new data
            if models_data:
                self.create_models(instance, models_data)
        
        if features_data is not None:
            logger.info("Clearing existing features and recreating")
            # Clear existing features
            instance.features.all().delete()
            # Recreate from new data
            if features_data:
                self.create_features(instance, features_data)
        
        # Process images if provided
        if image_urls is not None:
            logger.info("Processing updated images for gallery")
            # Clear existing gallery images
            instance.gallery_images.all().delete()
            # Process new images if any
            if image_urls:
                self.process_images(instance, image_urls, alt_text_suggestions, base_url)
        
        # Save and publish again to ensure all relationships are properly saved
        revision = instance.save_revision()
        revision.publish()
        logger.info("All updates published")
        
        # Restore the page's original publish state if needed
        if not should_be_published:
            instance.live = False
            instance.save_revision().publish()
            logger.info("Page unpublished as requested")
        elif should_be_published != was_live:
            logger.info(f"Page publish state changed from {was_live} to {should_be_published}")
        
        logger.info(f"=== Completed LabEquipmentPage update for: {instance.title} ===")
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