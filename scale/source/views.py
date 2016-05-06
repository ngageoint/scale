"""Defines the views for the RESTful source services"""
from __future__ import unicode_literals

import logging

from django.http.response import Http404
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response

import util.rest as rest_util
from source.models import SourceFile
from source.serializers import SourceFileSerializer, SourceFileUpdateSerializer
from source.serializers_extra import SourceFileDetailsSerializer

logger = logging.getLogger(__name__)


class SourcesView(ListAPIView):
    """This view is the endpoint for retrieving source files."""
    queryset = SourceFile.objects.all()
    serializer_class = SourceFileSerializer

    def list(self, request):
        """Retrieves the source files for a given time range and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """
        started = rest_util.parse_timestamp(request, 'started', required=False)
        ended = rest_util.parse_timestamp(request, 'ended', required=False)
        rest_util.check_time_range(started, ended)

        is_parsed = rest_util.parse_bool(request, 'is_parsed', required=False)
        file_name = rest_util.parse_string(request, 'file_name', required=False)

        order = rest_util.parse_string_list(request, 'order', required=False)

        sources = SourceFile.objects.get_sources(started, ended, is_parsed, file_name, order)

        page = self.paginate_queryset(sources)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class SourceDetailsView(RetrieveAPIView):
    """This view is the endpoint for retrieving/updating details of a source file."""
    queryset = SourceFile.objects.all()
    serializer_class = SourceFileDetailsSerializer

    def retrieve(self, request, source_id=None, file_name=None):
        """Retrieves the details for a source file and return them in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param source_id: The id of the source
        :type source_id: int encoded as a string
        :param file_name: The name of the source
        :type file_name: string
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        # Support retrieving by file name in addition to the usual identifier
        if file_name:
            sources = SourceFile.objects.filter(file_name=file_name).values('id').order_by('-parsed')
            if not sources:
                raise Http404
            source_id = sources[0]['id']

        try:
            source = SourceFile.objects.get_details(source_id)
        except SourceFile.DoesNotExist:
            raise Http404

        serializer = self.get_serializer(source)
        return Response(serializer.data)


class SourceUpdatesView(ListAPIView):
    """This view is the endpoint for retrieving source file updates over a given time range."""
    queryset = SourceFile.objects.all()
    serializer_class = SourceFileUpdateSerializer

    def list(self, request):
        """Retrieves the source file updates for a given time range and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """
        started = rest_util.parse_timestamp(request, 'started', required=False)
        ended = rest_util.parse_timestamp(request, 'ended', required=False)
        rest_util.check_time_range(started, ended)

        is_parsed = rest_util.parse_bool(request, 'is_parsed', required=False)
        file_name = rest_util.parse_string(request, 'file_name', required=False)

        order = rest_util.parse_string_list(request, 'order', required=False)

        sources = SourceFile.objects.get_sources(started, ended, is_parsed, file_name, order)

        page = self.paginate_queryset(sources)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)
