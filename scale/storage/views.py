"""Defines the views for the RESTful storage services"""
from __future__ import unicode_literals

import logging

import rest_framework.status as status
from django.http.response import Http404, HttpResponse
from django.utils.timezone import now
from rest_framework.generics import GenericAPIView, ListAPIView, ListCreateAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView

import util.rest as rest_util
from util.rest import BadParameter
from util.rest import title_to_name

from messaging.manager import CommandMessageManager
from source.messages.purge_source_file import create_purge_source_file_message
from storage.configuration.workspace_configuration import WorkspaceConfiguration
from storage.configuration.json.workspace_config_1_0 import WorkspaceConfigurationV1
from storage.configuration.json.workspace_config_v6 import WorkspaceConfigurationV6
from storage.configuration.exceptions import InvalidWorkspaceConfiguration
from storage.models import ScaleFile, Workspace
from storage.serializers import ScaleFileSerializerV5, ScaleFileSerializerV6, ScaleFileDetailsSerializerV6
from storage.serializers import (WorkspaceDetailsSerializerV5, WorkspaceSerializerV5, WorkspaceDetailsSerializerV6,
                                 WorkspaceSerializerV6)
from trigger.models import TriggerEvent


logger = logging.getLogger(__name__)


class FilesView(ListAPIView):
    """This view is the endpoint for retrieving source/product files"""
    queryset = ScaleFile.objects.all()
    
    def get_serializer_class(self):
        """Returns the appropriate serializer based off the requests version of the REST API"""
    
        if self.request.version == 'v6':
            return ScaleFileSerializerV6
        elif self.request.version == 'v5':
            return ScaleFileSerializerV5
        elif self.request.version == 'v4':
            return ScaleFileSerializerV5
        
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

    def _list_v5(self, request):
        """Retrieves a list of files based of filters and returns it in JSON form

        -*-*-
        parameters:
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
        responses:
          '200':
            description: A JSON list of files with metadata
        -*-*-

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        started = rest_util.parse_timestamp(request, 'started', required=False)
        ended = rest_util.parse_timestamp(request, 'ended', required=False)
        rest_util.check_time_range(started, ended)
        time_field = rest_util.parse_string(request, 'time_field', required=False,
                                            accepted_values=ScaleFile.VALID_TIME_FIELDS)
        file_name = rest_util.parse_string(request, 'file_name', required=False)

        files = ScaleFile.objects.filter_files_v5(started=started, ended=ended, time_field=time_field,
                                                  file_name=file_name)

        page = self.paginate_queryset(files)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def _list_v6(self, request):
        """Retrieves a list of files based on filters and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """
        data_started = rest_util.parse_timestamp(request, 'data_started', required=False)
        data_ended = rest_util.parse_timestamp(request, 'data_ended', required=False)
        rest_util.check_time_range(data_started, data_ended)

        source_started = rest_util.parse_timestamp(request, 'source_started', required=False)
        source_ended = rest_util.parse_timestamp(request, 'source_ended', required=False)
        rest_util.check_time_range(source_started, source_ended)

        source_sensor_classes = rest_util.parse_string_list(request, 'source_sensor_class', required=False)
        source_sensors = rest_util.parse_string_list(request, 'source_sensor', required=False)
        source_collections = rest_util.parse_string_list(request, 'source_collection', required=False)
        source_tasks = rest_util.parse_string_list(request, 'source_task', required=False)

        mod_started = rest_util.parse_timestamp(request, 'modified_started', required=False)
        mod_ended = rest_util.parse_timestamp(request, 'modified_ended', required=False)
        rest_util.check_time_range(mod_started, mod_ended)

        job_type_ids = rest_util.parse_int_list(request, 'job_type_id', required=False)
        job_type_names = rest_util.parse_string_list(request, 'job_type_name', required=False)
        job_ids = rest_util.parse_int_list(request, 'job_id', required=False)
        file_names = rest_util.parse_string_list(request, 'file_name', required=False)
        job_outputs = rest_util.parse_string_list(request, 'job_output', required=False)
        recipe_ids = rest_util.parse_int_list(request, 'recipe_id', required=False)
        recipe_type_ids = rest_util.parse_int_list(request, 'recipe_type_id', required=False)
        recipe_nodes = rest_util.parse_string_list(request, 'recipe_node', required=False)
        batch_ids = rest_util.parse_int_list(request, 'batch_id', required=False)

        order = rest_util.parse_string_list(request, 'order', required=False)

        files = ScaleFile.objects.filter_files(
            data_started=data_started, data_ended=data_ended,
            source_started=source_started, source_ended=source_ended,
            source_sensor_classes=source_sensor_classes, source_sensors=source_sensors,
            source_collections=source_collections, source_tasks=source_tasks,
            mod_started=mod_started, mod_ended=mod_ended, job_type_ids=job_type_ids,
            job_type_names=job_type_names, job_ids=job_ids,
            file_names=file_names, job_outputs=job_outputs, recipe_ids=recipe_ids,
            recipe_type_ids=recipe_type_ids, recipe_nodes=recipe_nodes, batch_ids=batch_ids,
            order=order,
        )

        page = self.paginate_queryset(files)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class FileDetailsView(RetrieveAPIView):
    """This view is the endpoint for retrieving details of a scale file."""
    queryset = ScaleFile.objects.all()
    serializer_class = ScaleFileDetailsSerializerV6

    def retrieve(self, request, file_id):
        """Determine api version and call specific method

        :param request: the HTTP POST request
        :type request: :class:`rest_framework.request.Request`
        :param file_id: The id of the file
        :type file_id: int encoded as a string
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        if request.version == 'v6':
            return self.retrieve_impl(request, file_id)

        raise Http404()

    def retrieve_impl(self, request, file_id):
        """Retrieves the details for a file and return them in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param file_id: The id of the file
        :type file_id: int encoded as a string
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        try:
            scale_file = ScaleFile.objects.get_details(file_id)
        except ScaleFile.DoesNotExist:
            raise Http404

        serializer = self.get_serializer(scale_file)
        return Response(serializer.data)


class PurgeSourceFileView(APIView):
    """This view is the endpoint for submitting a source file ID to be purged"""

    def post(self, request):
        """Kicks off the process of purging a given source file from Scale

        :param request: the HTTP POST request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        if self.request.version in ['v4', 'v5']:
            content = 'This endpoint is supported with REST API v6+'
            return Response(status=status.HTTP_400_BAD_REQUEST, content=content)

        file_id = rest_util.parse_dict(request, 'file_id')

        try:
            file_id = int(file_id)
        except ValueError:
            content = 'The given file_id is not valid: %i' % (file_id)
            return Response(status=status.HTTP_400_BAD_REQUEST, content=content)

        # Attempt to fetch the ScaleFile model
        try:
            source_file = ScaleFile.objects.get(id=file_id)
        except ScaleFile.DoesNotExist:
            content = 'No file record exists for the given file_id: %i' % (file_id)
            return Response(status=status.HTTP_400_BAD_REQUEST, content=content)

        # Inspect the file to ensure it will purge correctly
        if source_file.file_type != 'SOURCE':
            content = 'The given file_id does not correspond to a SOURCE file_type: %i' % (file_id)
            return Response(status=status.HTTP_400_BAD_REQUEST, content=content)

        event = TriggerEvent.objects.create_trigger_event('USER', None, {'user': 'Anonymous'}, now())
        CommandMessageManager().send_messages([create_purge_source_file_message(source_file_id=file_id,
                                                                                trigger_id=event.id)])

        return Response(status=status.HTTP_204_NO_CONTENT)

