"""Defines the URLs for the RESTful dataset services"""
from __future__ import unicode_literals, absolute_import

from django.conf.urls import url

from dataset.views import DataSetView, DataSetValidationView, DataSetDetailsView, DataSetFilesView

urlpatterns = [
    # DataSet views
    url(r'^data-sets/$', DataSetView.as_view(), name='datasets_view'),
    url(r'^data-sets/validation/$', DataSetValidationView.as_view(), name='dataset_validation_view'),
    url(r'^data-sets/(?P<dataset_id>\d+)/$', DataSetDetailsView.as_view(), name='dataset_id_details_view'),
    #url(r'^data-sets/(?P<dataset_id>\d+)/members/$', DataSetMembersView.as_view(), name='dataset_id_members_view'),
    url(r'^data-sets/(?P<dataset_id>\d+)/files/$', DataSetFilesView.as_view(), name='dataset__id_files_view'),
]