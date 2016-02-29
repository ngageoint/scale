'''Combines all of the URLs for the Scale RESTful services'''
from django.conf.urls import patterns, include, url

# Enable the admin applications
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns(
    '',

    # Map all the paths required by the admin applications
    url(r'^admin/', include(admin.site.urls)),

    # Include RESTful API URLs
    url(r'', include('error.urls')),
    url(r'', include('ingest.urls')),
    url(r'', include('job.urls')),
    url(r'', include('metrics.urls')),
    url(r'', include('node.urls')),
    url(r'', include('port.urls')),
    url(r'', include('product.urls')),
    url(r'', include('queue.urls')),
    url(r'', include('recipe.urls')),
    url(r'', include('scheduler.urls')),
    url(r'', include('source.urls')),
    url(r'', include('storage.urls')),
)
