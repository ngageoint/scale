"""Scheduler Views"""
import logging

import rest_framework.status as status
from django.http.response import Http404
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from scheduler.models import Scheduler
from scheduler.serializers import SchedulerSerializer


logger = logging.getLogger(__name__)


class SchedulerView(GenericAPIView):
    """This view is the endpoint for viewing and modifying the scheduler"""
    serializer_class = SchedulerSerializer
    update_fields = (u'is_paused', )

    def get(self, request):
        """Gets scheduler info

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

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """
        extra = filter(lambda x, y=self.update_fields: x not in y, request.data.keys())
        if len(extra) > 0:
            return Response(u'Unexpected fields: %s' % ', '.join(extra), status=status.HTTP_400_BAD_REQUEST)
        if len(request.data) == 0:
            return Response(u'No fields specified for update.', status=status.HTTP_400_BAD_REQUEST)
        try:
            Scheduler.objects.update_scheduler(dict(request.data))
            scheduler = Scheduler.objects.get_master()
        except Scheduler.DoesNotExist:
            raise Http404

        serializer = self.get_serializer(scheduler)
        return Response(serializer.data, status=status.HTTP_201_CREATED,
                        headers={'Location': request.build_absolute_uri()})


class StatusView(GenericAPIView):
    """This view is the endpoint for viewing overall system information"""

    def get(self, request):
        """Gets high level status information

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """
        status = Scheduler.objects.get_status()
        return Response(status)
