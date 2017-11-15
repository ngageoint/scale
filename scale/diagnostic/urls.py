"""Defines the URLs for the RESTful diagnostic services"""
from django.conf.urls import url

import diagnostic.views

urlpatterns = [
    url(r'^diagnostics/job/bake/$', diagnostic.views.QueueScaleBakeView.as_view(), name='diagnostic_bake_job_view'),
    url(r'^diagnostics/job/hello/$', diagnostic.views.QueueScaleHelloView.as_view(), name='diagnostic_hello_job_view'),
    url(r'^diagnostics/job/roulette/$', diagnostic.views.QueueScaleRouletteView.as_view(),
        name='diagnostic_roulette_job_view'),
    url(r'^diagnostics/recipe/casino/$', diagnostic.views.QueueScaleCasinoView.as_view(),
        name='diagnostic_casino_recipe_view'),
]
