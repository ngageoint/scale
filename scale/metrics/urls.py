"""Defines the URLs for the RESTful metrics services"""
from django.conf.urls import url

import metrics.views

urlpatterns = [
    url(r'^metrics/$', metrics.views.MetricsView.as_view(), name='metrics_view'),
    url(r'^metrics/([\w-]+)/$', metrics.views.MetricDetailsView.as_view(), name='metric_details_view'),
    url(r'^metrics/([\w-]+)/plot-data/$', metrics.views.MetricPlotView.as_view(), name='metric_plot_view'),
    url(r'^metrics/([\w-]+)/avg-runtime/$', metrics.views.MetricAvgRuntimeView.as_view(), name='metric_avg_runtime'),
    url(r'^metrics/([\w-]+)/ingest-time/$', metrics.views.MetricFileIngestView.as_view(), name='metric_ingest_time'),
]
