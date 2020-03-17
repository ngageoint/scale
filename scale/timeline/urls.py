"""Defines the URLs for the RESTful recipe services"""
from django.conf.urls import url

import timeline.views

# Gantt Chart urls
urlpatterns = [
    # Recipe type views
    url(r'^timeline/recipe-types/$', timeline.views.TimelineRecipeTypeView.as_view(), name='timeline_recipe_type_view'),
    url(r'^timeline/job-types/$', timeline.views.TimelineJobTypeView.as_view(), name='timeline_job_type_view'),
]
