'''Defines the views for the RESTful storage services'''
from __future__ import unicode_literals

import logging

import rest_framework.status as status
from django.http.response import Http404
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

import util.rest as rest_util
from storage.models import Workspace
from storage.serializers import WorkspaceDetailsSerializer, WorkspaceListSerializer

logger = logging.getLogger(__name__)


class WorkspacesView(APIView):
    '''This view is the endpoint for retrieving the list of all workspaces.'''
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def get(self, request):
        '''Retrieves the list of all workspaces and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        '''

        started = rest_util.parse_timestamp(request, 'started', required=False)
        ended = rest_util.parse_timestamp(request, 'ended', required=False)
        rest_util.check_time_range(started, ended)

        names = rest_util.parse_string_list(request, 'name', required=False)
        order = rest_util.parse_string_list(request, 'order', ['name'])

        workspaces = Workspace.objects.get_workspaces(started, ended, names, order)

        page = rest_util.perform_paging(request, workspaces)
        serializer = WorkspaceListSerializer(page, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class WorkspaceDetailsView(APIView):
    '''This view is the endpoint for retrieving/updating details of a workspace.'''
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def get(self, request, workspace_id):
        '''Retrieves the details for a workspace and return them in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param workspace_id: The id of the workspace
        :type workspace_id: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        '''
        try:
            workspace = Workspace.objects.get_details(workspace_id)
        except Workspace.DoesNotExist:
            raise Http404

        serializer = WorkspaceDetailsSerializer(workspace)
        return Response(serializer.data, status=status.HTTP_200_OK)
