"""Defines the URLs for the RESTful batch services"""
from django.conf.urls import url

import batch.views as views

urlpatterns = [
    url(r'^batches/$', views.BatchesView.as_view(), name='batches_view'),
    url(r'^batches/(\d+)/$', views.BatchDetailsView.as_view(), name='batch_details_view'),
    url(r'^batches/validation/$', views.BatchesValidationView.as_view(), name='batches_validation_view'),
]
