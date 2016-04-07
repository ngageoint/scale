"""Combines all of the URLs for the Scale RESTful services"""

from django.conf.urls import patterns, include, url

import util.rest as rest_util

# Enable the admin applications
from django.contrib import admin
admin.autodiscover()

# Add all the applications that expose REST APIs
REST_API_APPS = [
    'error',
    'ingest',
    'job',
    'metrics',
    'node',
    'port',
    'product',
    'queue',
    'recipe',
    'scheduler',
    'source',
    'storage',
]

# Generate URLs for all REST APIs with version prefix
rest_urls = rest_util.get_versioned_urls(REST_API_APPS)

urlpatterns = patterns(
    '',

    # Map all the paths required by the admin applications
    url(r'^admin/', include(admin.site.urls)),

) + rest_urls
