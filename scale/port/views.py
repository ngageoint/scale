'''Defines the views for the RESTful import/export services'''
from __future__ import unicode_literals

import json
import logging
import os

import django.utils.timezone as timezone
import rest_framework.status as status
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

import port.exporter as exporter
import port.importer as importer
import util.rest as rest_util
from port.schema import InvalidConfiguration
from util.rest import BadParameter

logger = logging.getLogger(__name__)


class DownloadRenderer(JSONRenderer):
    '''Renders a JSON response as a file download attachment instead of embedded content.'''

    def render(self, data, accepted_media_type=None, renderer_context=None):
        result = super(DownloadRenderer, self).render(data, accepted_media_type, renderer_context)

        file_name = 'scale-export_%s.json' % timezone.now().strftime('%Y-%m-%d_%H-%M-%S')
        disposition = 'attachment; filename=%s' % file_name

        response = renderer_context['response']
        response['Content-Disposition'] = disposition
        response['Content-Length'] = str(len(result))
        return result


class ConfigurationView(APIView):
    '''This view is the endpoint for importing/exporting job and recipe configuration.'''

    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def get(self, request):
        '''Exports the job and recipe configuration and returns it in JSON form.

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        '''

        # Filter and export recipe types
        recipe_type_ids = rest_util.parse_string_list(request, 'recipe_type_id', required=False)
        recipe_type_names = rest_util.parse_string_list(request, 'recipe_type_name', required=False)
        recipe_filter = recipe_type_ids or recipe_type_names
        recipe_types = exporter.get_recipe_types(recipe_type_ids, recipe_type_names)

        # Filter and export job types
        job_type_ids = rest_util.parse_string_list(request, 'job_type_id', required=False)
        job_type_names = rest_util.parse_string_list(request, 'job_type_name', required=False)
        job_type_categories = rest_util.parse_string_list(request, 'job_type_category', required=False)
        job_filter = job_type_ids or job_type_names or job_type_categories
        job_types = exporter.get_job_types(recipe_types if recipe_filter else None, job_type_ids, job_type_names,
                                           job_type_categories)

        # Filter and export errors
        error_ids = rest_util.parse_string_list(request, 'error_id', required=False)
        error_names = rest_util.parse_string_list(request, 'error_name', required=False)
        errors = exporter.get_errors(job_types if job_filter or recipe_filter else None, error_ids, error_names)

        # Includes are handled at the very end so that the cascaded filtering works as expected
        includes = rest_util.parse_string_list(
            request, 'include', default_value=['recipe_types', 'job_types', 'errors'], required=False,
            accepted_values=['recipe_types', 'job_types', 'errors']
        )
        recipe_types = recipe_types if 'recipe_types' in includes else None
        job_types = job_types if 'job_types' in includes else None
        errors = errors if 'errors' in includes else None

        export_config = exporter.export_config(recipe_types, job_types, errors)
        return Response(export_config.get_dict(), status=status.HTTP_200_OK)

    def post(self, request):
        '''Imports job and recipe configuration and updates the corresponding models.

        :param request: the HTTP POST request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        '''
        import_dict = rest_util.parse_dict(request, 'import')

        try:
            warnings = importer.import_config(import_dict)
        except InvalidConfiguration as ex:
            logger.exception('Unable to import configuration.')
            raise BadParameter(unicode(ex))

        results = [{'id': w.key, 'details': w.details} for w in warnings]
        return Response({'warnings': results}, status=status.HTTP_200_OK)


class ConfigurationDownloadView(ConfigurationView):
    '''This view is the endpoint for downloading an export of job and recipe configuration.'''

    renderer_classes = (DownloadRenderer,)


class ConfigurationUploadView(APIView):
    '''This view is the endpoint for uploading an import file of job and recipe configuration.'''

    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def post(self, request, *args, **kwargs):
        file_name = None
        file_content = None

        # Check whether AJAX or a standard encoded form was used
        if request.is_ajax():

            # File name must be provided by an HTTP header
            if 'HTTP_X_FILE_NAME' not in request.META:
                return Response('Missing HTTP header for file name.', status=status.HTTP_400_BAD_REQUEST)
            file_name = request.META['HTTP_X_FILE_NAME']
            file_content = request
        else:

            # File content must be already processed by the request
            if len(request.FILES) != 1:
                return Response('Missing embedded file content.', status=status.HTTP_400_BAD_REQUEST)
            file_handle = request.FILES.values()[0]
            file_name = file_handle.name
            file_content = file_handle

        # Make sure the file type is supported
        if not file_name or not file_content:
            return Response('Missing file attachment.', status=status.HTTP_400_BAD_REQUEST)
        if os.path.splitext(file_name)[1] not in ['.json']:
            return Response('Unsupported file type.', status=status.HTTP_400_BAD_REQUEST)

        # Attempt to parse the file content
        # TODO: Add buffer overflow protection
        import_dict = json.loads(file_content.read())

        # Attempt to apply the configuration
        try:
            warnings = importer.import_config(import_dict)
        except InvalidConfiguration as ex:
            logger.exception('Unable to import configuration.')
            raise BadParameter(unicode(ex))

        results = [{'id': w.key, 'details': w.details} for w in warnings]
        return Response({'warnings': results}, status=status.HTTP_200_OK)


class ConfigurationValidationView(APIView):
    '''This view is the endpoint for validation an exported job and recipe configuration.'''

    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def post(self, request):
        '''Validates job and recipe configuration to make sure it can be imported.

        :param request: the HTTP POST request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        '''
        import_dict = rest_util.parse_dict(request, 'import')

        try:
            warnings = importer.validate_config(import_dict)
        except InvalidConfiguration as ex:
            logger.exception('Unable to validate import configuration.')
            raise BadParameter(unicode(ex))

        results = [{'id': w.key, 'details': w.details} for w in warnings]
        return Response({'warnings': results}, status=status.HTTP_200_OK)
