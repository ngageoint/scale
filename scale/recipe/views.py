from __future__ import unicode_literals

import logging

import rest_framework.status as status
from django.db import transaction
from django.http.response import Http404
from recipe.deprecation import RecipeDefinitionSunset
from rest_framework.generics import GenericAPIView, ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView

import trigger.handler as trigger_handler
import util.rest as rest_util
from job.models import JobType
from recipe.configuration.data.exceptions import InvalidRecipeConnection
from recipe.configuration.definition.exceptions import InvalidDefinition
from recipe.exceptions import ReprocessError
from recipe.models import Recipe, RecipeInputFile, RecipeType
from recipe.serializers import (OldRecipeDetailsSerializer, RecipeDetailsSerializerV6,  
                                RecipeSerializerV5, RecipeSerializerV6,
                                RecipeTypeDetailsSerializerV5, RecipeTypeDetailsSerializerV6,
                                RecipeTypeSerializerV5, RecipeTypeSerializerV6)
from storage.models import ScaleFile
from storage.serializers import ScaleFileSerializerV5
from trigger.configuration.exceptions import InvalidTriggerRule, InvalidTriggerType
from util.rest import BadParameter


logger = logging.getLogger(__name__)


class RecipeTypesView(GenericAPIView):
    """This view is the endpoint for retrieving the list of all recipe types"""
    queryset = RecipeType.objects.all()

    def get_serializer_class(self):
        """Returns the appropriate serializer based off the requests version of the REST API. """

        if self.request.version == 'v6':
            return RecipeTypeSerializerV6
        else:
            return RecipeTypeSerializerV5

    def get(self, request):
        """Retrieves the list of all recipe types returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """
        started = rest_util.parse_timestamp(request, 'started', required=False)
        ended = rest_util.parse_timestamp(request, 'ended', required=False)
        rest_util.check_time_range(started, ended)

        order = rest_util.parse_string_list(request, 'order', ['name', 'version'])

        recipe_types = RecipeType.objects.get_recipe_types(started, ended, order)

        page = self.paginate_queryset(recipe_types)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def post(self, request):
        """Creates a new recipe type and returns a link to the detail URL

        :param request: the HTTP POST request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """
        name = rest_util.parse_string(request, 'name')
        version = rest_util.parse_string(request, 'version')
        title = rest_util.parse_string(request, 'title', default_value=name)
        description = rest_util.parse_string(request, 'description', required=False)
        definition_dict = rest_util.parse_dict(request, 'definition')

        # Check for optional trigger rule parameters
        trigger_rule_dict = rest_util.parse_dict(request, 'trigger_rule', required=False)
        if (('type' in trigger_rule_dict and 'configuration' not in trigger_rule_dict) or
                ('type' not in trigger_rule_dict and 'configuration' in trigger_rule_dict)):
            raise BadParameter('Trigger type and configuration are required together.')
        is_active = trigger_rule_dict['is_active'] if 'is_active' in trigger_rule_dict else True

        # Attempt to look up the trigger handler for the type
        rule_handler = None
        if trigger_rule_dict and 'type' in trigger_rule_dict:
            try:
                rule_handler = trigger_handler.get_trigger_rule_handler(trigger_rule_dict['type'])
            except InvalidTriggerType as ex:
                logger.exception('Invalid trigger type for new recipe type: %s', name)
                raise BadParameter(unicode(ex))

        try:
            with transaction.atomic():
                # Validate the recipe definition
                logger.info(definition_dict)
                recipe_def = RecipeDefinitionSunset.create(definition_dict)

                # Attempt to create the trigger rule
                trigger_rule = None
                if rule_handler and 'configuration' in trigger_rule_dict:
                    trigger_rule = rule_handler.create_trigger_rule(trigger_rule_dict['configuration'], name, is_active)

                # Create the recipe type
                recipe_type = RecipeType.objects.create_recipe_type(name, version, title, description, recipe_def,
                                                                    trigger_rule)
        except (InvalidDefinition, InvalidTriggerType, InvalidTriggerRule, InvalidRecipeConnection) as ex:
            logger.exception('Unable to create new recipe type: %s', name)
            raise BadParameter(unicode(ex))

        # Fetch the full recipe type with details
        try:
            recipe_type = RecipeType.objects.get_details(recipe_type.id)
        except RecipeType.DoesNotExist:
            raise Http404

        url = reverse('recipe_type_details_view', args=[recipe_type.id], request=request)
        if self.request.version == 'v6':
            serializer = RecipeTypeDetailsSerializerV6(recipe_type)
        else:
            serializer = RecipeTypeDetailsSerializerV5(recipe_type)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=dict(location=url))


