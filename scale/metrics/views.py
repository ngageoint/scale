'''Defines the views for the RESTful metrics services'''
from __future__ import unicode_literals

import logging

import rest_framework.status as status
from django.http.response import Http404
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

import metrics.registry as registry
import util.rest as rest_util
from metrics.registry import MetricsTypeError
from metrics.serializers import (MetricsPlotListSerializer, MetricsPlotMultiListSerializer,
                                 MetricsTypeDetailsSerializer, MetricsTypeListSerializer)

logger = logging.getLogger(__name__)


class MetricsView(APIView):
    '''This view is the endpoint for retrieving available types of metrics.'''

    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def get(self, request):
        '''Retrieves the metrics types and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        '''
        metrics_types = registry.get_metrics_types()
        page = rest_util.perform_paging(request, metrics_types)
        serializer = MetricsTypeListSerializer(page, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class MetricDetailsView(APIView):
    '''This view is the endpoint for retrieving details of metrics.'''
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def get(self, request, name):
        '''Retrieves the details for metrics and return them in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        '''
        try:
            metrics_type = registry.get_metrics_type(name, include_choices=True)
            serializer_class = registry.get_serializer(name) or MetricsTypeDetailsSerializer
        except MetricsTypeError:
            raise Http404

        return Response(serializer_class(metrics_type).data, status=status.HTTP_200_OK)


class MetricPlotView(APIView):
    '''This view is the endpoint for retrieving plot values of metrics.'''
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def get(self, request, name):
        '''Retrieves the plot values for metrics and return them in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        '''
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

        page = rest_util.perform_paging(request, metrics_values)

        if len(choice_ids) > 1:
            serializer = MetricsPlotMultiListSerializer(page, context={'request': request})
        else:
            serializer = MetricsPlotListSerializer(page, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
