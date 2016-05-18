"""Defines the URLs for the RESTful ingest and Strike services"""
from django.conf.urls import patterns, url

import ingest.views as views

urlpatterns = patterns(
    '',

    # Ingest views
    url(r'^ingests/$', views.IngestsView.as_view(), name='ingests_view'),
    url(r'^ingests/status/$', views.IngestsStatusView.as_view(), name='ingests_status_view'),
    url(r'^ingests/(?P<ingest_id>\d+)/$', views.IngestDetailsView.as_view(), name='ingest_details_view'),
    url(r'^ingests/(?P<file_name>[\w.]{0,250})/$', views.IngestDetailsView.as_view(), name='ingest_details_view'),

    # Strike views
    url(r'^strikes/$', views.StrikesView.as_view(), name='strikes_view'),
    url(r'^strikes/(\d+)/$', views.StrikeDetailsView.as_view(), name='strike_details_view'),

    # TODO: Remove this once the UI migrates to POST /strikes/
    url(r'^strike/create/$', views.CreateStrikeView.as_view(), name='create_strike_view'),
)
