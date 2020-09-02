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
from ingest.models import Ingest, Strike
from recipe.models import RecipeType
from job.models import JobType
import json
from metrics.registry import MetricsPlotData, MetricsType, MetricsTypeGroup, MetricsTypeFilter
from django.db.models import F, Q, ExpressionWrapper, fields

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

        if request.version == 'v6':
            return self.list_v6(request)
        elif request.version == 'v7':
            return self.list_v6(request)

        raise Http404()

    def list_v6(self, request):
        """Gets v6 metrics types

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        return self.list_impl(request)

    def list_impl(self, request):
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
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        if request.version == 'v6':
            return self.retrieve_v6(request, name)
        elif request.version == 'v7':
            return self.retrieve_v6(request, name)

        raise Http404()

    def retrieve_v6(self, request, name):
        """Gets v6 metrics type details in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        return self.retrieve_impl(request, name)

    def retrieve_impl(self, request, name):
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
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        if request.version == 'v6':
            return self.list_v6(request, name)
        elif request.version == 'v7':
            return self.list_v6(request, name)

        raise Http404()

    def list_v6(self, request, name):
        """Gets v6 plot values for metrics in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        return self.list_impl(request, name)

    def list_impl(self, request, name):
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


class MetricAvgRuntimeView(ListAPIView):
    """This view is the endpoint for retrieving plot values of metrics."""
    queryset = []

    def list(self, request, name):
        """Retrieves the plot values for metrics and return them in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        if request.version == 'v6':
            return self.list_v6(request, name)
        elif request.version == 'v7':
            return self.list_v6(request, name)

        raise Http404()

    def list_v6(self, request, name):
        """Gets v6 plot values for metrics in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        return self.list_impl(request, name)

    def list_impl(self, request, name):
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

        exp = F('run_time_avg') - F('job_time_avg')
        exp_wrapper = ExpressionWrapper(exp, output_field=fields.DurationField())

        # Get the actual plot values
        metrics_values = provider.get_plot_data(started, ended, choice_ids, columns, wrappers={
            "other_time_avg": exp_wrapper
        })

        page = self.paginate_queryset(metrics_values)
        serializer = MetricsPlotSerializer(page, many=True)

        return self.get_paginated_response(serializer.data)


class MetricFileIngestView(ListAPIView):
    """This view is the endpoint for retrieving plot values of metrics."""
    queryset = []

    def list(self, request, name):
        """Retrieves the plot values for metrics and return them in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        if request.version == 'v6':
            return self.list_v6(request, name)
        elif request.version == 'v7':
            return self.list_v6(request, name)

        raise Http404()

    def list_v6(self, request, name):
        """Gets v6 plot values for metrics in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        return self.list_impl(request, name)

    def list_impl(self, request, name):
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

        choice_ids = rest_util.parse_string_list(request, 'choice_id', required=True)
        column_names = rest_util.parse_string_list(request, 'column', required=False)
        group_names = rest_util.parse_string_list(request, 'group', required=False)

        job_type_id = choice_ids[0]

        jt = JobType.objects.get(id=job_type_id)
        recipes = set()

        for recipe in RecipeType.objects.all().iterator():
            nodes = recipe.definition.get("nodes", [])
            for node_data in nodes.values():
                node_type = node_data.get("node_type", {})
                job_type_name = node_type.get("job_type_name", None)

                if job_type_name and job_type_name == jt.name:
                    recipes.add(recipe.name)
    
        strikes = set()

        for strike in Strike.objects.all().iterator():
            recipe_name = strike.configuration["recipe"].get("name", None)
    
            if recipe_name in recipes:
                strikes.add(strike.id)

        exp = (F('ingest_ended') - F('ingest_started')) + (F('transfer_ended') - F('transfer_started'))
        exp_wrapper = ExpressionWrapper(exp, output_field=fields.DurationField())

        results = []
        ingests = Ingest.objects.all().filter(strike_id__in=strikes)

        if started:
            ingests = ingests.filter(created__gte=started)
        if ended:
            ingests = ingests.filter(created__lte=ended)

        ingests = ingests.annotate(duration=exp_wrapper)
        ingests = ingests.values('created', 'job_id', *column_names)

        try:
            provider = registry.get_provider(name)
            metrics_type = provider.get_metrics_type(include_choices=False)
        except MetricsTypeError:
            raise Http404

        # Build a unique set of column names from groups
        columns = metrics_type.get_column_set(column_names, group_names)

        page = self.paginate_queryset(MetricsPlotData.create(ingests, 'created', 'job_id', [job_type_id], columns))

        serializer = MetricsPlotSerializer(page, many=True)
        
        return self.get_paginated_response(serializer.data)


class MetricsGanttChartRecipeTypesView(ListAPIView):
    """This view is the endpoint for retrieving gantt chart values for recipe types"""
    queryset = []

    def list(self, request, name):
        """Retrieves the gantt chart values and return them in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        if request.version == 'v6':
            return self.list_v6(request, name)
        elif request.version == 'v7':
            return self.list_v6(request, name)

        raise Http404()

    def list_v6(self, request, name):
        """Gets v6 plot values for metrics in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        return self.list_impl(request, name)

    def list_impl(self, request, name):
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

        recipe_types = rest_util.parse_string_list(request, 'choice_id', required=False)
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