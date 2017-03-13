"""Defines the URLs for the RESTful source services"""
from django.conf.urls import url

import source.views as views

urlpatterns = [
    url(r'^sources/$', views.SourcesView.as_view(), name='sources_view'),
    url(r'^sources/updates/$', views.SourceUpdatesView.as_view(), name='source_updates_view'),
    url(r'^sources/(?P<source_id>\d+)/$', views.SourceDetailsView.as_view(), name='source_details_view'),
    url(r'^sources/(?P<file_name>[\w.]{0,250})/$', views.SourceDetailsView.as_view(), name='source_details_view'),
    url(r'^sources/(?P<source_id>\d+)/ingests/$', views.SourceIngestsView.as_view(), name='source_ingests_view'),
    url(r'^sources/(?P<source_id>\d+)/jobs/$', views.SourceJobsView.as_view(), name='source_jobs_view'),
    url(r'^sources/(?P<source_id>\d+)/products/$', views.SourceProductsView.as_view(), name='source_products_view'),
]
