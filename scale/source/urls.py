'''Defines the URLs for the RESTful product services'''
from django.conf.urls import patterns, url

import source.views

urlpatterns = patterns(
    '',
    url(r'^sources/updates/$', source.views.SourceUpdatesView.as_view(), name='source_updates_view'),
    url(r'^sources/$', source.views.SourcesView.as_view(), name='sources_view'),
)
