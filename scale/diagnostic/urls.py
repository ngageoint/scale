"""Defines the URLs for the RESTful diagnostic services"""
from django.conf.urls import url

import diagnostic.views

urlpatterns = [
    url(r'^diagnostics/job/hello/$', diagnostic.views.QueueScaleHelloView.as_view(), name='diagnostic_hello_job_view'),
]
