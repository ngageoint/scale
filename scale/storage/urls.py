'''Defines the URLs for the RESTful storage services'''
from django.conf.urls import patterns, url

import storage.views as views

urlpatterns = patterns(
    '',
    url(r'^workspaces/$', views.WorkspacesView.as_view(), name='workspaces_view'),
    url(r'^workspaces/(\d+)/$', views.WorkspaceDetailsView.as_view(), name='workspace_details_view'),
)
