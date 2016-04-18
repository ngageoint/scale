'''Defines the views for the RESTful ingest and Strike services'''
from __future__ import unicode_literals

import datetime
import logging

from django.http.response import Http404
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView

import util.rest as rest_util
from ingest.models import Ingest, Strike
from ingest.serializers import IngestDetailsSerializer, IngestSerializer, IngestStatusSerializer
from ingest.strike.configuration.exceptions import InvalidStrikeConfiguration
from util.rest import BadParameter

logger = logging.getLogger(__name__)


class IngestsView(ListAPIView):
    '''This view is the endpoint for retrieving the list of all ingests.'''
    queryset = Ingest.objects.all()
    serializer_class = IngestSerializer

    def list(self, request):
        '''Retrieves the list of all ingests and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        '''

        started = rest_util.parse_timestamp(request, 'started', required=False)
        ended = rest_util.parse_timestamp(request, 'ended', required=False)
        rest_util.check_time_range(started, ended)

        ingest_status = rest_util.parse_string(request, 'status', required=False)
        order = rest_util.parse_string_list(request, 'order', required=False)

        ingests = Ingest.objects.get_ingests(started, ended, ingest_status, order)

        page = self.paginate_queryset(ingests)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class IngestDetailsView(RetrieveAPIView):
    '''This view is the endpoint for retrieving/updating details of an ingest.'''
    queryset = Ingest.objects.all()
    serializer_class = IngestDetailsSerializer

    def retrieve(self, request, ingest_id):
        '''Retrieves the details for an ingest and return them in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param ingest_id: The id of the ingest
        :type ingest_id: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        '''
        try:
            ingest = Ingest.objects.get_details(ingest_id)
        except Ingest.DoesNotExist:
            raise Http404

        serializer = self.get_serializer(ingest)
        return Response(serializer.data)


class IngestsStatusView(ListAPIView):
    '''This view is the endpoint for retrieving summarized ingest status.'''
    queryset = Ingest.objects.all()
    serializer_class = IngestStatusSerializer

    def list(self, request):
        '''Retrieves the ingest status information and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        '''

        started = rest_util.parse_timestamp(request, 'started', rest_util.get_relative_days(7))
        ended = rest_util.parse_timestamp(request, 'ended', required=False)
        rest_util.check_time_range(started, ended, max_duration=datetime.timedelta(days=31))

        use_ingest_time = rest_util.parse_bool(request, 'use_ingest_time', default_value=False)

        ingests = Ingest.objects.get_status(started, ended, use_ingest_time)

        page = self.paginate_queryset(ingests)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class CreateStrikeView(APIView):
    '''This view is the endpoint for creating a new Strike process.'''
    parser_classes = (JSONParser,)

    def post(self, request):
        '''Creates a new Strike process and returns its ID in JSON form

        :param request: the HTTP POST request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        '''

        name = rest_util.parse_string(request, 'name')
        title = rest_util.parse_string(request, 'title', required=False)
        description = rest_util.parse_string(request, 'description', required=False)
        configuration = rest_util.parse_dict(request, 'configuration')

        try:
            strike = Strike.objects.create_strike_process(name, title, description, configuration)
        except InvalidStrikeConfiguration:
            raise BadParameter('Configuration failed to validate.')
        return Response({'strike_id': strike.id})
