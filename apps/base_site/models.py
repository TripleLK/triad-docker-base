from django.db import models
from wagtail.models import Page, Orderable, ClusterableModel
from wagtail.admin.panels import FieldRowPanel, FieldPanel, InlinePanel
from modelcluster.fields import ParentalKey, ParentalManyToManyField
from wagtail.fields import RichTextField
from wagtail.search import index
from taggit.models import TaggedItemBase
from modelcluster.contrib.taggit import ClusterTaggableManager
from apps.categorized_tags.models import CategorizedPageTag
from apps.categorized_tags.forms import CategoryTagForm
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
import uuid

class BasicPage(Page):
    intro = models.CharField(max_length=250)
    body = RichTextField(blank=True)

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        index.SearchField('body')
    ]

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        FieldPanel("body")
    ]

class CartPage(Page):
    """
    The quote cart page that displays items added to the quote cart
    and provides a form to request a quote.
    """
    intro_text = RichTextField(
        blank=True,
        help_text="Introductory text for the quote cart page"
    )
    
    empty_cart_text = RichTextField(
        blank=True, 
        default="Your quote cart is empty. Browse our products to add items to your quote request.",
        help_text="Text to display when the cart is empty"
    )
    
    success_message = RichTextField(
        blank=True,
        default="Thank you for your quote request. We will get back to you as soon as possible.",
        help_text="Message to display after submitting a quote request"
    )
    
    content_panels = Page.content_panels + [
        FieldPanel('intro_text'),
        FieldPanel('empty_cart_text'),
        FieldPanel('success_message')
    ]
    
    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        
        # Get session key
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key
        
        # Get cart items
        cart_items = QuoteCartItem.objects.filter(session_key=session_key)
        
        context['cart_items'] = cart_items
        context['cart_count'] = cart_items.count()
        
        return context

class ContactPage(Page):
    """
    Contact page model that also handles quote requests
    """
    intro_title = models.CharField(
        max_length=255,
        default="Contact Us",
        help_text="Title for the contact page"
    )
    
    intro_text = RichTextField(
        blank=True,
        help_text="Introductory text for the contact page"
    )
    
    thank_you_text = RichTextField(
        blank=True,
        default="Thank you for contacting us. We will get back to you as soon as possible.",
        help_text="Text to display after form submission"
    )
    
    quote_request_title = models.CharField(
        max_length=255,
        default="Request a Quote",
        help_text="Title for quote request section"
    )
    
    quote_request_text = RichTextField(
        blank=True, 
        default="Fill out the form below to request a quote for the items in your cart.",
        help_text="Text to display above quote request form"
    )
    
    content_panels = Page.content_panels + [
        FieldPanel('intro_title'),
        FieldPanel('intro_text'),
        FieldPanel('thank_you_text'),
        FieldPanel('quote_request_title'),
        FieldPanel('quote_request_text'),
    ]
    
    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        
        # Get session key
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key
        
        # Get cart items
        cart_items = QuoteCartItem.objects.filter(session_key=session_key)
        
        context['cart_items'] = cart_items
        context['cart_count'] = cart_items.count()
        
        return context

class HomePage(Page):
    """
    Home page model that displays a hero section, categories, featured products, and about section.
    """
    hero_title = models.CharField(
        max_length=255,
        default="Welcome to Triad Scientific",
        help_text="Title for the hero section"
    )
    
    hero_subtitle = models.CharField(
        max_length=255,
        default="Your trusted source for high-quality lab equipment and scientific supplies",
        help_text="Subtitle for the hero section"
    )
    
    about_title = models.CharField(
        max_length=255,
        default="About Triad Scientific",
        help_text="Title for the about section"
    )
    
    about_content = RichTextField(
        default="Triad Scientific has been a leading provider of laboratory equipment for over 20 years. "
                "We offer a comprehensive range of high-quality scientific instruments, supplies, and accessories.",
        help_text="Content for the about section"
    )
    
    about_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text="Image for the about section"
    )
    
    content_panels = Page.content_panels + [
        FieldPanel('hero_title'),
        FieldPanel('hero_subtitle'),
        FieldPanel('about_title'),
        FieldPanel('about_content'),
        FieldPanel('about_image'),
    ]
    
    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        
        # Get featured lab equipment pages - just getting the first 3 for simplicity
        featured_products = LabEquipmentPage.objects.live().order_by('?')[:3]  # Random selection
        
        context['featured_products'] = featured_products
        
        return context

