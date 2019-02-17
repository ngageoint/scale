"""Combines all of the URLs for the Scale RESTful services"""

from django.conf.urls import include, url

import util.rest as rest_util

# Enable the admin applications
from django.contrib import admin
admin.autodiscover()

# Add all the applications that expose REST APIs
REST_API_APPS = [
    'accounts',
    'batch',
    'diagnostic',
    'error',
    'ingest',
    'job',
    'metrics',
    'node',
    'queue',
    'recipe',
    'scheduler',
    'storage',
]

# Generate URLs for all REST APIs with version prefix
urlpatterns = rest_util.get_versioned_urls(REST_API_APPS)

unversioned_urls = [
    # Map all the paths required by the admin applications
    url(r'^admin/', admin.site.urls),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]

# Add unversioned_urls to URL regex pattern matcher
urlpatterns.extend(unversioned_urls)
