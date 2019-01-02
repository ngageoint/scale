"""Defines the URLs for the RESTful dataset services"""
from __future__ import unicode_literals

from django.conf.urls import url
import datasets.views as views

urlpatterns = [
    # DataSet views
    url(r'^datasets/$',views.DataSetsView.as_view(), name='data_sets_view'),
    url(r'^datasets/(?P<data_set_id>\d+)/$', views.DataSetsIDDetailsView.as_view(), name='data_set_id_details_view'),
]