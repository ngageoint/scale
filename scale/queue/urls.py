"""Defines the URLs for the RESTful queue services"""
from django.conf.urls import url

import queue.views

urlpatterns = [
    url(r'^load/$', queue.views.JobLoadView.as_view(), name='load_view'),
    url(r'^queue/new-job/$', queue.views.QueueNewJobView.as_view(), name='queue_new_job_view'),
    url(r'^queue/new-recipe/$', queue.views.QueueNewRecipeView.as_view(), name='queue_new_recipe_view'),
    url(r'^queue/requeue-jobs/$', queue.views.RequeueJobsView.as_view(), name='requeue_jobs_view_old'),
    url(r'^queue/status/$', queue.views.QueueStatusView.as_view(), name='queue_status_view'),
]