class RecipeTypeDetailsView(GenericAPIView):
    """This view is the endpoint for retrieving details of a recipe type"""
    queryset = RecipeType.objects.all()
    
    def get_serializer_class(self):
        """Returns the appropriate serializer based off the requests version of the REST API. """

        if self.request.version == 'v6':
            return RecipeTypeDetailsSerializerV6
        else:
            return RecipeTypeDetailsSerializerV5

    def get(self, request, recipe_type_id):
        """Retrieves the details for a recipe type and return them in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param recipe_type_id: The id of the recipe type
        :type recipe_type_id: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """
        try:
            recipe_type = RecipeType.objects.get_details(recipe_type_id)
        except RecipeType.DoesNotExist:
            raise Http404

        # TODO: remove this check when REST API v5 is remmoved 
        if self.request.version != 'v6':
            for jt in recipe_type.job_types:
                if jt.is_seed_job_type():
                    jt.manifest = JobType.objects.convert_manifest_to_v5_interface(jt.manifest)

        serializer = self.get_serializer(recipe_type)
        return Response(serializer.data)

    def patch(self, request, recipe_type_id):
        """Edits an existing recipe type and returns the updated details

        :param request: the HTTP PATCH request
        :type request: :class:`rest_framework.request.Request`
        :param recipe_type_id: The ID for the recipe type.
        :type recipe_type_id: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """
        title = rest_util.parse_string(request, 'title', required=False)
        description = rest_util.parse_string(request, 'description', required=False)
        definition_dict = rest_util.parse_dict(request, 'definition', required=False)

        # Check for optional trigger rule parameters
        trigger_rule_dict = rest_util.parse_dict(request, 'trigger_rule', required=False)
        if (('type' in trigger_rule_dict and 'configuration' not in trigger_rule_dict) or
                ('type' not in trigger_rule_dict and 'configuration' in trigger_rule_dict)):
            raise BadParameter('Trigger type and configuration are required together.')
        is_active = trigger_rule_dict['is_active'] if 'is_active' in trigger_rule_dict else True
        remove_trigger_rule = rest_util.has_params(request, 'trigger_rule') and not trigger_rule_dict

        # Fetch the current recipe type model
        try:
            recipe_type = RecipeType.objects.select_related('trigger_rule').get(pk=recipe_type_id)
        except RecipeType.DoesNotExist:
            raise Http404

        # Attempt to look up the trigger handler for the type
        rule_handler = None
        if trigger_rule_dict and 'type' in trigger_rule_dict:
            try:
                rule_handler = trigger_handler.get_trigger_rule_handler(trigger_rule_dict['type'])
            except InvalidTriggerType as ex:
                logger.exception('Invalid trigger type for recipe type: %i', recipe_type_id)
                raise BadParameter(unicode(ex))

        try:
            with transaction.atomic():
                # Validate the recipe definition
                recipe_def = None
                if definition_dict:
                    recipe_def = RecipeDefinitionSunset.create(definition_dict)

                # Attempt to create the trigger rule
                trigger_rule = None
                if rule_handler and 'configuration' in trigger_rule_dict:
                    trigger_rule = rule_handler.create_trigger_rule(trigger_rule_dict['configuration'],
                                                                    recipe_type.name, is_active)

                # Update the active state separately if that is only given trigger field
                if not trigger_rule and recipe_type.trigger_rule and 'is_active' in trigger_rule_dict:
                    recipe_type.trigger_rule.is_active = is_active
                    recipe_type.trigger_rule.save()

                # Edit the recipe type
                RecipeType.objects.edit_recipe_type(recipe_type_id, title, description, recipe_def, trigger_rule,
                                                    remove_trigger_rule)
        except (InvalidDefinition, InvalidTriggerType, InvalidTriggerRule, InvalidRecipeConnection) as ex:
            logger.exception('Unable to update recipe type: %i', recipe_type_id)
            raise BadParameter(unicode(ex))

        # Fetch the full recipe type with details
        try:
            recipe_type = RecipeType.objects.get_details(recipe_type_id)
        except RecipeType.DoesNotExist:
            raise Http404

        serializer = self.get_serializer(recipe_type)
        return Response(serializer.data)


