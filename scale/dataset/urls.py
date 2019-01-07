"""Defines the URLs for the RESTful dataset services"""
from __future__ import unicode_literals

from django.conf.urls import url
import dataset.views as views

urlpatterns = [
    # DataSet views
    url(r'^datasets/$',views.DataSetView.as_view(), name='datasets_view'),
    url(r'^datasets/validation/$', views.DataSetValidationView.as_view(), name='dataset_validation_view'),
    url(r'^datasets/(?P<data_set_id>\d+)/$', views.DataSetIDDetailsView.as_view(), name='dataset_id_details_view'),
    url(r'^datasets/(?P<name>[\w-]+)/$', views.DataSetVersionsView.as_view(), name='dataset_versions_view'),
    url(r'^datasets/(?P<name>[\w-]+)/(?P<version>[\w.]+)/$', views.DataSetDetailsView.as_view(), name='dataset_details_view'),
    url(r'^datasets/(?P<name>[\w-]+)/(?P<version>[\w.]+)/revisions/$', views.DataSetRevisionsView.as_view(), name='dataset_revisions_view'),
    url(r'^datasets/(?P<name>[\w-]+)/(?P<version>[\w.]+)/revisions/(?P<revision_num>\d+)/$', views.DataSetRevisionDetailsView.as_view(), name='dataset_revision_details_view'),
]