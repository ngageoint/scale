from __future__ import unicode_literals
import logging

import django.core.urlresolvers as urlresolvers
import rest_framework.status as status
from django.http.response import Http404
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

import util.rest as rest_util
from error.models import Error
from error.serializers import ErrorDetailsSerializer, ErrorListSerializer
from util.rest import BadParameter

logger = logging.getLogger(__name__)


class ErrorsView(APIView):
    '''This view is the endpoint for retrieving the list of all errors and creating a new error.'''
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def get(self, request):
        '''Retrieves the list of all errors and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        '''

        started = rest_util.parse_timestamp(request, 'started', required=False)
        ended = rest_util.parse_timestamp(request, 'ended', required=False)
        rest_util.check_time_range(started, ended)

        order = rest_util.parse_string_list(request, 'order', required=False)

        errors = Error.objects.get_errors(started, ended, order)

        page = rest_util.perform_paging(request, errors)
        serializer = ErrorListSerializer(page, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        '''Creates a new error and returns a link to the info URL

        :param request: the HTTP POST request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        '''

        name = rest_util.parse_string(request, 'name')
        title = rest_util.parse_string(request, 'title')
        description = rest_util.parse_string(request, 'description')
        category = rest_util.parse_string(request, 'category', accepted_values=[c for c, _ in Error.CATEGORIES])

        # Do not allow the creation of SYSTEM level errors
        if category == 'SYSTEM':
            raise BadParameter('System level errors cannot be created.')

        error = Error.objects.create_error(name, title, description, category)

        serializer = ErrorDetailsSerializer(error)
        error_url = urlresolvers.reverse('error_details_view', args=[error.id])
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=dict(location=error_url))


class ErrorDetailsView(APIView):
    '''This view is the endpoint for retrieving details of an error.'''
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def get(self, request, error_id):
        '''Retrieves the details for an error and return them in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param error_id: The id of the error
        :type error_id: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        '''
        try:
            error = Error.objects.get(pk=error_id)
        except Error.DoesNotExist:
            raise Http404

        serializer = ErrorDetailsSerializer(error)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, error_id):
        '''Edits an existing error and returns the updated model

        :param request: the HTTP PATCH request
        :type request: :class:`rest_framework.request.Request`
        :param error_id: The id of the error
        :type error_id: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        '''
        try:
            error = Error.objects.get(pk=error_id)
        except Error.DoesNotExist:
            raise Http404

        # Do not allow editing of SYSTEM level errors
        if error.category == 'SYSTEM':
            raise BadParameter('System level errors cannot be edited.')

        title = rest_util.parse_string(request, 'title', required=False)
        description = rest_util.parse_string(request, 'description', required=False)
        category = rest_util.parse_string(request, 'category', required=False,
                                          accepted_values=[c for c, _ in Error.CATEGORIES])

        # Do not allow editing of SYSTEM level errors
        if category == 'SYSTEM':
            raise BadParameter('Errors cannot be changed to system level.')

        error.title = title or error.title
        error.description = description or error.description
        error.category = category or error.category

        serializer = ErrorDetailsSerializer(error)
        return Response(serializer.data, status=status.HTTP_200_OK)
