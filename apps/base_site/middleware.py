from django.shortcuts import redirect
from django.urls import resolve, reverse
from wagtail.models import Site

class AdminPageRedirectMiddleware:
    """
    Middleware to redirect the Wagtail admin pages explorer to show 
    children of the homepage by default.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        if request.path.endswith('/admin/pages/'):
            try:
                # Get the home page id
                site = Site.objects.get(is_default_site=True)
                home_page_id = site.root_page.id
                return redirect(reverse('wagtailadmin_explore', args=[home_page_id]))
            except Exception as e:
                # If something goes wrong, continue to the normal page
                pass
                
        # Continue processing the request normally
        response = self.get_response(request)
        return response 