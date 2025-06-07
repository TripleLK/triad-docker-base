from django.db import models
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from taggit.models import TagBase, ItemBase
from wagtail.models import Page
from modelcluster.contrib.taggit import ClusterTaggableManager
from wagtail.admin.panels import FieldPanel
from django.utils.text import slugify
import random
from django import forms
from .widgets import ColorPickerWidget

def generate_random_color():
    # Generate random hue (0-360), fixed saturation and lightness for consistent brightness
    h = random.randint(0, 360)
    s = 65  # Medium-high saturation (65%)
    l = 75  # Light color (75% lightness) for good contrast with text
    return f"hsl({h}, {s}%, {l}%)"

class TagCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    color = models.CharField(max_length=20, default=generate_random_color, 
                            help_text="Color for this category (HSL format)")
    
    panels = [
        FieldPanel('name'),
        FieldPanel('color', widget=ColorPickerWidget()),
    ]
    
    class Meta:
        verbose_name = "Tag Category"
        verbose_name_plural = "Tag Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name
        
    @property
    def tag_count(self):
        """Get the number of tags in this category"""
        from .models import CategorizedTag
        return CategorizedTag.objects.filter(category=self.name).count()

class CategorizedTag(TagBase):
    category = models.CharField(max_length=100)
    
    panels = [
        FieldPanel('name'),
        FieldPanel('category'),
    ]
    
    class Meta:
        verbose_name = "Categorized Tag"
        verbose_name_plural = "Categorized Tags"
        unique_together = ('name', 'category')
    
    @property
    def category_color(self):
        """Get the color for this tag's category"""
        try:
            category = TagCategory.objects.get(name=self.category)
            return category.color
        except TagCategory.DoesNotExist:
            return "hsl(0, 0%, 90%)"  # Default light gray
    
    def __str__(self):
        return f"{self.category}: {self.name}"
    
    def save(self, *args, **kwargs):
        # Generate the slug from category and name if not explicitly provided
        if not self.slug:
            self.slug = slugify(f"{self.category}-{self.name}")
        
        # Ensure a TagCategory exists for this category
        TagCategory.objects.get_or_create(
            name=self.category,
            defaults={'color': generate_random_color()}
        )
        
        super().save(*args, **kwargs)

class CategorizedTaggedItemBase(ItemBase):
    tag = models.ForeignKey(
        CategorizedTag, related_name="%(app_label)s_%(class)s_items", on_delete=models.CASCADE
    )
    
    class Meta:
        abstract = True


class CategorizedPageTag(CategorizedTaggedItemBase):
    content_object = ParentalKey(to='wagtailcore.Page', on_delete=models.CASCADE, related_name='categorized_tagged_items')
