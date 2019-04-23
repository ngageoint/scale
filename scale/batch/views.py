"""Defines the views for the RESTful batch services"""
from __future__ import unicode_literals

import logging

import rest_framework.status as status
from django.db import transaction
from django.http.response import Http404
from django.utils.timezone import now
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateAPIView
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView

from batch.configuration.exceptions import InvalidConfiguration
from batch.configuration.json.configuration_v6 import BatchConfigurationV6
from batch.definition.exceptions import InvalidDefinition
from batch.definition.json.definition_v6 import BatchDefinitionV6
from batch.messages.create_batch_recipes import create_batch_recipes_message
from batch.models import Batch
from batch.serializers import BatchDetailsSerializerV6, BatchSerializerV6
from messaging.manager import CommandMessageManager
from recipe.diff.json.diff_v6 import convert_recipe_diff_to_v6_json
from recipe.models import RecipeType
from recipe.serializers import RecipeTypeBaseSerializerV6, RecipeTypeRevisionBaseSerializerV6
from trigger.models import TriggerEvent
from util.rest import BadParameter
from util import rest as rest_util


logger = logging.getLogger(__name__)


class BatchesView(ListCreateAPIView):
    """This view is the endpoint for the list of batches"""
    queryset = Batch.objects.all()

    def get_serializer_class(self):
        """Returns the appropriate serializer based off the requests version of the REST API"""

        if self.request.version == 'v6':
            return BatchSerializerV6

    def list(self, request):
        """Retrieves the batches and returns them in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        if request.version == 'v6':
            return self._list_v6(request)

        raise Http404()

    def create(self, request):
        """Creates a new batch and returns a link to the detail URL

        :param request: the HTTP POST request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        if request.version == 'v6':
            return self._create_v6(request)

        raise Http404()

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
        is_superseded = rest_util.parse_bool(request, 'is_superseded', required=False)
        root_batch_ids = rest_util.parse_int_list(request, 'root_batch_id', required=False)
        order = rest_util.parse_string_list(request, 'order', required=False)

        batches = Batch.objects.get_batches_v6(started=started, ended=ended, recipe_type_ids=recipe_type_ids,
                                               is_creation_done=is_creation_done, is_superseded=is_superseded,
                                               root_batch_ids=root_batch_ids, order=order)

        page = self.paginate_queryset(batches)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def _create_v6(self, request):
        """The v6 version for creating batches

        :param request: the HTTP POST request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        title = rest_util.parse_string(request, 'title', required=False)
        description = rest_util.parse_string(request, 'description', required=False)
        recipe_type_id = rest_util.parse_int(request, 'recipe_type_id')
        definition_dict = rest_util.parse_dict(request, 'definition')
        configuration_dict = rest_util.parse_dict(request, 'configuration', required=False)

        # Make sure the recipe type exists
        try:
            recipe_type = RecipeType.objects.get(pk=recipe_type_id)
        except RecipeType.DoesNotExist:
            raise BadParameter('Unknown recipe type: %d' % recipe_type_id)

        # Validate and create the batch
        try:
            definition = BatchDefinitionV6(definition=definition_dict, do_validate=True).get_definition()
            configuration = BatchConfigurationV6(configuration=configuration_dict, do_validate=True).get_configuration()
            with transaction.atomic():
                event = TriggerEvent.objects.create_trigger_event('USER', None, {'user': 'Anonymous'}, now())
                batch = Batch.objects.create_batch_v6(title, description, recipe_type, event, definition,
                                                      configuration=configuration)
                CommandMessageManager().send_messages([create_batch_recipes_message(batch.id)])
        except InvalidDefinition as ex:
            raise BadParameter(unicode(ex))
        except InvalidConfiguration as ex:
            raise BadParameter(unicode(ex))

        # Fetch the full batch with details
        batch = Batch.objects.get_details_v6(batch.id)

        url = reverse('batch_details_view', args=[batch.id], request=request)
        serializer = BatchDetailsSerializerV6(batch)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers={'Location': url})


class BatchDetailsView(RetrieveUpdateAPIView):
    """This view is the endpoint for a specific batch"""
    queryset = Batch.objects.all()
    http_method_names = ['get', 'patch', 'head', 'options']

    def get_serializer_class(self):
        """Returns the appropriate serializer based off the requests version of the REST API"""

        if self.request.version == 'v6':
            return BatchDetailsSerializerV6

    def retrieve(self, request, batch_id):
        """Retrieves the details for a batch and returns them in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param batch_id: The batch ID
        :type batch_id: int
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        if request.version == 'v6':
            return self._retrieve_v6(batch_id)

        raise Http404()

    def update(self, request, batch_id, **kwargs):
        """Updates the given batch

        :param request: the HTTP PATCH request
        :type request: :class:`rest_framework.request.Request`
        :param batch_id: the batch id
        :type batch_id: int
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        if request.version == 'v6':
            return self._update_v6(request, batch_id)

        raise Http404()

    def _retrieve_v6(self, batch_id):
        """The v6 version for retrieving batch details

        :param batch_id: The batch ID
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

    def _update_v6(self, request, batch_id):
        """The v6 version for updating a batch

        :param request: the HTTP PATCH request
        :type request: :class:`rest_framework.request.Request`
        :param batch_id: the batch id
        :type batch_id: int
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        title = rest_util.parse_string(request, 'title', required=False)
        description = rest_util.parse_string(request, 'description', required=False)
        configuration_dict = rest_util.parse_dict(request, 'configuration', required=False)

        try:
            batch = Batch.objects.get(id=batch_id)
        except Batch.DoesNotExist:
            raise Http404()

        # Validate and create the batch
        try:
            configuration = None
            if configuration_dict:
                configuration_json = BatchConfigurationV6(configuration=configuration_dict, do_validate=True)
                configuration = configuration_json.get_configuration()
            Batch.objects.edit_batch_v6(batch, title=title, description=description, configuration=configuration)
        except InvalidConfiguration as ex:
            raise BadParameter('Batch configuration invalid: %s' % unicode(ex))

        return Response(status=status.HTTP_204_NO_CONTENT)


class BatchesComparisonView(APIView):
    """This view is the endpoint for comparing batches with the same root ID (in the same iterative chain)"""
    queryset = Batch.objects.all()

    def get(self, request, root_batch_id):
        """Validates a new batch

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param root_batch_id: The root batch ID
        :type root_batch_id: int
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        if request.version == 'v6':
            return self._get_v6(request, root_batch_id)

        raise Http404()

    def _get_v6(self, request, root_batch_id):
        """The v6 version for comparing batches

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param root_batch_id: The root batch ID
        :type root_batch_id: int
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        comparison_dict = Batch.objects.get_batch_comparison_v6(root_batch_id)
        return Response(comparison_dict)


class BatchesValidationView(APIView):
    """This view is the endpoint for validating a new batch before attempting to actually create it"""
    queryset = Batch.objects.all()

    def post(self, request):
        """Validates a new batch

        :param request: the HTTP POST request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        if request.version == 'v6':
            return self._post_v6(request)

        raise Http404()

    def _post_v6(self, request):
        """The v6 version for validating a new batch

        :param request: the HTTP POST request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        recipe_type_id = rest_util.parse_int(request, 'recipe_type_id')
        definition_dict = rest_util.parse_dict(request, 'definition')
        configuration_dict = rest_util.parse_dict(request, 'configuration', required=False)

        # Make sure the recipe type exists
        try:
            recipe_type = RecipeType.objects.get(pk=recipe_type_id)
        except RecipeType.DoesNotExist:
            raise BadParameter('Unknown recipe type: %d' % recipe_type_id)

        try:
            definition = BatchDefinitionV6(definition=definition_dict, do_validate=True).get_definition()
            configuration = BatchConfigurationV6(configuration=configuration_dict, do_validate=True).get_configuration()
        except InvalidDefinition as ex:
            raise BadParameter(unicode(ex))
        except InvalidConfiguration as ex:
            raise BadParameter(unicode(ex))

        # Validate the batch
        validation = Batch.objects.validate_batch_v6(recipe_type, definition, configuration=configuration)
        batch = validation.batch
        recipe_type_serializer = RecipeTypeBaseSerializerV6(batch.recipe_type)
        resp_dict = {'is_valid': validation.is_valid, 'errors': [e.to_dict() for e in validation.errors],
                     'warnings': [w.to_dict() for w in validation.warnings],
                     'recipes_estimated': definition.estimated_recipes, 'recipe_type': recipe_type_serializer.data}
        if batch.superseded_batch:
            recipe_type_rev_serializer = RecipeTypeRevisionBaseSerializerV6(batch.superseded_batch.recipe_type_rev)
            prev_batch_dict = {'recipe_type_rev': recipe_type_rev_serializer.data}
            resp_dict['prev_batch'] = prev_batch_dict
            if definition.prev_batch_diff:
                diff_v6 = convert_recipe_diff_to_v6_json(definition.prev_batch_diff)
                diff_dict = rest_util.strip_schema_version(diff_v6.get_dict())
                prev_batch_dict['diff'] = diff_dict
        return Response(resp_dict)
