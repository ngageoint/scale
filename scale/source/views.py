'''Defines the views for the RESTful source services'''
from __future__ import unicode_literals

import logging

import rest_framework.status as status
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

import util.rest as rest_util
from source.models import SourceFile
from source.serializers import SourceFileListSerializer, SourceFileUpdateListSerializer

logger = logging.getLogger(__name__)


class SourcesView(APIView):
    '''This view is the endpoint for retrieving source files.'''
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def get(self, request):
        '''Retrieves the source files for a given time range and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        '''
        started = rest_util.parse_timestamp(request, u'started', required=False)
        ended = rest_util.parse_timestamp(request, u'ended', required=False)
        rest_util.check_time_range(started, ended)

        is_parsed = rest_util.parse_bool(request, u'is_parsed', required=False)
        file_name = rest_util.parse_string(request, u'file_name', required=False)

        order = rest_util.parse_string_list(request, u'order', required=False)

        sources = SourceFile.objects.get_sources(started, ended, is_parsed, file_name, order)
        page = rest_util.perform_paging(request, sources)
        serializer = SourceFileListSerializer(page, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class SourceUpdatesView(APIView):
    '''This view is the endpoint for retrieving source file updates over a given time range.'''

    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def get(self, request):
        '''Retrieves the source file updates for a given time range and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        '''
        started = rest_util.parse_timestamp(request, u'started', required=False)
        ended = rest_util.parse_timestamp(request, u'ended', required=False)
        rest_util.check_time_range(started, ended)

        is_parsed = rest_util.parse_bool(request, u'is_parsed', required=False)
        file_name = rest_util.parse_string(request, u'file_name', required=False)

        order = rest_util.parse_string_list(request, u'order', required=False)

        sources = SourceFile.objects.get_sources(started, ended, is_parsed, file_name, order)
        page = rest_util.perform_paging(request, sources)
        serializer = SourceFileUpdateListSerializer(page, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
