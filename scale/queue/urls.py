'''Defines the URLs for the RESTful queue services'''
from django.conf.urls import patterns, url

import queue.views

urlpatterns = patterns(
    '',
    # TODO: Remove this once the UI migrates to /load/
    url(r'queue/depth/$', queue.views.QueueDepthView.as_view(), name='queue_depth_view'),
    # TODO: Remove this once the UI migrates to /queue/requeue-jobs/
    url(r'queue/requeue-job/$', queue.views.RequeueExistingJobView.as_view(), name='requeue_existing_job_view'),

    url(r'^load/$', queue.views.JobLoadView.as_view(), name='load_view'),
    url(r'^queue/new-job/$', queue.views.QueueNewJobView.as_view(), name='queue_new_job_view'),
    url(r'^queue/new-recipe/$', queue.views.QueueNewRecipeView.as_view(), name='queue_new_recipe_view'),
    url(r'^queue/requeue-jobs/$', queue.views.RequeueJobsView.as_view(), name='requeue_jobs_view'),
    url(r'^queue/status/$', queue.views.QueueStatusView.as_view(), name='queue_status_view'),
)