class RecipeTypesValidationView(APIView):
    """This view is the endpoint for validating a new recipe type before attempting to actually create it"""
    queryset = RecipeType.objects.all()

    def post(self, request):
        """Validates a new recipe type and returns any warnings discovered

        :param request: the HTTP POST request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """
        name = rest_util.parse_string(request, 'name')
        version = rest_util.parse_string(request, 'version')
        title = rest_util.parse_string(request, 'title', default_value=name)
        description = rest_util.parse_string(request, 'description', required=False)
        definition_dict = rest_util.parse_dict(request, 'definition')

        # Check for optional trigger rule parameters
        trigger_rule_dict = rest_util.parse_dict(request, 'trigger_rule', required=False)
        if (('type' in trigger_rule_dict and 'configuration' not in trigger_rule_dict) or
                ('type' not in trigger_rule_dict and 'configuration' in trigger_rule_dict)):
            raise BadParameter('Trigger type and configuration are required together.')

        # Attempt to look up the trigger handler for the type
        rule_handler = None
        if trigger_rule_dict and 'type' in trigger_rule_dict:
            try:
                rule_handler = trigger_handler.get_trigger_rule_handler(trigger_rule_dict['type'])
            except InvalidTriggerType as ex:
                logger.exception('Invalid trigger type for recipe validation: %s', name)
                raise BadParameter(unicode(ex))

        # Attempt to look up the trigger rule configuration
        trigger_config = None
        if rule_handler and 'configuration' in trigger_rule_dict:
            try:
                trigger_config = rule_handler.create_configuration(trigger_rule_dict['configuration'])
            except InvalidTriggerRule as ex:
                logger.exception('Invalid trigger rule configuration for recipe validation: %s', name)
                raise BadParameter(unicode(ex))

        # Validate the recipe definition
        try:
            recipe_def = RecipeDefinitionSunset.create(definition_dict)
            warnings = RecipeType.objects.validate_recipe_type(name, title, version, description, recipe_def,
                                                               trigger_config)
        except (InvalidDefinition, InvalidTriggerType, InvalidTriggerRule, InvalidRecipeConnection) as ex:
            logger.exception('Unable to validate new recipe type: %s', name)
            raise BadParameter(unicode(ex))

        results = [{'id': w.key, 'details': w.details} for w in warnings]
        return Response({'warnings': results})


