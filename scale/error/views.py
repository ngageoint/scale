from __future__ import unicode_literals
import logging

import rest_framework.status as status
from django.http.response import Http404
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.reverse import reverse

import util.rest as rest_util
from error.models import Error
from error.serializers import ErrorDetailsSerializerV6, ErrorSerializerV6
from util.rest import BadParameter

logger = logging.getLogger(__name__)


class ErrorsView(GenericAPIView):
    """This view is the endpoint for retrieving the list of all errors and creating a new error."""
    queryset = Error.objects.all()

    serializer_class = ErrorSerializerV6

    def get(self, request):
        """Retrieves the list of all errors and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        if self.request.version == 'v6':
            return self._get_v6(request)
        elif self.request.version == 'v7':
            return self._get_v6(request)

        raise Http404

    def _get_v6(self, request):
        """Retrieves the list of all errors and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        started = rest_util.parse_timestamp(request, 'started', required=False)
        ended = rest_util.parse_timestamp(request, 'ended', required=False)
        rest_util.check_time_range(started, ended)
        is_builtin = rest_util.parse_bool(request, 'is_builtin', required=False)
        job_type_name = rest_util.parse_string(request, 'job_type_name', required=False)
        name = rest_util.parse_string(request, 'name', required=False)
        category = rest_util.parse_string(request, 'category', required=False)

        order = rest_util.parse_string_list(request, 'order', required=False)

        errors = Error.objects.get_errors(started=started, ended=ended, order=order, is_builtin=is_builtin,
                                          job_type_name=job_type_name, name=name, category=category)

        page = self.paginate_queryset(errors)
        serializer = self.serializer_class(page, many=True)
        return self.get_paginated_response(serializer.data)

    def post(self, request):
        """Creates a new error and returns a link to the info URL

        :param request: the HTTP POST request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        raise Http404


class ErrorDetailsView(GenericAPIView):
    """This view is the endpoint for retrieving details of an error."""
    queryset = Error.objects.all()

    serializer_class = ErrorDetailsSerializerV6

    def get(self, request, error_id):
        """Retrieves the details for an error and return them in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param error_id: The id of the error
        :type error_id: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        if self.request.version == 'v6':
            return self._get_v6(request, error_id)
        elif self.request.version == 'v7':
            return self._get_v6(request, error_id)

        raise Http404

    def _get_v6(self, request, error_id):
        """Retrieves the details for an error and return them in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param error_id: The id of the error
        :type error_id: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        try:
            error = Error.objects.get(pk=error_id)
        except Error.DoesNotExist:
            raise Http404

        serializer = self.serializer_class(error)
        return Response(serializer.data)

    def patch(self, request, error_id):
        """Edits an existing error and returns the updated model
        :param request: the HTTP PATCH request
        :type request: :class:`rest_framework.request.Request`
        :param error_id: The id of the error
        :type error_id: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        raise Http404