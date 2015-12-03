'''Defines the URLs for the RESTful ingest and Strike services'''
from django.conf.urls import patterns, url

import ingest.views as views

urlpatterns = patterns(
    '',

    # Ingest views
    url(r'^ingests/$', views.IngestsView.as_view(), name='ingests_view'),
    url(r'^ingests/(\d+)/$', views.IngestDetailsView.as_view(), name='ingest_details_view'),
    url(r'^ingests/status/$', views.IngestsStatusView.as_view(), name='ingests_status_view'),

    # Strike views
    url(r'^strike/create/$', views.CreateStrikeView.as_view(), name='create_strike_view'),
)
