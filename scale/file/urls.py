"""Defines the URLs for the RESTful source services"""
from django.conf.urls import url

import file.views as views

urlpatterns = [
    url(r'^files/$', views.FilesView.as_view(), name='files_view'),
    url(r'^files/(?P<file_id>\d+)/$', views.FileDetailsView.as_view(), name='file_details_view'),
]
