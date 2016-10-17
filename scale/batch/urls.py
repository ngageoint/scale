"""Defines the URLs for the RESTful batch services"""
from django.conf.urls import patterns, url

import batch.views as views

urlpatterns = patterns(
    '',

    url(r'^batches/$', views.BatchesView.as_view(), name='batches_view'),
    url(r'^batches/(\d+)/$', views.BatchDetailsView.as_view(), name='batch_details_view'),
)
