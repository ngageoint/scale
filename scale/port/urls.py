'''Defines the URLs for the RESTful import/export services'''
from django.conf.urls import patterns, url

import port.views

urlpatterns = patterns(
    '',

    url(r'^configuration/$', port.views.ConfigurationView.as_view(), name='configuration_view'),

    url(r'^configuration/download/$', port.views.ConfigurationDownloadView.as_view(),
        name='configuration_download_view'),
    url(r'^configuration/upload/$', port.views.ConfigurationUploadView.as_view(), name='configuration_upload_view'),

    url(r'^configuration/validation/$', port.views.ConfigurationValidationView.as_view(),
        name='configuration_validation_view'),
)