class MultiProductPage(Page):
    """
    A page that displays multiple lab equipment products with search and filtering options.
    """
    intro_title = models.CharField(
        max_length=255,
        blank=True,
        help_text="Title to display at the top of the page"
    )
    
    intro_text = RichTextField(
        blank=True,
        help_text="Introductory text to display at the top of the page"
    )
    
    search_fields = Page.search_fields + [
        index.SearchField('intro_title'),
        index.SearchField('intro_text'),
    ]
    
    content_panels = Page.content_panels + [
        FieldPanel('intro_title'),
        FieldPanel('intro_text'),
    ]
    
    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        
        # Get all lab equipment pages
        equipment_pages = LabEquipmentPage.objects.live().order_by('title')
        
        # Pagination
        page = request.GET.get('page', 1)
        paginator = Paginator(equipment_pages, 12)  # Show 12 products per page
        
        try:
            equipment_pages = paginator.page(page)
        except PageNotAnInteger:
            equipment_pages = paginator.page(1)
        except EmptyPage:
            equipment_pages = paginator.page(paginator.num_pages)
        
        context['search_results'] = equipment_pages
        
        # Pass a flag to indicate these are not search results
        context['is_search_results'] = False
        
        return context

class Spec(ClusterableModel):
    spec_group = ParentalKey(
        'SpecGroup',
        related_name='specs',
    )
    key = models.CharField(
        max_length=128,
        help_text="What the specification is measuring (e.g. height)"
    )
    value = models.CharField(
        max_length=256,
        help_text="The value of the specification (e.g. 50in)"
    )

    panels = [
        FieldRowPanel([
            FieldPanel('key'),
            FieldPanel('value'),
        ])
    ]

class SpecGroup(ClusterableModel):
    name = models.CharField(
        max_length=128,
        help_text="The name of the specification group (e.g. dimensions, construction, electrical, etc.)"
    )

class EquipmentModelSpecGroup(SpecGroup):
    equipment_model = ParentalKey(
        'EquipmentModel',
        related_name='spec_groups',
    )

    panels = [
        FieldPanel('name'),
        InlinePanel('specs', label="Specifications"),
    ]

class LabEquipmentPageSpecGroup(SpecGroup):
    LabEquipmentPage = ParentalKey(
        'LabEquipmentPage',
        related_name='spec_groups',
    )

    panels = [
        FieldPanel( "name" ),
        InlinePanel('specs', label="Specifications"),
    ]

class EquipmentFeature(Orderable):
    """
    An orderable model for equipment features (non-pairs).
    Each equipment page can have multiple features.
    """
    page = ParentalKey(
        'LabEquipmentPage',
        related_name='features'
    )

    feature = models.CharField(
        max_length=255,
        help_text="A single equipment feature."
    )

    panels = [
        FieldPanel('feature'),
    ]

    def __str__(self):
        return self.feature

class EquipmentModel(ClusterableModel):
    page = ParentalKey(
        'LabEquipmentPage',
        related_name='models',
    )

    name = models.CharField(
        max_length=255,
        help_text="The name of the model"
    )

    panels = [
        FieldPanel('name'),
        InlinePanel('spec_groups', label="Specification Groups"),
    ]

    @property
    def merged_spec_groups(self):
        """
        Returns the merged spec groups for this model (default specs overridden
        by model-specific specs). This calls LabEquipmentPage.get_effective_spec_groups.
        """
        return self.page.get_effective_spec_groups(self)

