'''Defines the URLs for the RESTful recipe services'''
from django.conf.urls import patterns, url

import error.views

urlpatterns = patterns(
    '',

    url(r'^errors/$', error.views.ErrorsView.as_view(), name='errors_view'),
    url(r'^errors/(\d+)/$', error.views.ErrorDetailsView.as_view(), name='error_details_view'),
)
