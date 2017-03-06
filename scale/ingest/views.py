"""Defines the views for the RESTful ingest and Strike services"""
from __future__ import unicode_literals

import datetime
import logging

import rest_framework.status as status
from django.http.response import Http404
from rest_framework.generics import GenericAPIView, ListAPIView, ListCreateAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView

import util.rest as rest_util
from ingest.models import Ingest, Scan, Strike
from ingest.serializers import (IngestDetailsSerializer, IngestSerializer, IngestStatusSerializer,
                                ScanSerializer, StrikeSerializer, ScanDetailsSerializer, StrikeDetailsSerializer)
from ingest.strike.configuration.exceptions import InvalidStrikeConfiguration
from ingest.strike.configuration.strike_configuration import StrikeConfiguration
from scan.configuration.exceptions import InvalidScanConfiguration
from util.rest import BadParameter

logger = logging.getLogger(__name__)


class IngestsView(ListAPIView):
    """This view is the endpoint for retrieving the list of all ingests."""
    queryset = Ingest.objects.all()
    serializer_class = IngestSerializer

    def list(self, request):
        """Retrieves the list of all ingests and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        started = rest_util.parse_timestamp(request, 'started', required=False)
        ended = rest_util.parse_timestamp(request, 'ended', required=False)
        rest_util.check_time_range(started, ended)

        ingest_statuses = rest_util.parse_string_list(request, 'status', required=False)
        strike_ids = rest_util.parse_int_list(request, 'strike_id', required=False)
        scan_ids = rest_util.parse_int_list(request, 'scan_id', required=False)
        file_name = rest_util.parse_string(request, 'file_name', required=False)
        order = rest_util.parse_string_list(request, 'order', required=False)

        ingests = Ingest.objects.get_ingests(started=started, ended=ended, 
                                             statuses=ingest_statuses,
                                             scan_ids=scan_ids,
                                             strike_ids=strike_ids,
                                             file_name=file_name,
                                             order=order)

        page = self.paginate_queryset(ingests)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class IngestDetailsView(RetrieveAPIView):
    """This view is the endpoint for retrieving/updating details of an ingest."""
    queryset = Ingest.objects.all()
    serializer_class = IngestDetailsSerializer

    def retrieve(self, request, ingest_id=None, file_name=None):
        """Retrieves the details for an ingest and return them in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param ingest_id: The id of the ingest
        :type ingest_id: int encoded as a str
        :param file_name: The name of the ingest
        :type file_name: string
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        # Support retrieving by file name in addition to the usual identifier
        if file_name:
            ingests = Ingest.objects.filter(file_name=file_name).values('id').order_by('-created')
            if not ingests:
                raise Http404
            ingest_id = ingests[0]['id']

        try:
            ingest = Ingest.objects.get_details(ingest_id)
        except Ingest.DoesNotExist:
            raise Http404

        serializer = self.get_serializer(ingest)
        return Response(serializer.data)


class IngestsStatusView(ListAPIView):
    """This view is the endpoint for retrieving summarized ingest status."""
    queryset = Ingest.objects.all()
    serializer_class = IngestStatusSerializer

    def list(self, request):
        """Retrieves the ingest status information and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        started = rest_util.parse_timestamp(request, 'started', rest_util.get_relative_days(7))
        ended = rest_util.parse_timestamp(request, 'ended', required=False)
        rest_util.check_time_range(started, ended, max_duration=datetime.timedelta(days=31))

        use_ingest_time = rest_util.parse_bool(request, 'use_ingest_time', default_value=False)

        ingests = Ingest.objects.get_status(started, ended, use_ingest_time)

        page = self.paginate_queryset(ingests)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class ScansProcessView(APIView):
    """This view is the endpoint for launching a scan execution to ingest"""
    queryset = Scan.objects.all()

    def post(self, request, scan_id=None):
        """Launches a scan to ingest from an existing scan model instance

        :param request: the HTTP POST request
        :type request: :class:`rest_framework.request.Request`
        :param scan_id: ID for Scan record to pull configuration from
        :type scan_id: int
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        ingest = rest_util.parse_bool(request, 'ingest', default_value=False)

        scan = Scan.objects.queue_scan(scan_id, dry_run=not ingest)

        scan_url = reverse('scans_details_view', args=[scan.id], request=request)
        return Response(status=status.HTTP_201_CREATED, headers=dict(location=scan_url))

