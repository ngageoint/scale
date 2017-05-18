"""Defines the URLs for the RESTful job services"""
from __future__ import unicode_literals

from django.conf.urls import url

import job.views as views

urlpatterns = [
    # Job type views
    url(r'^job-types/$', views.JobTypesView.as_view(), name='job_types_view'),
    url(r'^job-types/(\d+)/$', views.JobTypeDetailsView.as_view(), name='job_type_details_view'),
    url(r'^job-types/validation/$', views.JobTypesValidationView.as_view(), name='job_types_validation_view'),
    url(r'^job-types/status/$', views.JobTypesStatusView.as_view(), name='job_types_status_view'),
    url(r'^job-types/pending/$', views.JobTypesPendingView.as_view(), name='job_types_pending_view'),
    url(r'^job-types/running/$', views.JobTypesRunningView.as_view(), name='job_types_running_view'),
    url(r'^job-types/system-failures/$', views.JobTypesSystemFailuresView.as_view(),
        name='job_types_system_failures_view'),

    # Job views
    url(r'^jobs/$', views.JobsView.as_view(), name='jobs_view'),
    url(r'^jobs/(\d+)/$', views.JobDetailsView.as_view(), name='job_details_view'),
    url(r'^jobs/updates/$', views.JobUpdatesView.as_view(), name='job_updates_view'),

    # Augment the jobs view with execution information
    url(r'^jobs/executions/$', views.JobsWithExecutionView.as_view(), name='jobs_with_execution_view'),

    # Job execution views
    url(r'^job-executions/$', views.JobExecutionsView.as_view(), name='job_executions_view'),
    url(r'^job-executions/(\d+)/$', views.JobExecutionDetailsView.as_view(), name='job_execution_details_view'),
    url(r'^job-executions/(\d+)/logs/(stdout|stderr|combined)/$', views.JobExecutionSpecificLogView.as_view(),
        name='job_execution_log_view'),
]
