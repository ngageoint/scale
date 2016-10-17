"""Defines the views for the RESTful batch services"""
from __future__ import unicode_literals

import logging

from django.http.response import Http404
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response

import util.rest as rest_util
from batch.models import Batch
from batch.serializers import BatchDetailsSerializer, BatchSerializer

logger = logging.getLogger(__name__)


class BatchesView(ListAPIView):
    """This view is the endpoint for retrieving existing batches."""
    queryset = Batch.objects.all()
    serializer_class = BatchSerializer

    def list(self, request):
        """Retrieves the batches and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        started = rest_util.parse_timestamp(request, 'started', required=False)
        ended = rest_util.parse_timestamp(request, 'ended', required=False)
        rest_util.check_time_range(started, ended)

        statuses = rest_util.parse_string_list(request, 'status', required=False)
        recipe_type_ids = rest_util.parse_int_list(request, 'recipe_type_id', required=False)
        recipe_type_names = rest_util.parse_string_list(request, 'recipe_type_name', required=False)
        order = rest_util.parse_string_list(request, 'order', required=False)

        batches = Batch.objects.get_batches(started=started, ended=ended, statuses=statuses,
                                            recipe_type_ids=recipe_type_ids, recipe_type_names=recipe_type_names,
                                            order=order)

        page = self.paginate_queryset(batches)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class BatchDetailsView(RetrieveAPIView):
    """This view is the endpoint for viewing batch detail"""
    queryset = Batch.objects.all()
    serializer_class = BatchDetailsSerializer

    def retrieve(self, request, batch_id):
        """Retrieves the details for a batch and return them in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param batch_id: the batch id
        :type batch_id: int
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """
        try:
            batch = Batch.objects.get_details(batch_id)
        except Batch.DoesNotExist:
            raise Http404

        serializer = self.get_serializer(batch)
        return Response(serializer.data)
