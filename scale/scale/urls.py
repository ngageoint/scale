"""Combines all of the URLs for the Scale RESTful services"""

import util.rest as rest_util
from django.conf import settings
from django.conf.urls import include, url
from django.contrib.auth import views as auth_views
from rest_framework.authtoken import views


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
login_settings = \
    {
        'template_name': 'accounts/login.html',
        'extra_context':
            {
                'GEOAXIS_ENABLED': settings.GEOAXIS_ENABLED
            }
    }
unversioned_urls = [
    # Map all the various login endpoints to share our custom auth page
    # Our custom login view must appear FIRST to override subsequent login views
    url(r'^admin/login/', auth_views.login, login_settings),
    url(r'^api-auth/login/',auth_views.login, login_settings),
    url(r'^login/$', auth_views.login, login_settings),
    url(r'^admin/', admin.site.urls),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^api-token-auth/', views.obtain_auth_token),
    url(r'^social-auth/', include('social_django.urls', namespace='social')),
]

# Add unversioned_urls to URL regex pattern matcher
urlpatterns.extend(unversioned_urls)
