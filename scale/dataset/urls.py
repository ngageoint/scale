"""Defines the URLs for the RESTful dataset services"""
from __future__ import unicode_literals, absolute_import

from django.conf.urls import url

from dataset.views import DataSetView, DataSetValidationView, DataSetIDDetailsView, DataSetVersionsView, DataSetDetailsView

urlpatterns = [
    # DataSet views
    url(r'^datasets/$', DataSetView.as_view(), name='datasets_view'),
    url(r'^datasets/validation/$', DataSetValidationView.as_view(), name='dataset_validation_view'),
    url(r'^datasets/(?P<dataset_id>\d+)/$', DataSetIDDetailsView.as_view(), name='dataset_id_details_view'),
    url(r'^datasets/(?P<name>[\w-]+)/$', DataSetVersionsView.as_view(), name='dataset_versions_view'),
    url(r'^datasets/(?P<name>[\w-]+)/(?P<version>[\w.]+)/$', DataSetDetailsView.as_view(), name='dataset_details_view'),
    # url(r'^datasets/(?P<name>[\w-]+)/(?P<version>[\w.]+)/revisions/$', views.DataSetRevisionsView.as_view(), name='dataset_revisions_view'),
    # url(r'^datasets/(?P<name>[\w-]+)/(?P<version>[\w.]+)/revisions/(?P<revision_num>\d+)/$', views.DataSetRevisionDetailsView.as_view(), name='dataset_revision_details_view'),
]