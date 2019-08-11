"""Defines the URLs for the RESTful dataset services"""
from __future__ import unicode_literals, absolute_import

from django.conf.urls import url

from dataset.views import DataSetView, DataSetValidationView, DataSetDetailsView, DataSetFilesView, DataSetMembersView, DataSetMemberDetailsView

urlpatterns = [
    # DataSet views
    url(r'^data-sets/$', DataSetView.as_view(), name='datasets_view'),
    url(r'^data-sets/validation/$', DataSetValidationView.as_view(), name='dataset_validation_view'),
    url(r'^data-sets/(?P<dataset_id>\d+)/$', DataSetDetailsView.as_view(), name='dataset_details_view'),
    url(r'^data-sets/(?P<dataset_id>\d+)/members/$', DataSetMembersView.as_view(), name='dataset_members_view'),
    url(r'^data-sets/members/(?P<dsm_id>\d+)/$', DataSetMemberDetailsView.as_view(), name='dataset_member_details_view')
]