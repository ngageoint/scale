"""Defines the views for the RESTful batch services"""
from __future__ import unicode_literals

import logging

import rest_framework.status as status
from django.http.response import Http404
from rest_framework.generics import ListCreateAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView

import util.rest as rest_util
from batch.configuration.definition.batch_definition import BatchDefinition
from batch.configuration.definition.exceptions import InvalidDefinition
from batch.models import Batch
from batch.serializers import BatchDetailsSerializer, BatchSerializer
from recipe.models import RecipeType
from util.rest import BadParameter

logger = logging.getLogger(__name__)


class BatchesView(ListCreateAPIView):
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

    def create(self, request):
        """Creates a new batch and returns a link to the detail URL

        :param request: the HTTP POST request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """
        recipe_type_id = rest_util.parse_int(request, 'recipe_type_id')
        title = rest_util.parse_string(request, 'title', required=False)
        description = rest_util.parse_string(request, 'description', required=False)

        # Make sure the recipe type exists
        try:
            recipe_type = RecipeType.objects.get(pk=recipe_type_id)
        except RecipeType.DoesNotExist:
            raise BadParameter('Unknown recipe type: %i' % recipe_type_id)

        # Validate the batch definition
        definition_dict = rest_util.parse_dict(request, 'definition')
        definition = None
        try:
            if definition_dict:
                definition = BatchDefinition(definition_dict)
        except InvalidDefinition as ex:
            raise BadParameter('Batch definition invalid: %s' % unicode(ex))

        # Create the batch
        batch = Batch.objects.create_batch(recipe_type, definition, title=title, description=description)

        # Fetch the full batch with details
        try:
            batch = Batch.objects.get_details(batch.id)
        except Batch.DoesNotExist:
            raise Http404

        url = reverse('batch_details_view', args=[batch.id], request=request)
        serializer = BatchDetailsSerializer(batch)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=dict(location=url))


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


class BatchesValidationView(APIView):
    """This view is the endpoint for validating a new batch before attempting to actually create it"""
    queryset = Batch.objects.all()

    def post(self, request):
        """Validates a new batch and returns any warnings discovered

        :param request: the HTTP POST request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """
        recipe_type_id = rest_util.parse_int(request, 'recipe_type_id')

        # Make sure the recipe type exists
        try:
            recipe_type = RecipeType.objects.get(pk=recipe_type_id)
        except RecipeType.DoesNotExist:
            raise BadParameter('Unknown recipe type: %i' % recipe_type_id)

        # Validate the batch definition
        definition_dict = rest_util.parse_dict(request, 'definition')
        definition = None
        try:
            if definition_dict:
                definition = BatchDefinition(definition_dict)
        except InvalidDefinition as ex:
            raise BadParameter('Batch definition invalid: %s' % unicode(ex))

        # Get a rough estimate of how many recipes will be affected
        old_recipes = Batch.objects.get_matched_recipes(recipe_type, definition)

        return Response({
            'recipe_count': old_recipes.count(),
            'warnings': [],
        })
