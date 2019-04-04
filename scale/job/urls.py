"""Defines the URLs for the RESTful job services"""
from __future__ import unicode_literals

from django.conf.urls import url

import job.views as views

urlpatterns = [
    # Job type views
    url(r'^job-types/$', views.JobTypesView.as_view(), name='job_types_view'),
    url(r'^job-type-names/$', views.JobTypeNamesView.as_view(), name='job_type_names_view'),
    url(r'^job-types/validation/$', views.JobTypesValidationView.as_view(), name='job_types_validation_view'),
    url(r'^job-types/status/$', views.JobTypesStatusView.as_view(), name='job_types_status_view'),
    url(r'^job-types/pending/$', views.JobTypesPendingView.as_view(), name='job_types_pending_view'),
    url(r'^job-types/running/$', views.JobTypesRunningView.as_view(), name='job_types_running_view'),
    url(r'^job-types/system-failures/$', views.JobTypesSystemFailuresView.as_view(), name='job_types_system_failures_view'),
    url(r'^job-types/(?P<name>[\w-]+)/$', views.JobTypeVersionsView.as_view(), name='job_type_versions_view'),
    url(r'^job-types/(?P<name>[\w-]+)/(?P<version>[\w.]+)/$', views.JobTypeDetailsView.as_view(), name='job_type_details_view'),
    url(r'^job-types/(?P<name>[\w-]+)/(?P<version>[\w.]+)/revisions/$', views.JobTypeRevisionsView.as_view(), name='job_type_revisions_view'),
    url(r'^job-types/(?P<name>[\w-]+)/(?P<version>[\w.]+)/revisions/(?P<revision_num>\d+)/$', views.JobTypeRevisionDetailsView.as_view(), name='job_type_revision_details_view'),


    # Job views
    url(r'^jobs/$', views.JobsView.as_view(), name='jobs_view'),
    url(r'^jobs/cancel/$', views.CancelJobsView.as_view(), name='cancel_jobs_view'),
    url(r'^jobs/requeue/$', views.RequeueJobsView.as_view(), name='requeue_jobs_view'),
    url(r'^jobs/(\d+)/$', views.JobDetailsView.as_view(), name='job_details_view'),
    url(r'^jobs/(\d+)/executions/$', views.JobExecutionsView.as_view(), name=''),
    url(r'^jobs/(\d+)/executions/(\d+)/$', views.JobExecutionDetailsView.as_view(), name=''),
    url(r'^jobs/(\d+)/input_files/$', views.JobInputFilesView.as_view(), name='job_input_files_view'),

    # Job execution views
    url(r'^job-executions/$', views.JobExecutionsView.as_view(), name='job_executions_view'),
    url(r'^job-executions/(\d+)/$', views.JobExecutionDetailsView.as_view(), name='job_execution_details_view'),
    url(r'^job-executions/(\d+)/logs/(stdout|stderr|combined)/$', views.JobExecutionSpecificLogView.as_view(),
        name='job_execution_log_view'),
]
