"""Defines the URLs for the RESTful queue services"""
from django.conf.urls import url

import queue.views

urlpatterns = [
    url(r'^load/$', queue.views.JobLoadView.as_view(), name='load_view'),
    url(r'^queue/status/$', queue.views.QueueStatusView.as_view(), name='queue_status_view'),
]
