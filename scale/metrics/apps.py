"""Defines the application configuration for the scale metrics application"""
from __future__ import unicode_literals
from django.apps import AppConfig


class MetricsConfig(AppConfig):
    """Configuration for the metrics app"""
    name = 'metrics'
    label = 'metrics'
    verbose_name = 'Metrics collection'

    def ready(self):
        """Registers the metrics processors with the clock system."""
        import job.clock as clock
        import metrics.registry as registry
        from metrics.daily_metrics import DailyMetricsProcessor
        from metrics.models import MetricsError, MetricsIngest, MetricsJobType
        from metrics.serializers import (MetricsErrorDetailsSerializer, MetricsIngestDetailsSerializer,
                                         MetricsJobTypeDetailsSerializer)

        clock.register_processor('scale-daily-metrics', DailyMetricsProcessor)

        # TODO: Add the resource metrics processor back in once it is ported to the new clock system
        # clock.register_processor('scale-resource-metrics', ResourceMetricsProcessor)

        # Register metrics type providers
        registry.register_provider(MetricsError.objects, MetricsErrorDetailsSerializer)
        registry.register_provider(MetricsIngest.objects, MetricsIngestDetailsSerializer)
        registry.register_provider(MetricsJobType.objects, MetricsJobTypeDetailsSerializer)
