import logging

import django.core.urlresolvers as urlresolvers
import rest_framework.status as status
from django.http.response import Http404
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

import util.rest as rest_util
from recipe.models import Recipe, RecipeType
from recipe.configuration.definition.exceptions import InvalidDefinition
from recipe.configuration.definition.recipe_definition import RecipeDefinition
from recipe.serializers import (RecipeDetailsSerializer, RecipeListSerializer, RecipeTypeDetailsSerializer,
                                RecipeTypeListSerializer)
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
        started = rest_util.parse_timestamp(request, u'started', required=False)
        ended = rest_util.parse_timestamp(request, u'ended', required=False)
        rest_util.check_time_range(started, ended)

        order = rest_util.parse_string_list(request, u'order', [u'name', u'version'])

        recipe_types = RecipeType.objects.get_recipe_types(started, ended, order)

        page = rest_util.perform_paging(request, recipe_types)
        serializer = RecipeTypeListSerializer(page, context={u'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        '''Creates a new recipe type and returns a link to the detail URL

        :param request: the HTTP POST request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        '''
        name = rest_util.parse_string(request, u'name')
        version = rest_util.parse_string(request, u'version')
        title = rest_util.parse_string(request, u'title')
        description = rest_util.parse_string(request, u'description', '')
        definition = rest_util.parse_dict(request, u'definition')

        try:
            recipe_def = RecipeDefinition(definition)
            recipe_type = RecipeType.objects.create_recipe_type(name, version, title, description, recipe_def, None)
        except InvalidDefinition:
            logger.exception('Unable to create new recipe type: %s', name)
            raise BadParameter('Invalid recipe type definition')

        url = urlresolvers.reverse('recipe_type_details_view', args=[recipe_type.id])
        return Response({u'id': recipe_type.id}, status=status.HTTP_201_CREATED, headers=dict(location=url))


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
        name = rest_util.parse_string(request, u'name')
        version = rest_util.parse_string(request, u'version')
        description = rest_util.parse_string(request, u'description', '')
        definition = rest_util.parse_dict(request, u'definition')

        try:
            recipe_def = RecipeDefinition(definition)
            warnings = RecipeType.objects.validate_recipe_type(name, version, description, recipe_def)
        except InvalidDefinition as ex:
            logger.exception('Unable to validate new recipe type: %s', name)
            raise BadParameter(unicode(ex))

        results = [{'id': w.key, 'details': w.details} for w in warnings]
        return Response({u'warnings': results}, status=status.HTTP_200_OK)


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
        started = rest_util.parse_timestamp(request, u'started', required=False)
        ended = rest_util.parse_timestamp(request, u'ended', required=False)
        rest_util.check_time_range(started, ended)

        type_ids = rest_util.parse_int_list(request, u'type_id', required=False)
        type_names = rest_util.parse_string_list(request, u'type_name', required=False)
        order = rest_util.parse_string_list(request, u'order', required=False)

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
