'''Defines the URLs for the RESTful metrics services'''
from django.conf.urls import patterns, url

import metrics.views

urlpatterns = patterns(
    '',

    url(r'^metrics/$', metrics.views.MetricsView.as_view(), name='metrics_view'),
    url(r'^metrics/([\w-]+)/$', metrics.views.MetricDetailsView.as_view(), name='metric_details_view'),
    url(r'^metrics/([\w-]+)/plot-data/$', metrics.views.MetricPlotView.as_view(), name='metric_plot_view'),
)
