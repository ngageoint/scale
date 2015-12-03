import logging

import django.core.urlresolvers as urlresolvers
import rest_framework.status as status
from django.http.response import Http404
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

import util.rest as rest_util
from error.models import Error, InvalidData
from error.serializers import ErrorDetailsSerializer, ErrorListSerializer

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

        started = rest_util.parse_timestamp(request, u'started', required=False)
        ended = rest_util.parse_timestamp(request, u'ended', required=False)
        rest_util.check_time_range(started, ended)

        order = rest_util.parse_string_list(request, u'order', required=False)

        errors = Error.objects.get_errors(started, ended, order)

        page = rest_util.perform_paging(request, errors)
        serializer = ErrorListSerializer(page, context={u'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        '''Creates a new error and returns a link to the info URL

        :param request: the HTTP POST request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        '''

        name = rest_util.parse_string(request, u'name')
        title = rest_util.parse_string(request, u'title')
        description = rest_util.parse_string(request, u'description')
        category = rest_util.parse_string(request, u'category')
        if category not in map(lambda x: x[1], Error.CATEGORIES):
            return Response(u'category is not valid', status=status.HTTP_400_BAD_REQUEST)

        try:
            error_id = Error.objects.create_error(name, title, description, category).id
        except InvalidData:
            return Response('Unable to create error.', status=status.HTTP_400_BAD_REQUEST)

        error_url = urlresolvers.reverse('error_details_view', args=[error_id])
        return Response({u'error_id': error_id}, status=status.HTTP_201_CREATED, headers=dict(location=error_url))


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