class WorkspacesView(ListCreateAPIView):
    """This view is the endpoint for retrieving the list of all workspaces."""
    queryset = Workspace.objects.all()

    def get_serializer_class(self):
        """Returns the appropriate serializer based off the requests version of the REST API"""

        if self.request.version == 'v6':
            return WorkspaceSerializerV6
        elif self.request.version == 'v5':
            return WorkspaceSerializerV5
        elif self.request.version == 'v4':
            return WorkspaceSerializerV5

    def list(self, request):
        """Retrieves the list of all workspaces and returns it in JSON form

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

    def _list_v5(self, request):
        """Retrieves the list of all workspaces and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        started = rest_util.parse_timestamp(request, 'started', required=False)
        ended = rest_util.parse_timestamp(request, 'ended', required=False)
        rest_util.check_time_range(started, ended)

        names = rest_util.parse_string_list(request, 'name', required=False)
        order = rest_util.parse_string_list(request, 'order', ['name'])

        workspaces = Workspace.objects.get_workspaces(started, ended, names, order)

        page = self.paginate_queryset(workspaces)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def _list_v6(self, request):
        """Retrieves the list of all workspaces and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        started = rest_util.parse_timestamp(request, 'started', required=False)
        ended = rest_util.parse_timestamp(request, 'ended', required=False)
        rest_util.check_time_range(started, ended)

        names = rest_util.parse_string_list(request, 'name', required=False)
        order = rest_util.parse_string_list(request, 'order', ['name'])

        workspaces = Workspace.objects.get_workspaces(started, ended, names, order)

        page = self.paginate_queryset(workspaces)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def create(self, request):
        """Creates a new Workspace and returns it in JSON form

        :param request: the HTTP POST request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        if request.version == 'v6':
            return self._create_v6(request)
        elif request.version == 'v5':
            return self._create_v5(request)
        elif request.version == 'v4':
            return self._create_v5(request)

        raise Http404()

    def _create_v5(self, request):
        """Creates a new Workspace and returns it in JSON form

        :param request: the HTTP POST request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        name = rest_util.parse_string(request, 'name')
        title = rest_util.parse_string(request, 'title', required=False)
        description = rest_util.parse_string(request, 'description', required=False)
        json_config = rest_util.parse_dict(request, 'json_config')
        base_url = rest_util.parse_string(request, 'base_url', required=False)
        is_active = rest_util.parse_bool(request, 'is_active', default_value=True, required=False)

        configuration = None
        if json_config:
            try:
                configuration = WorkspaceConfigurationV1(json_config, do_validate=True).get_configuration()
            except InvalidWorkspaceConfiguration as ex:
                message = 'Workspace configuration invalid'
                logger.exception(message)
                raise BadParameter('%s: %s' % (message, unicode(ex)))
      
        try:
            workspace = Workspace.objects.create_workspace(name, title, description, configuration, base_url, is_active)
        except InvalidWorkspaceConfiguration as ex:
            logger.exception('Unable to create new workspace: %s', name)
            raise BadParameter(unicode(ex))

        # Fetch the full workspace with details
        try:
            workspace = Workspace.objects.get_details(workspace.id)
        except Workspace.DoesNotExist:
            raise Http404

        serializer = WorkspaceDetailsSerializerV5(workspace)
        workspace_url = reverse('workspace_details_view', args=[workspace.id], request=request)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=dict(location=workspace_url))

    def _create_v6(self, request):
        """Creates a new Workspace and returns it in JSON form

        :param request: the HTTP POST request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        title = rest_util.parse_string(request, 'title', required=True)
        name = title_to_name(self.queryset, title)
        description = rest_util.parse_string(request, 'description', required=False)
        json = rest_util.parse_dict(request, 'configuration')
        base_url = rest_util.parse_string(request, 'base_url', required=False)
        is_active = rest_util.parse_bool(request, 'is_active', default_value=True, required=False)

        configuration = None
        if json:
            try:
                configuration = WorkspaceConfigurationV6(json, do_validate=True).get_configuration()
            except InvalidWorkspaceConfiguration as ex:
                message = 'Workspace configuration invalid'
                logger.exception(message)
                raise BadParameter('%s: %s' % (message, unicode(ex)))

        try:
            workspace = Workspace.objects.create_workspace(name, title, description, configuration, base_url, is_active)
        except InvalidWorkspaceConfiguration as ex:
            logger.exception('Unable to create new workspace: %s', name)
            raise BadParameter(unicode(ex))

        # Fetch the full workspace with details
        try:
            workspace = Workspace.objects.get_details(workspace.id)
        except Workspace.DoesNotExist:
            raise Http404

        serializer = WorkspaceDetailsSerializerV6(workspace)
        workspace_url = reverse('workspace_details_view', args=[workspace.id], request=request)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=dict(location=workspace_url))

