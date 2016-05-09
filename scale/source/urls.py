"""Defines the URLs for the RESTful source services"""
from django.conf.urls import patterns, url

import source.views as views

urlpatterns = patterns(
    '',
    url(r'^sources/$', views.SourcesView.as_view(), name='sources_view'),
    url(r'^sources/updates/$', views.SourceUpdatesView.as_view(), name='source_updates_view'),
    url(r'^sources/(?P<source_id>\d+)/$', views.SourceDetailsView.as_view(), name='source_details_view'),
    url(r'^sources/(?P<file_name>[\w.]{0,250})/$', views.SourceDetailsView.as_view(), name='source_details_view'),
)