class LabEquipmentGalleryImage(Orderable):
    page = ParentalKey(
        'LabEquipmentPage',
        related_name='gallery_images',
        on_delete=models.CASCADE
    )

    # Field for uploaded image (internal)
    internal_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='+'
    )

    # Field for an external image URL
    external_image_url = models.URLField(
        "External image URL",
        blank=True,
        help_text="If provided, this will be used instead of an uploaded image."
    )

    # Flag to indicate if this is a fallback image (to avoid recursion in templates)
    is_fallback = models.BooleanField(default=False, editable=False)

    panels = [
        FieldPanel('internal_image'),
        FieldPanel('external_image_url'),
    ]

    def get_image_url(self):
        """
        Returns the URL to be used:
         - Prefer the internal image if it exists
         - Otherwise, use the external image URL
         - If neither is available, return None
        
        Note: External images are now used with an onerror handler in the template
        to fallback to a default image if the external URL has CORS issues.
        """
        if self.internal_image:
            # Prefer internal images as they won't have CORS issues
            rendition = self.internal_image.get_rendition('fill-800x600')
            return rendition.url
        elif self.external_image_url and not self.is_fallback:
            # External image - template will handle CORS issues with onerror
            return self.external_image_url
        return None

class LabEquipmentPage(Page):
    """
    A page model for a single lab equipment item.
    """
    SOURCE_TYPES = (
        ('new', 'New Equipment'),
        ('used', 'Used Equipment'),
        ('refurbished', 'Refurbished Equipment'),
        ('unknown', 'Unknown'),
    )

    short_description = RichTextField(
        blank=True,
        help_text="A brief summary of the equipment."
    )

    full_description = RichTextField(
        blank=True,
        help_text="Detailed description of the equipment."
    )
    
    source_url = models.URLField(
        verbose_name="Source URL",
        blank=True, 
        null=True,
        help_text="Original URL where this product information was sourced from"
    )

    source_type = models.CharField(
        max_length=20,
        choices=SOURCE_TYPES,
        default='unknown',
        help_text="Indicates whether this is new, used, or refurbished equipment"
    )

    data_completeness = models.FloatField(
        default=1.0,
        help_text="Score from 0.0 to 1.0 indicating how complete the product data is"
    )

    specification_confidence = models.CharField(
        max_length=10,
        choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')],
        default='high',
        help_text="Confidence level in the accuracy of the specifications"
    )

    needs_review = models.BooleanField(
        default=False,
        help_text="Flag indicating this listing needs manual review"
    )

    # This field will store our custom tags
    # tags = ClusterTaggableManager(through=CategoryPageTag, blank=True)
    categorized_tags = ClusterTaggableManager(through=CategorizedPageTag, blank=True)

    content_panels = Page.content_panels + [
        FieldPanel('short_description', classname="full"),
        FieldPanel('full_description', classname="full"),
        FieldPanel('source_url'),
        FieldPanel('source_type'),
        FieldPanel('data_completeness'),
        FieldPanel('specification_confidence'),
        FieldPanel('needs_review'),
        FieldPanel('categorized_tags'),
        InlinePanel('gallery_images', label='Images'),
        InlinePanel(
            'spec_groups',
            label="Specification Groups",
            help_text="Technical specifications about the piece of equipment. "
            "You can provide default specs here which may be overridden for a particular model."
        ),
        InlinePanel('models', label='Models'),
    ]

    base_form_class = CategoryTagForm

    subpage_types = []  # No subpages allowed for a detail page

    class Meta:
        verbose_name = "Lab Equipment Page"

    def main_image(self):
        gallery_item = self.gallery_images.first()
        if gallery_item:
            return gallery_item.get_image_url
        else:
            return None

    @property
    def spec_group_names(self):
        spec_group_names = set()
        for model in self.models.all():
            spec_groups = self.get_effective_spec_groups(model)
            for spec_group in spec_groups:
                spec_group_names.add(spec_group['name'])

        return sorted(list(spec_group_names))

    def get_effective_spec_groups(self, equipment_model=None):
        """
        Returns a list of merged spec groups (each a dict with a name and a list of specs)
        If an equipment_model is passed, then any spec group in that model overrides the default.
        Otherwise, just the page-level spec groups are returned.
        """
        effective = {}

        # Gather all shared spec groups
        for group in self.spec_groups.all():
            effective[group.name] = {
                'name': group.name,
                'specs': list(group.specs.all())
            }

        # If a model is provided, override or add spec groups.
        if equipment_model:
            for group in equipment_model.spec_groups.all():
                if group.name in effective:
                    effective[group.name]['specs'] += list(group.specs.all())
                else:
                    effective[group.name] = {
                        'name': group.name,
                        'specs': list(group.specs.all())
                       }

        # Return as a list – you can sort by name or leave unsorted.
        return sorted(effective.values(), key=lambda x: x['name'])