class WorkspaceDetailsView(GenericAPIView):
    """This view is the endpoint for retrieving/updating details of a workspace."""
    queryset = Workspace.objects.all()

    def get_serializer_class(self):
        """Returns the appropriate serializer based off the requests version of the REST API"""

        if self.request.version == 'v6':
            return WorkspaceDetailsSerializerV6
        elif self.request.version == 'v5':
            return WorkspaceDetailsSerializerV5
        elif self.request.version == 'v4':
            return WorkspaceDetailsSerializerV5

    def get(self, request, workspace_id):
        """Retrieves the details for a workspace and return them in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param workspace_id: The id of the workspace
        :type workspace_id: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        if request.version == 'v6':
            return self._get_v6(request, workspace_id)
        elif request.version == 'v5':
            return self._get_v5(request, workspace_id)
        elif request.version == 'v4':
            return self._get_v5(request, workspace_id)

        raise Http404()


    def _get_v5(self, request, workspace_id):
        """Retrieves the details for a workspace and return them in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param workspace_id: The id of the workspace
        :type workspace_id: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """
        try:
            workspace = Workspace.objects.get_details(workspace_id)
        except Workspace.DoesNotExist:
            raise Http404

        serializer = self.get_serializer(workspace)
        return Response(serializer.data)

    def _get_v6(self, request, workspace_id):
        """Retrieves the details for a workspace and return them in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param workspace_id: The id of the workspace
        :type workspace_id: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """
        try:
            workspace = Workspace.objects.get_details(workspace_id)
        except Workspace.DoesNotExist:
            raise Http404

        serializer = self.get_serializer(workspace)
        return Response(serializer.data)

    def patch(self, request, workspace_id):
        """Edits an existing workspace and returns the updated details

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param workspace_id: The id of the workspace
        :type workspace_id: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        if request.version == 'v6':
            return self._patch_v6(request, workspace_id)
        elif request.version == 'v5':
            return self._patch_v5(request, workspace_id)
        elif request.version == 'v4':
            return self._patch_v5(request, workspace_id)

        raise Http404()

    def _patch_v5(self, request, workspace_id):
        """Edits an existing workspace and returns the updated details

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param workspace_id: The ID for the workspace.
        :type workspace_id: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        title = rest_util.parse_string(request, 'title', required=False)
        description = rest_util.parse_string(request, 'description', required=False)
        json_config = rest_util.parse_dict(request, 'json_config', required=False)
        base_url = rest_util.parse_string(request, 'base_url', required=False)
        is_active = rest_util.parse_string(request, 'is_active', required=False)

        configuration = None
        if json_config:
            try:
                configuration = WorkspaceConfigurationV1(json_config, do_validate=True).get_configuration()
            except InvalidWorkspaceConfiguration as ex:
                message = 'Workspace configuration invalid'
                logger.exception(message)
                raise BadParameter('%s: %s' % (message, unicode(ex)))

        try:
            Workspace.objects.edit_workspace(workspace_id, title, description, configuration, base_url, is_active)

            workspace = Workspace.objects.get_details(workspace_id)
        except Workspace.DoesNotExist:
            raise Http404
        except InvalidWorkspaceConfiguration as ex:
            logger.exception('Unable to edit workspace: %s', workspace_id)
            raise BadParameter(unicode(ex))

        serializer = self.get_serializer(workspace)
        return Response(serializer.data)

    def _patch_v6(self, request, workspace_id):
        """Edits an existing workspace and returns the updated details

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param workspace_id: The ID for the workspace.
        :type workspace_id: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        title = rest_util.parse_string(request, 'title', required=False)
        description = rest_util.parse_string(request, 'description', required=False)
        json = rest_util.parse_dict(request, 'configuration', required=False)
        base_url = rest_util.parse_string(request, 'base_url', required=False)
        is_active = rest_util.parse_string(request, 'is_active', required=False)

        configuration = None
        if json:
            try:
                configuration = WorkspaceConfigurationV6(json, do_validate=True).get_configuration()
            except InvalidWorkspaceConfiguration as ex:
                message = 'Workspace configuration invalid'
                logger.exception(message)
                raise BadParameter('%s: %s' % (message, unicode(ex)))

        try:
            Workspace.objects.edit_workspace(workspace_id, title, description, configuration, base_url, is_active)
        except Workspace.DoesNotExist:
            raise Http404
        except InvalidWorkspaceConfiguration as ex:
            logger.exception('Unable to edit workspace: %s', workspace_id)
            raise BadParameter(unicode(ex))

        return HttpResponse(status=204)