class ScansView(ListCreateAPIView):
    """This view is the endpoint for retrieving the list of all Scan process."""
    queryset = Scan.objects.all()
    serializer_class = ScanSerializer

    def list(self, request):
        """Retrieves the list of all Scan process and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        started = rest_util.parse_timestamp(request, 'started', required=False)
        ended = rest_util.parse_timestamp(request, 'ended', required=False)
        rest_util.check_time_range(started, ended)

        names = rest_util.parse_string_list(request, 'name', required=False)
        order = rest_util.parse_string_list(request, 'order', required=False)

        scans = Scan.objects.get_scans(started, ended, names, order)

        page = self.paginate_queryset(scans)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def create(self, request):
        """Creates a new Scan process and returns a link to the detail URL

        :param request: the HTTP POST request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        name = rest_util.parse_string(request, 'name')
        title = rest_util.parse_string(request, 'title', required=False)
        description = rest_util.parse_string(request, 'description', required=False)
        configuration = rest_util.parse_dict(request, 'configuration')

        try:
            scan = Scan.objects.create_scan(name, title, description, configuration)
        except InvalidScanConfiguration as ex:
            raise BadParameter('Scan configuration invalid: %s' % unicode(ex))

        # Fetch the full scan process with details
        try:
            scan = Scan.objects.get_details(scan.id)
        except Scan.DoesNotExist:
            raise Http404

        serializer = ScanDetailsSerializer(scan)
        scan_url = reverse('scans_details_view', args=[scan.id], request=request)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=dict(location=scan_url))


class ScansDetailsView(GenericAPIView):
    """This view is the endpoint for retrieving/updating details of a Scan process."""
    queryset = Scan.objects.all()
    serializer_class = ScanDetailsSerializer

    def get(self, request, scan_id):
        """Retrieves the details for a Scan process and return them in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param scan_id: The ID of the Scan process
        :type scan_id: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """
        try:
            scan = Scan.objects.get_details(scan_id)
        except Scan.DoesNotExist:
            raise Http404

        serializer = self.get_serializer(scan)
        return Response(serializer.data)

    def patch(self, request, scan_id):
        """Edits an existing Scan process and returns the updated details

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param scan_id: The ID of the Scan process
        :type scan_id: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        title = rest_util.parse_string(request, 'title', required=False)
        description = rest_util.parse_string(request, 'description', required=False)
        configuration = rest_util.parse_dict(request, 'configuration', required=False)

        try:
            Scan.objects.edit_scan(scan_id, title, description, configuration)

            scan = Scan.objects.get_details(scan_id)
        except Scan.DoesNotExist:
            raise Http404
        except InvalidScanConfiguration as ex:
            logger.exception('Unable to edit Scan process: %s', scan_id)
            raise BadParameter(unicode(ex))

        serializer = self.get_serializer(scan)
        return Response(serializer.data)


class ScansValidationView(APIView):
    """This view is the endpoint for validating a new Scan process before attempting to actually create it"""
    queryset = Scan.objects.all()

    def post(self, request):
        """Validates a new Scan process and returns any warnings discovered

        :param request: the HTTP POST request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        name = rest_util.parse_string(request, 'name')
        configuration = rest_util.parse_dict(request, 'configuration')

        rest_util.parse_string(request, 'title', required=False)
        rest_util.parse_string(request, 'description', required=False)

        # Validate the Scan configuration
        try:
            config = ScanConfiguration(configuration)
            warnings = config.validate()
        except InvalidScanConfiguration as ex:
            logger.exception('Unable to validate new Scan process: %s', name)
            raise BadParameter(unicode(ex))

        results = [{'id': w.key, 'details': w.details} for w in warnings]
        return Response({'warnings': results})


