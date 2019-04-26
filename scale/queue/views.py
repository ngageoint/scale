"""Defines the views for the RESTful queue services"""
from __future__ import unicode_literals

import logging

import datetime
from rest_framework.generics import ListAPIView

import util.rest as rest_util
from queue.models import JobLoad, Queue
from queue.serializers import JobLoadGroupSerializer, QueueStatusSerializer, QueueStatusSerializerV6

logger = logging.getLogger(__name__)


class JobLoadView(ListAPIView):
    """This view is the endpoint for retrieving the job load for a given time range."""
    queryset = JobLoad.objects.all()
    serializer_class = JobLoadGroupSerializer

    def list(self, request):
        """Retrieves the job load for a given time range and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """
        started = rest_util.parse_timestamp(request, 'started', default_value=rest_util.get_relative_days(7))
        ended = rest_util.parse_timestamp(request, 'ended', required=False)
        rest_util.check_time_range(started, ended, max_duration=datetime.timedelta(days=31))

        job_type_ids = rest_util.parse_int_list(request, 'job_type_id', required=False)
        job_type_names = rest_util.parse_string_list(request, 'job_type_name', required=False)

        job_loads = JobLoad.objects.get_job_loads(started, ended, job_type_ids, job_type_names)
        job_loads_grouped = JobLoad.objects.group_by_time(job_loads)

        page = self.paginate_queryset(job_loads_grouped)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class QueueStatusView(ListAPIView):
    """This view is the endpoint for retrieving the queue status."""
    queryset = Queue.objects.all()

    def get_serializer_class(self):
        """Returns the appropriate serializer based off the requests version of the REST API. """

        if self.request.version == 'v6':
            return QueueStatusSerializerV6

    def list(self, request):
        """Retrieves the current status of the queue and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """
        queue_statuses = Queue.objects.get_queue_status()

        page = self.paginate_queryset(queue_statuses)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)