class LabEquipmentAccessory(ClusterableModel):
    page = ParentalManyToManyField(
        'LabEquipmentPage',related_name='accessories',
    )
    image = models.ForeignKey(
        'wagtailimages.Image',
        related_name='+',
        on_delete=models.CASCADE
    )

    model_number = models.CharField(
        max_length=32,
        help_text="The identification number of the accessory"
    )

    name = models.CharField(
        max_length=32,
        help_text="The name of the accessory"
    )

    panels = [
        FieldPanel('name'),
        FieldPanel('model_number'),
        FieldPanel('image'),
    ]

# Quote Cart models
class QuoteCartItem(models.Model):
    """
    Model for items in the quote cart. These are stored in the session.
    """
    session_key = models.CharField(max_length=40)
    equipment_page_id = models.IntegerField()
    equipment_model_id = models.IntegerField(null=True, blank=True)  # Can be null for items without specific models
    model_name = models.CharField(max_length=128)
    quantity = models.PositiveIntegerField(default=1)
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_added']

    def __str__(self):
        return f"{self.model_name} - Qty: {self.quantity}"

    @property
    def equipment_page(self):
        return LabEquipmentPage.objects.get(id=self.equipment_page_id)

    @property
    def equipment_model(self):
        if self.equipment_model_id:
            try:
                return EquipmentModel.objects.get(id=self.equipment_model_id)
            except EquipmentModel.DoesNotExist:
                return None
        return None

class QuoteRequest(models.Model):
    """
    Model for storing quote requests from users.
    """
    INQUIRY_TYPES = (
        ('general', 'General Inquiry'),
        ('pricing', 'Pricing Request'),
        ('availability', 'Availability Check'),
        ('customization', 'Customization Options'),
        ('other', 'Other'),
    )

    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    company = models.CharField(max_length=100, blank=True)
    inquiry_type = models.CharField(max_length=20, choices=INQUIRY_TYPES, default='pricing')
    message = models.TextField()
    session_key = models.CharField(max_length=40)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Quote Request from {self.name} ({self.created_at.strftime('%Y-%m-%d')})"
    
    @property
    def cart_items(self):
        return QuoteCartItem.objects.filter(session_key=self.session_key)

# Add the APIToken model at the end of the file
class APIToken(models.Model):
    """
    Model for API authentication tokens with name, description, and token value.
    """
    name = models.CharField(max_length=100, help_text="Friendly name for this token")
    token = models.CharField(max_length=64, unique=True, editable=False, help_text="Authentication token")
    description = models.TextField(blank=True, help_text="Description of what this token is used for")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, help_text="Whether this token is active and can be used")
    
    def __str__(self):
        return f"{self.name} ({self.created_at.strftime('%Y-%m-%d')})"
    
    def save(self, *args, **kwargs):
        # Generate a new token if one doesn't exist
        if not self.token:
            self.token = uuid.uuid4().hex
        super().save(*args, **kwargs)
