"""Defines the views for the RESTful storage services"""
from __future__ import unicode_literals

import logging

from django.http.response import Http404
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response

import util.rest as rest_util
from storage.models import Workspace
from storage.serializers import WorkspaceDetailsSerializer, WorkspaceSerializer

logger = logging.getLogger(__name__)


class WorkspacesView(ListAPIView):
    """This view is the endpoint for retrieving the list of all workspaces."""
    queryset = Workspace.objects.all()
    serializer_class = WorkspaceSerializer

    def get(self, request):
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


class WorkspaceDetailsView(RetrieveAPIView):
    """This view is the endpoint for retrieving/updating details of a workspace."""
    queryset = Workspace.objects.all()
    serializer_class = WorkspaceDetailsSerializer

    def retrieve(self, request, workspace_id):
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
