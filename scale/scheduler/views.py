"""Scheduler Views"""
from __future__ import unicode_literals

import logging

import rest_framework.status as status
from django.conf import settings
from django.core.exceptions import ValidationError
from django.http.response import Http404
from django.utils.dateparse import parse_datetime
from django.utils.timezone import now
from rest_framework import permissions
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from scheduler.models import Scheduler
from scheduler.serializers import SchedulerSerializerV6

from util.rest import ServiceUnavailable

logger = logging.getLogger(__name__)


class SchedulerView(GenericAPIView):
    """This view is the endpoint for viewing and modifying the scheduler"""
    queryset = Scheduler.objects.all()
    update_fields = ('is_paused', 'num_message_handlers', 'system_logging_level', 'queue_mode')

    def get_serializer_class(self):
        """Returns the appropriate serializer based off the requests version of the REST API"""

        if self.request.version == 'v6':
            return SchedulerSerializerV6
        elif self.request.version == 'v7':
            return SchedulerSerializerV6

    def get(self, request):
        """Gets scheduler information

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        if request.version == 'v6':
            return self.get_v6(request)
        elif request.version == 'v7':
            return self.get_v6(request)

        raise Http404()

    def get_v6(self, request):
        """Gets v6 scheduler info

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        try:
            scheduler = Scheduler.objects.get_master()
        except Scheduler.DoesNotExist:
            raise Http404

        serializer = self.get_serializer(scheduler)
        return Response(serializer.data)

    def patch(self, request):
        """Modify scheduler info with a subset of fields

        :param request: the HTTP PATCH request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        if request.version == 'v6':
            return self.patch_v6(request)
        elif request.version == 'v7':
            return self.patch_v6(request)

        raise Http404()

    def patch_v6(self, request):
        """Modify v6 scheduler info with a subset of fields

        :param request: the HTTP PATCH request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """
        extra = filter(lambda x, y=self.update_fields: x not in y, request.data.keys())
        if len(extra) > 0:
            return Response('Unexpected fields: %s' % ', '.join(extra), status=status.HTTP_400_BAD_REQUEST)
        if len(request.data) == 0:
            return Response('No fields specified for update.', status=status.HTTP_400_BAD_REQUEST)

        from queue.models import QUEUE_ORDER_FIFO, QUEUE_ORDER_LIFO
        if 'queue_mode' in request.data and request.data['queue_mode'].upper() not in [QUEUE_ORDER_FIFO, QUEUE_ORDER_LIFO]:
            msg = 'Unexpected value %s for queue_mode. Valid values are %s, %s' % (request.data['queue_mode'],
                                                                                   QUEUE_ORDER_FIFO, QUEUE_ORDER_LIFO)
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        try:
            Scheduler.objects.update_scheduler(dict(request.data))
        except Scheduler.DoesNotExist:
            raise Http404
        except ValidationError as e:
            return Response('Validation Error: %s' % str(e), status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_204_NO_CONTENT)


class StatusView(GenericAPIView):
    """This view is the endpoint for viewing overall system information"""

    # The scheduler is considered offline if its status JSON is older than this threshold
    STATUS_FRESHNESS_THRESHOLD = 12.0  # seconds

    def get(self, request):
        """Gets high level status information

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        if request.version == 'v6':
            return self.get_v6(request)
        elif request.version == 'v7':
            return self.get_v6(request)

        raise Http404()

    def get_v6(self, request):
        """The v6 version to get high level status information

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        status_dict = Scheduler.objects.get_master().status

        if not status_dict:  # Empty dict from model initialization
            raise ServiceUnavailable(unicode('Status is missing. Scheduler may be down.'))

        # If status dict has not been updated recently, assume scheduler is down or slow
        status_timestamp = parse_datetime(status_dict['timestamp'])
        if (now() - status_timestamp).total_seconds() > StatusView.STATUS_FRESHNESS_THRESHOLD:
            raise ServiceUnavailable(unicode('Status is over %d seconds old' % StatusView.STATUS_FRESHNESS_THRESHOLD))

        return Response(status_dict)


class VersionView(GenericAPIView):
    """This view is the endpoint for viewing version/build information"""
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        """Gets various version/build information

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        if request.version == 'v6':
            return self.get_v6(request)
        elif request.version == 'v7':
            return self.get_v6(request)

        raise Http404()

    def get_v6(self, request):
        """Gets various version/build information for a v6 request

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        version_info = {
            'version': getattr(settings, 'VERSION', 'snapshot'),
        }
        return Response(version_info)