class WorkspacesValidationView(APIView):
    """This view is the endpoint for validating a new workspace before attempting to actually create it"""
    queryset = Workspace.objects.all()

    def post(self, request):
        """Validates a new workspace and returns any warnings discovered

        :param request: the HTTP POST request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        if request.version == 'v6':
            return self._post_v6(request)
        elif request.version == 'v5':
            return self._post_v5(request)
        elif request.version == 'v4':
            return self._post_v5(request)

        raise Http404()

    def _post_v5(self, request):
        """Validates a new workspace and returns any warnings discovered

        :param request: the HTTP POST request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        name = rest_util.parse_string(request, 'name')
        json_config = rest_util.parse_dict(request, 'json_config')

        rest_util.parse_string(request, 'title', required=False)
        rest_util.parse_string(request, 'description', required=False)
        rest_util.parse_string(request, 'base_url', required=False)
        rest_util.parse_string(request, 'is_active', required=False)

        # Validate the workspace configuration
        try:
            warnings = Workspace.objects.validate_workspace_v5(name, json_config)
        except InvalidWorkspaceConfiguration as ex:
            logger.exception('Unable to validate new workspace: %s', name)
            raise BadParameter(unicode(ex))

        results = [{'id': w.name, 'details': w.description} for w in warnings]
        return Response({'warnings': results})

    def _post_v6(self, request):
        """Validates a new workspace and returns any warnings discovered

        :param request: the HTTP POST request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        configuration = rest_util.parse_dict(request, 'configuration')

        name = rest_util.parse_string(request, 'name', required=False)
        title = rest_util.parse_string(request, 'title', required=True)
        if not name:
            name = title_to_name(self.queryset, title)
        rest_util.parse_string(request, 'description', required=False)
        rest_util.parse_string(request, 'base_url', required=False)
        rest_util.parse_string(request, 'is_active', required=False)

        # Validate the workspace configuration

        validation = Workspace.objects.validate_workspace_v6(name=name, configuration=configuration)
        resp_dict = {'is_valid': validation.is_valid, 'errors': [e.to_dict() for e in validation.errors],
                     'warnings': [w.to_dict() for w in validation.warnings]}
          
        if not resp_dict['is_valid']:
            return Response(resp_dict, status=status.HTTP_400_BAD_REQUEST)
        return Response(resp_dict)
