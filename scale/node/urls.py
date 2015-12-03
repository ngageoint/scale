'''Defines the URLs for the RESTful node services'''
from django.conf.urls import patterns, url

import node.views as views

urlpatterns = patterns(
    '',

    url(r'^nodes/$', views.NodesView.as_view(), name=u'nodes_view'),
    url(r'^nodes/(\d+)/$', views.NodeDetailsView.as_view(), name=u'node_details_view'),
    url(r'^nodes/status/$', views.NodesStatusView.as_view(), name=u'nodes_status_view'),
)
