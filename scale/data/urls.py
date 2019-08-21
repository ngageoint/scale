"""Defines the URLs for the RESTful dataset services"""
from __future__ import unicode_literals, absolute_import

from django.conf.urls import url

from data.views import DataSetView, DataSetValidationView, DataSetDetailsView, DataSetMembersView, DataSetMemberDetailsView

urlpatterns = [
    # DataSet views
    url(r'^datasets/$', DataSetView.as_view(), name='datasets_view'),
    url(r'^datasets/validation/$', DataSetValidationView.as_view(), name='dataset_validation_view'),
    url(r'^datasets/(?P<dataset_id>\d+)/$', DataSetDetailsView.as_view(), name='dataset_details_view'),
    url(r'^datasets/(?P<dataset_id>\d+)/members/$', DataSetMembersView.as_view(), name='dataset_members_view'),
    url(r'^datasets/members/(?P<dsm_id>\d+)/$', DataSetMemberDetailsView.as_view(), name='dataset_member_details_view')
]