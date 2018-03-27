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
from batch.definition.exceptions import InvalidDefinition
from batch.definition.json.old.batch_definition import BatchDefinition as OldBatchDefinition
from batch.models import Batch
from batch.serializers import BatchDetailsSerializerV5, BatchDetailsSerializerV6, BatchSerializerV5, BatchSerializerV6
from recipe.models import RecipeType
from util.rest import BadParameter


logger = logging.getLogger(__name__)


class BatchesView(ListCreateAPIView):
    """This view is the endpoint for retrieving a list of batches"""
    queryset = Batch.objects.all()

    def get_serializer_class(self):
        """Returns the appropriate serializer based off the requests version of the REST API"""

        if self.request.version == 'v6':
            return BatchSerializerV6
        elif self.request.version == 'v5':
            return BatchSerializerV5
        elif self.request.version == 'v4':
            return BatchSerializerV5

    def list(self, request):
        """Retrieves the batches and returns them in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        if request.version == 'v6':
            return self._list_v6(request)
        elif request.version == 'v5':
            return self._list_v5(request)
        elif request.version == 'v4':
            return self._list_v5(request)

        raise Http404()

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
                definition = OldBatchDefinition(definition_dict)
                definition.validate(recipe_type)
        except InvalidDefinition as ex:
            raise BadParameter('Batch definition invalid: %s' % unicode(ex))

        # Create the batch
        batch = Batch.objects.create_batch_old(recipe_type, definition, title=title, description=description)

        # Fetch the full batch with details
        try:
            batch = Batch.objects.get_details_v5(batch.id)
        except Batch.DoesNotExist:
            raise Http404

        url = reverse('batch_details_view', args=[batch.id], request=request)
        serializer = BatchDetailsSerializerV5(batch)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=dict(location=url))

    def _list_v5(self, request):
        """The v5 version for retrieving batches

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

        batches = Batch.objects.get_batches_v5(started=started, ended=ended, statuses=statuses,
                                               recipe_type_ids=recipe_type_ids, recipe_type_names=recipe_type_names,
                                               order=order)

        page = self.paginate_queryset(batches)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def _list_v6(self, request):
        """The v6 version for retrieving batches

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        started = rest_util.parse_timestamp(request, 'started', required=False)
        ended = rest_util.parse_timestamp(request, 'ended', required=False)
        rest_util.check_time_range(started, ended)

        recipe_type_ids = rest_util.parse_int_list(request, 'recipe_type_id', required=False)
        is_creation_done = rest_util.parse_bool(request, 'is_creation_done', required=False)
        root_batch_ids = rest_util.parse_int_list(request, 'root_batch_id', required=False)
        order = rest_util.parse_string_list(request, 'order', required=False)

        batches = Batch.objects.get_batches_v6(started=started, ended=ended, recipe_type_ids=recipe_type_ids,
                                               is_creation_done=is_creation_done, root_batch_ids=root_batch_ids,
                                               order=order)

        page = self.paginate_queryset(batches)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class BatchDetailsView(RetrieveAPIView):
    """This view is the endpoint for retrieving a detailed batch"""
    queryset = Batch.objects.all()

    def get_serializer_class(self):
        """Returns the appropriate serializer based off the requests version of the REST API"""

        if self.request.version == 'v6':
            return BatchDetailsSerializerV6
        elif self.request.version == 'v5':
            return BatchDetailsSerializerV5
        elif self.request.version == 'v4':
            return BatchDetailsSerializerV5

    def retrieve(self, request, batch_id):
        """Retrieves the details for a batch and returns them in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param batch_id: the batch id
        :type batch_id: int
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        if request.version == 'v6':
            return self._retrieve_v6(batch_id)
        elif request.version == 'v5':
            return self._retrieve_v5(batch_id)
        elif request.version == 'v4':
            return self._retrieve_v5(batch_id)

        raise Http404()

    def _retrieve_v5(self, batch_id):
        """The v5 version for retrieving batch details

        :param batch_id: the batch id
        :type batch_id: int
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        try:
            batch = Batch.objects.get_details_v5(batch_id)
        except Batch.DoesNotExist:
            raise Http404()

        serializer = self.get_serializer(batch)
        return Response(serializer.data)

    def _retrieve_v6(self, batch_id):
        """The v6 version for retrieving batch details

        :param batch_id: the batch id
        :type batch_id: int
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        try:
            batch = Batch.objects.get_details_v6(batch_id)
        except Batch.DoesNotExist:
            raise Http404()

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
        warnings = []
        try:
            if definition_dict:
                definition = OldBatchDefinition(definition_dict)
                warnings = definition.validate(recipe_type)
        except InvalidDefinition as ex:
            raise BadParameter('Batch definition invalid: %s' % unicode(ex))

        # Get a rough estimate of how many recipes/files will be affected
        old_recipes = Batch.objects.get_matched_recipes(recipe_type, definition)
        old_files = Batch.objects.get_matched_files(recipe_type, definition)

        return Response({
            'recipe_count': old_recipes.count(),
            'file_count': old_files.count(),
            'warnings': warnings,
        })
