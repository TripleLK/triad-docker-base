from django.db import models
from wagtail.models import Page, Orderable, ClusterableModel
from wagtail.admin.panels import FieldRowPanel, FieldPanel, InlinePanel
from modelcluster.fields import ParentalKey, ParentalManyToManyField
from wagtail.fields import RichTextField
from wagtail.search import index
from taggit.models import TaggedItemBase
from modelcluster.contrib.taggit import ClusterTaggableManager

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
    pass

class ContactPage(Page):
    pass

class MultiProductPage(Page):
    pass

class Spec(ClusterableModel):
    SpecGroup = ParentalKey(
        'SpecGroup',
        related_name='specs',
    )
    key = models.CharField(
        max_length=32,
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
        max_length=32,
        help_text="The name of the specification group (e.g. dimensions, construction, electrical, etc.)"
    )

class EquipmentModelSpecGroup(SpecGroup):
    EquipmentModel = ParentalKey(
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

class LabEquipmentTag(TaggedItemBase):
    content_object = ParentalKey(
        'LabEquipmentPage',
        related_name='tagged_items',
        on_delete=models.CASCADE
    )

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
        max_length=128,
        help_text="The name of the model"
    )

    model_number = models.CharField(
        max_length=32,
        help_text="The identification number of the model"
    )

    panels = [
        FieldPanel('name'),
        FieldPanel('model_number'),
        InlinePanel('spec_groups', label="Specification Groups"),
    ]

    @property
    def merged_spec_groups(self):
        """
        Returns the merged spec groups for this model (default specs overridden
        by model-specific specs). This calls LabEquipmentPage.get_effective_spec_groups.
        """
        print(self.page.get_effective_spec_groups(self))
        return self.page.get_effective_spec_groups(self)

class LabEquipmentGalleryImage(Orderable):
    page = ParentalKey(
        'LabEquipmentPage',
        related_name='gallery_images',
    )

    image = models.ForeignKey(
        'wagtailimages.Image', on_delete=models.CASCADE, related_name='+'
    )

    panels = [FieldPanel('image')]

class LabEquipmentPage(Page):
    """
    A page model for a single lab equipment item.
    """
    short_description = RichTextField(
        blank=True,
        help_text="A brief summary of the equipment."
    )

    full_description = RichTextField(
        blank=True,
        help_text="Detailed description of the equipment."
    )

    tags = ClusterTaggableManager(through=LabEquipmentTag, blank=True)

    content_panels = Page.content_panels + [
        FieldPanel('short_description', classname="full"),
        FieldPanel('full_description', classname="full"),
        FieldPanel('tags'),
        InlinePanel('gallery_images', label='Images'),
        InlinePanel(
            'spec_groups',
            label="Specification Groups",
            help_text="Technical specifications about the piece of equipment. "
            "You can provide default specs here which may be overridden for a particular model."
        ),
        InlinePanel('models', label='Models'),
    ]

    subpage_types = []  # No subpages allowed for a detail page

    class Meta:
        verbose_name = "Lab Equipment Page"

    def main_image(self):
        gallery_item = self.gallery_images.first()
        if gallery_item:
            return gallery_item.image
        else:
            return None

    @property
    def spec_group_names(self):
        print("getting spec_group_names")
        spec_group_names = set()
        for model in self.models.all():
            print("a model")
            spec_groups = self.get_effective_spec_groups(model)
            for spec_group in spec_groups:
                spec_group_names.add(spec_group['name'])

        print("returning: " + str(spec_group_names))
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
