"""Defines the views for the RESTful storage services"""
from __future__ import unicode_literals

import logging

import django.core.urlresolvers as urlresolvers
import rest_framework.status as status
from django.http.response import Http404
from rest_framework.generics import GenericAPIView, ListCreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

import util.rest as rest_util
from util.rest import BadParameter
from storage.configuration.exceptions import InvalidWorkspaceConfiguration
from storage.models import Workspace
from storage.serializers import WorkspaceDetailsSerializer, WorkspaceSerializer

logger = logging.getLogger(__name__)


class WorkspacesView(ListCreateAPIView):
    """This view is the endpoint for retrieving the list of all workspaces."""
    queryset = Workspace.objects.all()
    serializer_class = WorkspaceSerializer

    def list(self, request):
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

        name = rest_util.parse_string(request, 'name')
        title = rest_util.parse_string(request, 'title', required=False)
        description = rest_util.parse_string(request, 'description', required=False)
        json_config = rest_util.parse_dict(request, 'json_config')
        base_url = rest_util.parse_string(request, 'base_url', required=False)
        is_active = rest_util.parse_bool(request, 'is_active', default_value=True, required=False)

        try:
            workspace = Workspace.objects.create_workspace(name, title, description, json_config, base_url, is_active)
        except InvalidWorkspaceConfiguration as ex:
            logger.exception('Unable to create new workspace: %s', name)
            raise BadParameter(unicode(ex))

        # Fetch the full workspace with details
        try:
            workspace = Workspace.objects.get_details(workspace.id)
        except Workspace.DoesNotExist:
            raise Http404

        serializer = WorkspaceDetailsSerializer(workspace)
        workspace_url = urlresolvers.reverse('workspace_details_view', args=[workspace.id])
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=dict(location=workspace_url))


class WorkspaceDetailsView(GenericAPIView):
    """This view is the endpoint for retrieving/updating details of a workspace."""
    queryset = Workspace.objects.all()
    serializer_class = WorkspaceDetailsSerializer

    def get(self, request, workspace_id):
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

        try:
            Workspace.objects.edit_workspace(workspace_id, title, description, json_config, base_url, is_active)

            workspace = Workspace.objects.get_details(workspace_id)
        except Workspace.DoesNotExist:
            raise Http404
        except InvalidWorkspaceConfiguration as ex:
            logger.exception('Unable to edit workspace: %s', workspace_id)
            raise BadParameter(unicode(ex))

        serializer = self.get_serializer(workspace)
        return Response(serializer.data)


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

        name = rest_util.parse_string(request, 'name')
        json_config = rest_util.parse_dict(request, 'json_config')

        rest_util.parse_string(request, 'title', required=False)
        rest_util.parse_string(request, 'description', required=False)
        rest_util.parse_string(request, 'base_url', required=False)
        rest_util.parse_string(request, 'is_active', required=False)

        # Validate the workspace configuration
        try:
            warnings = Workspace.objects.validate_workspace(name, json_config)
        except InvalidWorkspaceConfiguration as ex:
            logger.exception('Unable to validate new workspace: %s', name)
            raise BadParameter(unicode(ex))

        results = [{'id': w.key, 'details': w.details} for w in warnings]
        return Response({'warnings': results})
