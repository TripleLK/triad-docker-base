# myapp/views.py

import subprocess
from django.http import HttpResponseRedirect
from django.urls import reverse
from wagtail.admin import messages
from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def deploy_latest_code(request):
    # Run git pull
    try:
        result = subprocess.run(
            ['git', 'pull'],
            capture_output=True,
            text=True,
            check=True
        )
        messages.success(request, "Git pull successful: {}".format(result.stdout))
    except subprocess.CalledProcessError as e:
        messages.error(request, "Git pull failed: {}".format(e.stderr))
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('wagtailadmin_home')))

    # Trigger a server restart.
    # In a Docker scenario, this might simply be touching the WSGI file,
    # which can signal some servers to reload. Adjust as needed.
    try:
        subprocess.run(['touch', 'wsgi.py'], check=True)
        messages.success(request, "Server restart triggered.")
    except subprocess.CalledProcessError as e:
        messages.error(request, "Failed to trigger server restart: {}".format(e))
    
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('wagtailadmin_home')))
