from django import forms
from django.utils.safestring import mark_safe
from .models import URLProcessingRequest, BatchURLProcessingRequest, SelectorConfiguration


class URLProcessingForm(forms.ModelForm):
    """Form for processing a URL with AWS Bedrock."""
    
    SELECTOR_CHOICE_CONFIG = 'config'
    SELECTOR_CHOICE_MANUAL = 'manual'
    
    selector_choice = forms.ChoiceField(
        choices=[
            (SELECTOR_CHOICE_CONFIG, 'Use Selector Configuration'),
            (SELECTOR_CHOICE_MANUAL, 'Use Manual Selectors'),
        ],
        widget=forms.RadioSelect(),
        initial=SELECTOR_CHOICE_MANUAL,
        required=True,
        help_text=mark_safe(
            '<strong>Use Selector Configuration:</strong> Applies a predefined set of selectors with named sections.<br/>'
            '<strong>Use Manual Selectors:</strong> Directly extracts content matching your CSS selectors.'
        )
    )
    
    selector_configuration = forms.ModelChoiceField(
        queryset=SelectorConfiguration.objects.all(),
        required=False,
        empty_label="Select a configuration",
        widget=forms.Select(attrs={'class': 'w-full', 'data-selector-type': 'config'}),
        help_text='Select a predefined configuration of selectors.'
    )
    
    class Meta:
        model = URLProcessingRequest
        fields = ['url', 'css_selectors']
        widgets = {
            'url': forms.URLInput(attrs={
                'class': 'w-full', 
                'placeholder': 'Enter a URL to process'
            }),
            'css_selectors': forms.TextInput(attrs={
                'class': 'w-full',
                'placeholder': 'E.g., #main-content, .product-specs, .specifications-table',
                'data-selector-type': 'manual'
            }),
        }
        help_texts = {
            'css_selectors': 'Enter CSS selectors to extract specific elements (comma-separated).'
        }
        
    def clean(self):
        """Validate the form data and ensure only one selector type is provided."""
        cleaned_data = super().clean()
        selector_choice = cleaned_data.get('selector_choice')
        selector_configuration = cleaned_data.get('selector_configuration')
        css_selectors = cleaned_data.get('css_selectors', '')
        
        # Validate based on selector choice
        if selector_choice == self.SELECTOR_CHOICE_CONFIG:
            # Configuration selected but no configuration chosen
            if not selector_configuration:
                self.add_error('selector_configuration', 'Please select a configuration or switch to manual selectors.')
            # Clear the css_selectors field to ensure it's not used
            cleaned_data['css_selectors'] = ''
        elif selector_choice == self.SELECTOR_CHOICE_MANUAL:
            # Manual selected but no selectors provided
            if not css_selectors:
                self.add_error('css_selectors', 'Please enter at least one CSS selector or switch to using a configuration.')
            # Clear the selector_configuration field to ensure it's not used
            cleaned_data['selector_configuration'] = None
        
        return cleaned_data
        
    def clean_url(self):
        """Validate the URL."""
        url = self.cleaned_data.get('url', '')
        if not url:
            raise forms.ValidationError("Please enter a valid URL.")
        
        # You could add additional validation here if needed
        # For example, check if the URL is reachable
        
        return url
    
    def clean_css_selectors(self):
        """Validate and process the CSS selectors."""
        selectors = self.cleaned_data.get('css_selectors', '')
        
        # If empty, return as is (we'll process the entire HTML)
        if not selectors:
            return selectors
            
        # Clean up selectors (remove extra spaces, ensure comma separation)
        cleaned_selectors = []
        for selector in selectors.split(','):
            selector = selector.strip()
            if selector:
                cleaned_selectors.append(selector)
                
        return ','.join(cleaned_selectors)


class BatchURLProcessingForm(forms.ModelForm):
    """Form for processing multiple URLs with AWS Bedrock."""
    
    SELECTOR_CHOICE_CONFIG = 'config'
    SELECTOR_CHOICE_MANUAL = 'manual'
    
    selector_choice = forms.ChoiceField(
        choices=[
            (SELECTOR_CHOICE_CONFIG, 'Use Selector Configuration'),
            (SELECTOR_CHOICE_MANUAL, 'Use Manual Selectors'),
        ],
        widget=forms.RadioSelect(),
        initial=SELECTOR_CHOICE_MANUAL,
        required=True,
        help_text=mark_safe(
            '<strong>Use Selector Configuration:</strong> Applies a predefined set of selectors with named sections.<br/>'
            '<strong>Use Manual Selectors:</strong> Directly extracts content matching your CSS selectors.'
        )
    )
    
    selector_configuration = forms.ModelChoiceField(
        queryset=SelectorConfiguration.objects.all(),
        required=False,
        empty_label="Select a configuration",
        widget=forms.Select(attrs={'class': 'w-full', 'data-selector-type': 'config'}),
        help_text='Select a predefined configuration of selectors.'
    )
    
    urls = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full',
            'rows': '10',
            'placeholder': 'Enter one URL per line'
        }),
        label="URLs to Process",
        help_text="Enter one URL per line. Each URL will be processed separately."
    )
    
    class Meta:
        model = BatchURLProcessingRequest
        fields = ['name', 'css_selectors']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full',
                'placeholder': 'Enter a name for this batch'
            }),
            'css_selectors': forms.TextInput(attrs={
                'class': 'w-full',
                'placeholder': 'E.g., #main-content, .product-specs, body > section:nth-child(9)',
                'data-selector-type': 'manual'
            }),
        }
        help_texts = {
            'css_selectors': 'Optional: Enter CSS selectors to extract specific elements (comma-separated). Leave empty to process the entire page.'
        }
    
    def clean(self):
        """Validate the form data and ensure only one selector type is provided."""
        cleaned_data = super().clean()
        selector_choice = cleaned_data.get('selector_choice')
        selector_configuration = cleaned_data.get('selector_configuration')
        css_selectors = cleaned_data.get('css_selectors', '')
        
        # Validate based on selector choice
        if selector_choice == self.SELECTOR_CHOICE_CONFIG:
            # Configuration selected but no configuration chosen
            if not selector_configuration:
                self.add_error('selector_configuration', 'Please select a configuration or switch to manual selectors.')
            # Clear the css_selectors field to ensure it's not used
            cleaned_data['css_selectors'] = ''
        elif selector_choice == self.SELECTOR_CHOICE_MANUAL:
            # We'll allow empty selectors for manual mode (will process whole page)
            # Clear the selector_configuration field to ensure it's not used
            cleaned_data['selector_configuration'] = None
        
        return cleaned_data
    
    def clean_urls(self):
        """Validate the list of URLs."""
        urls_text = self.cleaned_data.get('urls', '')
        if not urls_text.strip():
            raise forms.ValidationError("Please enter at least one URL.")
        
        # Split by newline and filter out empty lines
        urls = [url.strip() for url in urls_text.split('\n') if url.strip()]
        
        if not urls:
            raise forms.ValidationError("Please enter at least one URL.")
        
        # Basic URL validation
        invalid_urls = []
        for url in urls:
            try:
                # Use URLField's validation logic
                URLProcessingRequest._meta.get_field('url').run_validators(url)
            except forms.ValidationError:
                invalid_urls.append(url)
        
        if invalid_urls:
            raise forms.ValidationError(
                f"The following URLs are invalid: {', '.join(invalid_urls)}"
            )
        
        return urls 