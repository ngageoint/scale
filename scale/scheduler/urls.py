'''Defines the URLs for the RESTful node services'''
from django.conf.urls import patterns, url

import views

urlpatterns = patterns(
    '',
    url(r'^scheduler/$', views.SchedulerView.as_view(), name=u'scheduler_view'),
    url(r'^status/$', views.StatusView.as_view(), name=u'status_view'),
)
