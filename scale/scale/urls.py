"""Combines all of the URLs for the Scale RESTful services"""

import util.rest as rest_util

from django.conf import settings
from django.conf.urls import include, url
from rest_framework.authtoken import views
from django.contrib.auth import views as auth_views


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
    url(r'^api-token-auth/', views.obtain_auth_token),
    url(r'^auth/', include('social_django.urls', namespace='social')),
    url(r'^login/$', auth_views.login,
        {'template_name': 'accounts/login.html', 'extra_context':{'GEOAXIS_ENABLED': settings.GEOAXIS_ENABLED}},
        name='login'),
]

# Add unversioned_urls to URL regex pattern matcher
urlpatterns.extend(unversioned_urls)