class RecipesView(ListAPIView):
    """This view is the endpoint for retrieving the list of all recipes"""
    queryset = Recipe.objects.all()
    
    def get_serializer_class(self):
        """Returns the appropriate serializer based off the requests version of the REST API. """

        if self.request.version == 'v6':
            return RecipeSerializerV6
        else:
            return RecipeSerializerV5

    def list(self, request):
        """Retrieves the list of all recipes and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """
        started = rest_util.parse_timestamp(request, 'started', required=False)
        ended = rest_util.parse_timestamp(request, 'ended', required=False)
        rest_util.check_time_range(started, ended)

        type_ids = rest_util.parse_int_list(request, 'type_id', required=False)
        type_names = rest_util.parse_string_list(request, 'type_name', required=False)
        batch_ids = rest_util.parse_int_list(request, 'batch_id', required=False)
        include_superseded = rest_util.parse_bool(request, 'include_superseded', required=False)
        order = rest_util.parse_string_list(request, 'order', required=False)

        recipes = Recipe.objects.get_recipes(started=started, ended=ended, type_ids=type_ids, type_names=type_names,
                                             batch_ids=batch_ids, include_superseded=include_superseded, order=order)

        page = self.paginate_queryset(recipes)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class RecipeDetailsView(RetrieveAPIView):
    """This view is the endpoint for retrieving details of a recipe"""
    queryset = Recipe.objects.all()

    # TODO: remove this class and un-comment the serializer declaration when REST API v5 is removed
    # serializer_class = RecipeDetailsSerializer
    def get_serializer_class(self):
        """Returns the appropriate serializer based off the requests version of the REST API. """

        if self.request.version == 'v6':
            return RecipeDetailsSerializerV6
        else:
            return OldRecipeDetailsSerializer

    def retrieve(self, request, recipe_id):
        """Retrieves the details for a recipe and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param recipe_id: The id of the recipe
        :type recipe_id: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        try:
            # TODO: remove check when REST API v5 is removed
            if request.version == 'v6':
                recipe = Recipe.objects.get_details(recipe_id)
            else:
                recipe = Recipe.objects.get_details_v5(recipe_id)
        except Recipe.DoesNotExist:
            raise Http404

        serializer = self.get_serializer(recipe)
        return Response(serializer.data)


class RecipeInputFilesView(ListAPIView):
    """This is the endpoint for retrieving details about input files associated with a given recipe."""
    queryset = RecipeInputFile.objects.all()
    serializer_class = ScaleFileSerializerV5

    def get(self, request, recipe_id):
        """Retrieve detailed information about the input files for a recipe

        -*-*-
        parameters:
          - name: recipe_id
            in: path
            description: The ID of the recipe the file is associated with
            required: true
            example: 113
          - name: started
            in: query
            description: The start time of a start/end time range
            required: false
            example: 2016-01-01T00:00:00Z
          - name: ended
            in: query
            description: The end time of a start/end time range
            required: false
            example: 2016-01-02T00:00:00Z
          - name: time_field
            in: query
            description: 'The database time field to apply `started` and `ended` time filters
                          [Valid fields: `source`, `data`, `last_modified`]'
            required: false
            example: source
          - name: file_name
            in: query
            description: The name of a specific file in Scale
            required: false
            example: some_file_i_need_to_find.zip
          - name: recipe_input
            in: query
            description: The name of the input the file is passed to in a recipe
            required: false
            example: input_1
        responses:
          '200':
            description: A JSON list of files with metadata
        -*-*-

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param recipe_id: The ID for the recipe.
        :type recipe_id: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        started = rest_util.parse_timestamp(request, 'started', required=False)
        ended = rest_util.parse_timestamp(request, 'ended', required=False)
        rest_util.check_time_range(started, ended)
        time_field = rest_util.parse_string(request, 'time_field', required=False,
                                            accepted_values=ScaleFile.VALID_TIME_FIELDS)
        file_name = rest_util.parse_string(request, 'file_name', required=False)
        recipe_input = rest_util.parse_string(request, 'recipe_input', required=False)

        files = RecipeInputFile.objects.get_recipe_input_files(recipe_id, started=started, ended=ended,
                                                               time_field=time_field, file_name=file_name,
                                                               recipe_input=recipe_input)

        page = self.paginate_queryset(files)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class RecipeReprocessView(GenericAPIView):
    """This view is the endpoint for scheduling a reprocess of a recipe"""
    queryset = Recipe.objects.all()

    # TODO: remove this class and un-comment the serializer declaration when REST API v5 is removed
    # serializer_class = RecipeDetailsSerializer
    def get_serializer_class(self):
        """Returns the appropriate serializer based off the requests version of the REST API. """

        if self.request.version == 'v6':
            return RecipeDetailsSerializerV6
        else:
            return OldRecipeDetailsSerializer

    def post(self, request, recipe_id):
        """Schedules a recipe for reprocessing and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param recipe_id: The id of the recipe
        :type recipe_id: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        job_names = rest_util.parse_string_list(request, 'job_names', required=False)
        all_jobs = rest_util.parse_bool(request, 'all_jobs', required=False)
        priority = rest_util.parse_int(request, 'priority', required=False)

        try:
            handler = Recipe.objects.reprocess_recipe(recipe_id, job_names=job_names, all_jobs=all_jobs,
                                                      priority=priority)
        except Recipe.DoesNotExist:
            raise Http404
        except ReprocessError as err:
            raise BadParameter(unicode(err))

        try:
            # TODO: remove this check when REST API v5 is removed
            if request.version == 'v6':
                new_recipe = Recipe.objects.get_details(handler.recipe.id)
            else:
                new_recipe = Recipe.objects.get_details_v5(handler.recipe.id)
        except Recipe.DoesNotExist:
            raise Http404

        serializer = self.get_serializer(new_recipe)

        url = reverse('recipe_details_view', args=[new_recipe.id], request=request)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=dict(location=url))
