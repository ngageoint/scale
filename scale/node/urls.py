"""Defines the URLs for the RESTful node services"""
from __future__ import unicode_literals

from django.conf.urls import url

import node.views as views

urlpatterns = [
    url(r'^nodes/$', views.NodesView.as_view(), name='nodes_view'),
    url(r'^nodes/(\d+)/$', views.NodeDetailsView.as_view(), name='node_details_view'),
    url(r'^nodes/status/$', views.NodesStatusView.as_view(), name='nodes_status_view'),
]
