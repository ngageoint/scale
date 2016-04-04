"""Defines the views for the RESTful metrics services"""
from __future__ import unicode_literals

import logging

from django.http.response import Http404
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response

import metrics.registry as registry
import util.rest as rest_util
from metrics.registry import MetricsTypeError
from metrics.serializers import (MetricsPlotSerializer, MetricsPlotMultiSerializer, MetricsTypeDetailsSerializer,
                                 MetricsTypeSerializer)

logger = logging.getLogger(__name__)


class MetricsView(ListAPIView):
    """This view is the endpoint for retrieving available types of metrics."""
    queryset = registry.get_metrics_types()
    serializer_class = MetricsTypeSerializer

    def list(self, request):
        """Retrieves the metrics types and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """
        metrics_types = registry.get_metrics_types()

        page = self.paginate_queryset(metrics_types)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class MetricDetailsView(RetrieveAPIView):
    """This view is the endpoint for retrieving details of metrics."""

    def retrieve(self, request, name):
        """Retrieves the details for metrics and return them in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param name: the name of the metrics detail to retrieve.
        :type name: string
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """
        try:
            metrics_type = registry.get_metrics_type(name, include_choices=True)
            serializer_class = registry.get_serializer(name) or MetricsTypeDetailsSerializer
        except MetricsTypeError:
            raise Http404

        return Response(serializer_class(metrics_type).data)


class MetricPlotView(ListAPIView):
    """This view is the endpoint for retrieving plot values of metrics."""
    queryset = []

    def list(self, request, name):
        """Retrieves the plot values for metrics and return them in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param name: the name of the metrics detail to retrieve.
        :type name: string
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """
        started = rest_util.parse_timestamp(request, 'started', required=False)
        ended = rest_util.parse_timestamp(request, 'ended', required=False)
        rest_util.check_time_range(started, ended)

        choice_ids = rest_util.parse_string_list(request, 'choice_id', required=False)
        column_names = rest_util.parse_string_list(request, 'column', required=False)
        group_names = rest_util.parse_string_list(request, 'group', required=False)

        try:
            provider = registry.get_provider(name)
            metrics_type = provider.get_metrics_type(include_choices=False)
        except MetricsTypeError:
            raise Http404

        # Build a unique set of column names from groups
        columns = metrics_type.get_column_set(column_names, group_names)

        # Get the actual plot values
        metrics_values = provider.get_plot_data(started, ended, choice_ids, columns)

        page = self.paginate_queryset(metrics_values)
        if len(choice_ids) > 1:
            serializer = MetricsPlotMultiSerializer(page, many=True)
        else:
            serializer = MetricsPlotSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)
