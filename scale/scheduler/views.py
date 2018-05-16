"""Scheduler Views"""
from __future__ import unicode_literals

import logging

import rest_framework.status as status
from django.conf import settings
from django.http.response import Http404
from django.utils.dateparse import parse_datetime
from django.utils.timezone import now
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from scheduler.models import Scheduler
from scheduler.serializers import SchedulerSerializerV5, SchedulerSerializerV6


logger = logging.getLogger(__name__)


class SchedulerView(GenericAPIView):
    """This view is the endpoint for viewing and modifying the scheduler"""
    queryset = Scheduler.objects.all()
    update_fields = ('is_paused', 'num_message_handlers', 'resource_level', 'system_logging_level')
    
    def get_serializer_class(self):
        """Returns the appropriate serializer based off the requests version of the REST API"""

        if self.request.version == 'v6':
            return SchedulerSerializerV6
        elif self.request.version == 'v5':
            return SchedulerSerializerV5
        elif self.request.version == 'v4':
            return SchedulerSerializerV5

    def get(self, request):
        """Gets scheduler information

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        if request.version == 'v4':
            return self.get_v4(request)
        elif request.version == 'v5':
            return self.get_v5(request)
        elif request.version == 'v6':
            return self.get_v6(request)

        raise Http404()

    def get_v4(self, request):
        """Gets v4 scheduler info

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
        
    def get_v5(self, request):
        """Gets v5 scheduler info

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

        if request.version == 'v4':
            return self.patch_v4(request)
        elif request.version == 'v5':
            return self.patch_v5(request)
        elif request.version == 'v6':
            return self.patch_v6(request)

        raise Http404()

    def patch_v4(self, request):
        """Modify v4 scheduler info with a subset of fields

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
        try:
            Scheduler.objects.update_scheduler(dict(request.data))
            scheduler = Scheduler.objects.get_master()
        except Scheduler.DoesNotExist:
            raise Http404

        serializer = self.get_serializer(scheduler)
        return Response(serializer.data)
        
    def patch_v5(self, request):
        """Modify v5 scheduler info with a subset of fields

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
        try:
            Scheduler.objects.update_scheduler(dict(request.data))
            scheduler = Scheduler.objects.get_master()
        except Scheduler.DoesNotExist:
            raise Http404

        serializer = self.get_serializer(scheduler)
        return Response(serializer.data)
        
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
        try:
            Scheduler.objects.update_scheduler(dict(request.data))
            scheduler = Scheduler.objects.get_master()
        except Scheduler.DoesNotExist:
            raise Http404

        serializer = self.get_serializer(scheduler)
        return Response(serializer.data)


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

        if request.version == 'v4':
            return self.get_v4(request)
        elif request.version == 'v5':
            return self.get_v5(request)
        elif request.version == 'v6':
            return self.get_v6(request)

        raise Http404()

    # TODO: remove when REST API v4 is removed
    def get_v4(self, request):
        """Gets high level status information

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        status = Scheduler.objects.get_status()
        return Response(status)
        
    def get_v5(self, request):
        """The v5 version to get high level status information

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        status_dict = Scheduler.objects.get_master().status

        if not status_dict:  # Empty dict from model initialization
            return Response(status=status.HTTP_204_NO_CONTENT)

        # If status dict has not been updated recently, assume scheduler is down
        status_timestamp = parse_datetime(status_dict['timestamp'])
        if (now() - status_timestamp).total_seconds() > StatusView.STATUS_FRESHNESS_THRESHOLD:
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status_dict)

    def get_v6(self, request):
        """The v6 version to get high level status information

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        status_dict = Scheduler.objects.get_master().status

        if not status_dict:  # Empty dict from model initialization
            return Response(status=status.HTTP_204_NO_CONTENT)

        # If status dict has not been updated recently, assume scheduler is down
        status_timestamp = parse_datetime(status_dict['timestamp'])
        if (now() - status_timestamp).total_seconds() > StatusView.STATUS_FRESHNESS_THRESHOLD:
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status_dict)


class VersionView(GenericAPIView):
    """This view is the endpoint for viewing version/build information"""

    def get(self, request):
        """Gets various version/build information

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        if request.version == 'v4':
            return self.get_v4(request)
        elif request.version == 'v5':
            return self.get_v5(request)
        elif request.version == 'v6':
            return self.get_v6(request)

        raise Http404()

    # TODO: remove when REST API v4 is removed
    def get_v4(self, request):
        """Gets various version/build information for a v4 request

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        version_info = {
            'version': getattr(settings, 'VERSION', 'snapshot'),
        }
        return Response(version_info)
        
    def get_v5(self, request):
        """Gets various version/build information for a v5 request

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        version_info = {
            'version': getattr(settings, 'VERSION', 'snapshot'),
        }
        return Response(version_info)

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