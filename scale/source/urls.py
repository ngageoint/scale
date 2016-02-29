'''Defines the URLs for the RESTful source services'''
from django.conf.urls import patterns, url

import source.views as views

urlpatterns = patterns(
    '',
    url(r'^sources/updates/$', views.SourceUpdatesView.as_view(), name='source_updates_view'),
    url(r'^sources/$', views.SourcesView.as_view(), name='sources_view'),
)