class StrikesView(ListCreateAPIView):
    """This view is the endpoint for retrieving the list of all Strike process."""
    queryset = Strike.objects.all()
    serializer_class = StrikeSerializer

    def list(self, request):
        """Retrieves the list of all Strike process and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        started = rest_util.parse_timestamp(request, 'started', required=False)
        ended = rest_util.parse_timestamp(request, 'ended', required=False)
        rest_util.check_time_range(started, ended)

        names = rest_util.parse_string_list(request, 'name', required=False)
        order = rest_util.parse_string_list(request, 'order', required=False)

        strikes = Strike.objects.get_strikes(started, ended, names, order)

        page = self.paginate_queryset(strikes)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def create(self, request):
        """Creates a new Strike process and returns a link to the detail URL

        :param request: the HTTP POST request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        name = rest_util.parse_string(request, 'name')
        title = rest_util.parse_string(request, 'title', required=False)
        description = rest_util.parse_string(request, 'description', required=False)
        configuration = rest_util.parse_dict(request, 'configuration')

        try:
            strike = Strike.objects.create_strike(name, title, description, configuration)
        except InvalidStrikeConfiguration as ex:
            raise BadParameter('Strike configuration invalid: %s' % unicode(ex))

        # Fetch the full strike process with details
        try:
            strike = Strike.objects.get_details(strike.id)
        except Strike.DoesNotExist:
            raise Http404

        serializer = StrikeDetailsSerializer(strike)
        strike_url = reverse('strike_details_view', args=[strike.id], request=request)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=dict(location=strike_url))


class StrikeDetailsView(GenericAPIView):
    """This view is the endpoint for retrieving/updating details of a Strike process."""
    queryset = Strike.objects.all()
    serializer_class = StrikeDetailsSerializer

    def get(self, request, strike_id):
        """Retrieves the details for a Strike process and return them in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param strike_id: The ID of the Strike process
        :type strike_id: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """
        try:
            strike = Strike.objects.get_details(strike_id)
        except Strike.DoesNotExist:
            raise Http404

        serializer = self.get_serializer(strike)
        return Response(serializer.data)

    def patch(self, request, strike_id):
        """Edits an existing Strike process and returns the updated details

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param strike_id: The ID of the Strike process
        :type strike_id: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        title = rest_util.parse_string(request, 'title', required=False)
        description = rest_util.parse_string(request, 'description', required=False)
        configuration = rest_util.parse_dict(request, 'configuration', required=False)

        try:
            Strike.objects.edit_strike(strike_id, title, description, configuration)

            strike = Strike.objects.get_details(strike_id)
        except Strike.DoesNotExist:
            raise Http404
        except InvalidStrikeConfiguration as ex:
            logger.exception('Unable to edit Strike process: %s', strike_id)
            raise BadParameter(unicode(ex))

        serializer = self.get_serializer(strike)
        return Response(serializer.data)


class StrikesValidationView(APIView):
    """This view is the endpoint for validating a new Strike process before attempting to actually create it"""
    queryset = Strike.objects.all()

    def post(self, request):
        """Validates a new Strike process and returns any warnings discovered

        :param request: the HTTP POST request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        name = rest_util.parse_string(request, 'name')
        configuration = rest_util.parse_dict(request, 'configuration')

        rest_util.parse_string(request, 'title', required=False)
        rest_util.parse_string(request, 'description', required=False)

        # Validate the Strike configuration
        try:
            config = StrikeConfiguration(configuration)
            warnings = config.validate()
        except InvalidStrikeConfiguration as ex:
            logger.exception('Unable to validate new Strike process: %s', name)
            raise BadParameter(unicode(ex))

        results = [{'id': w.key, 'details': w.details} for w in warnings]
        return Response({'warnings': results})
