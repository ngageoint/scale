"""Defines the URLs for the RESTful node services"""
from __future__ import unicode_literals

from django.conf.urls import url

import views

urlpatterns = [
    url(r'^scheduler/$', views.SchedulerView.as_view(), name='scheduler_view'),
    url(r'^scheduler/queued-resources/$', views.QueuedResourcesView.as_view(), name='queued_resrouces_view'),
    url(r'^status/$', views.StatusView.as_view(), name='status_view'),
    url(r'^version/$', views.VersionView.as_view(), name='version_view'),
]
