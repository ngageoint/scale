"""Node Views"""
from __future__ import unicode_literals

import logging

import rest_framework.status as status
from django.http.response import Http404
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.response import Response

import mesos_api.api as mesos_api
import util.rest as rest_util
from node.models import Node
from node.serializers import NodeSerializer, NodeDetailsSerializer
from scheduler.models import Scheduler

logger = logging.getLogger(__name__)


class NodesView(ListAPIView):
    """This view is the endpoint for viewing a list of nodes with metadata"""
    queryset = Node.objects.all()
    serializer_class = NodeSerializer

    def list(self, request):
        """Determine api version and call specific method

        :param request: the HTTP POST request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        if request.version == 'v6':
            return self.list_impl(request)

        raise Http404()

    def list_impl(self, request):
        """Retrieves the list of all nodes and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        started = rest_util.parse_timestamp(request, 'started', required=False)
        ended = rest_util.parse_timestamp(request, 'ended', required=False)
        rest_util.check_time_range(started, ended)
        is_active = rest_util.parse_bool(request, 'is_active', None, False)

        order = rest_util.parse_string_list(request, 'order', required=False)

        nodes = Node.objects.get_nodes(started, ended, order, is_active=is_active)

        page = self.paginate_queryset(nodes)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class NodeDetailsView(GenericAPIView):
    """This view is the endpoint for viewing and modifying a node"""
    queryset = Node.objects.all()
    update_fields = ('pause_reason', 'is_paused', 'is_active')
    serializer_class = NodeDetailsSerializer

    def get(self, request, node_id):
        """Determine api version and call specific method

        :param request: the HTTP POST request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        if request.version == 'v6':
            return self.get_impl(request, node_id)

        raise Http404()

    def get_impl(self, request, node_id):
        """Gets node info

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param node_id: The ID for the node.
        :type node_id: str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        try:
            node = Node.objects.get_details(node_id)
        except Node.DoesNotExist:
            raise Http404

        serializer = self.get_serializer(node)
        return Response(serializer.data)

    def patch(self, request, node_id):
        """Determine api version and call specific method

        :param request: the HTTP PATCH request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        if request.version == 'v6':
            return self.patch_v6(request, node_id)

        raise Http404()

    def patch_v6(self, request, node_id):
        """Modify node info with a subset of fields

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param node_id: The ID for the node.
        :type node_id: str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        extra = filter(lambda x, y=self.update_fields: x not in y, request.data.keys())
        if len(extra) > 0:
            return Response('Unexpected fields: %s' % ', '.join(extra), status=status.HTTP_400_BAD_REQUEST)

        if not len(request.data):
            return Response('No fields specified for update.', status=status.HTTP_400_BAD_REQUEST)

        try:
            Node.objects.get(id=node_id)
        except Node.DoesNotExist:
            raise Http404

        Node.objects.update_node(dict(request.data), node_id=node_id)

        return Response(status=status.HTTP_204_NO_CONTENT)
