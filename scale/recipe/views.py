from __future__ import unicode_literals

import logging

import django.core.urlresolvers as urlresolvers
import rest_framework.status as status
from django.db import transaction
from django.http.response import Http404
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

import trigger.handler as trigger_handler
import util.rest as rest_util
from recipe.models import Recipe, RecipeType
from recipe.configuration.data.exceptions import InvalidRecipeConnection
from recipe.configuration.definition.exceptions import InvalidDefinition
from recipe.configuration.definition.recipe_definition import RecipeDefinition
from recipe.serializers import (RecipeDetailsSerializer, RecipeListSerializer, RecipeTypeDetailsSerializer,
                                RecipeTypeListSerializer)
from trigger.configuration.exceptions import InvalidTriggerRule, InvalidTriggerType
from util.rest import BadParameter


logger = logging.getLogger(__name__)


class RecipeTypesView(APIView):
    '''This view is the endpoint for retrieving the list of all recipe types
    '''
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def get(self, request):
        '''Retrieves the list of all recipe types returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        '''
        started = rest_util.parse_timestamp(request, 'started', required=False)
        ended = rest_util.parse_timestamp(request, 'ended', required=False)
        rest_util.check_time_range(started, ended)

        order = rest_util.parse_string_list(request, 'order', ['name', 'version'])

        recipe_types = RecipeType.objects.get_recipe_types(started, ended, order)

        page = rest_util.perform_paging(request, recipe_types)
        serializer = RecipeTypeListSerializer(page, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        '''Creates a new recipe type and returns a link to the detail URL

        :param request: the HTTP POST request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        '''
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
                recipe_def = RecipeDefinition(definition_dict)

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

        url = urlresolvers.reverse('recipe_type_details_view', args=[recipe_type.id])
        serializer = RecipeTypeDetailsSerializer(recipe_type)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=dict(location=url))


class RecipeTypeDetailsView(APIView):
    '''This view is the endpoint for retrieving details of a recipe type
    '''
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def get(self, request, recipe_type_id):
        '''Retrieves the details for a recipe type and return them in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param recipe_type_id: The id of the recipe type
        :type recipe_type_id: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        '''
        try:
            recipe_type = RecipeType.objects.get_details(recipe_type_id)
        except RecipeType.DoesNotExist:
            raise Http404

        serializer = RecipeTypeDetailsSerializer(recipe_type)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, recipe_type_id):
        '''Edits an existing recipe type and returns the updated details

        :param request: the HTTP PATCH request
        :type request: :class:`rest_framework.request.Request`
        :param recipe_type_id: The ID for the recipe type.
        :type recipe_type_id: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        '''
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
                    recipe_def = RecipeDefinition(definition_dict)

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

        serializer = RecipeTypeDetailsSerializer(recipe_type)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RecipeTypesValidationView(APIView):
    '''This view is the endpoint for validating a new recipe type before attempting to actually create it
    '''
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def post(self, request):
        '''Validates a new recipe type and returns any warnings discovered

        :param request: the HTTP POST request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        '''
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
            recipe_def = RecipeDefinition(definition_dict)
            warnings = RecipeType.objects.validate_recipe_type(name, title, version, description, recipe_def,
                                                               trigger_config)
        except (InvalidDefinition, InvalidTriggerType, InvalidTriggerRule, InvalidRecipeConnection) as ex:
            logger.exception('Unable to validate new recipe type: %s', name)
            raise BadParameter(unicode(ex))

        results = [{'id': w.key, 'details': w.details} for w in warnings]
        return Response({'warnings': results}, status=status.HTTP_200_OK)


class RecipesView(APIView):
    '''This view is the endpoint for retrieving the list of all recipes
    '''
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def get(self, request):
        '''Retrieves the list of all recipes and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        '''
        started = rest_util.parse_timestamp(request, 'started', required=False)
        ended = rest_util.parse_timestamp(request, 'ended', required=False)
        rest_util.check_time_range(started, ended)

        type_ids = rest_util.parse_int_list(request, 'type_id', required=False)
        type_names = rest_util.parse_string_list(request, 'type_name', required=False)
        order = rest_util.parse_string_list(request, 'order', required=False)

        recipes = Recipe.objects.get_recipes(started, ended, type_ids, type_names, order)

        page = rest_util.perform_paging(request, recipes)
        serializer = RecipeListSerializer(page, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class RecipeDetailsView(APIView):
    '''This view is the endpoint for retrieving details of a recipe
    '''
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def get(self, request, recipe_id):
        '''Retrieves the details for a recipe type and return them in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param id: The id of the recipe type
        :type id: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        '''
        try:
            recipe = Recipe.objects.get_details(recipe_id)
        except Recipe.DoesNotExist:
            raise Http404

        serializer = RecipeDetailsSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_200_OK)
