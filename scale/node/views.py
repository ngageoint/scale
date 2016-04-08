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
from node.serializers import NodeSerializer
from node.serializers_extra import NodeDetailsSerializer, NodeStatusSerializer
from scheduler.models import Scheduler

logger = logging.getLogger(__name__)


class NodesView(ListAPIView):
    """This view is the endpoint for viewing a list of nodes with metadata"""
    queryset = Node.objects.all()
    serializer_class = NodeSerializer

    def list(self, request):
        """Retrieves the list of all nodes and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """
        started = rest_util.parse_timestamp(request, 'started', required=False)
        ended = rest_util.parse_timestamp(request, 'ended', required=False)
        rest_util.check_time_range(started, ended)
        include_inactive = rest_util.parse_bool(request, 'include_inactive', False, False)

        order = rest_util.parse_string_list(request, 'order', required=False)

        nodes = Node.objects.get_nodes(started, ended, order, include_inactive=include_inactive)

        page = self.paginate_queryset(nodes)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class NodeDetailsView(GenericAPIView):
    """This view is the endpoint for viewing and modifying a node"""
    queryset = Node.objects.all()
    serializer_class = NodeDetailsSerializer
    update_fields = ('hostname', 'port', 'pause_reason', 'is_paused', 'is_active')
    required_fields = ('hostname', 'port', 'is_paused', 'is_active')

    def get(self, request, node_id):
        """Gets node info

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param node_id: The ID for the node.
        :type node_id: str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        # Fetch the basic node attributes
        try:
            node = Node.objects.get_details(node_id)
        except Node.DoesNotExist:
            raise Http404
        serializer = self.get_serializer(node)
        result = serializer.data

        # Attempt to fetch resource usage for the node
        resources = None
        try:
            sched = Scheduler.objects.get_master()
            slave_info = mesos_api.get_slave(sched.master_hostname, sched.master_port, node.slave_id, True)
            if slave_info and slave_info.total:
                resources = slave_info.to_dict()['resources']
        except:
            logger.exception('Unable to fetch slave resource usage')
        if resources:
            result['resources'] = resources
        else:
            result['disconnected'] = True

        return Response(result)

    def put(self, request, node_id):
        """Modify node info by replacing an object

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param node_id: The ID for the node.
        :type node_id: str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        missing = filter(lambda x, y=request.data.keys(): x not in y, self.required_fields)
        if len(missing):
            return Response('Missing required fields: %s' % ', '.join(missing), status=status.HTTP_400_BAD_REQUEST)

        extra = filter(lambda x, y=self.update_fields: x not in y, request.data.keys())
        if len(extra):
            return Response('Unexpected fields: %s' % ', '.join(extra), status=status.HTTP_400_BAD_REQUEST)

        try:
            Node.objects.get(id=node_id)
        except Node.DoesNotExist:
            raise Http404

        Node.objects.update_node(dict(request.data), node_id=node_id)

        node = Node.objects.get(id=node_id)
        serializer = NodeSerializer(node)
        return Response(serializer.data, status=status.HTTP_201_CREATED,
                        headers={'Location': request.build_absolute_uri()})

    def patch(self, request, node_id):
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
        node = Node.objects.get(id=node_id)
        serializer = NodeSerializer(node)
        return Response(serializer.data, status=status.HTTP_201_CREATED,
                        headers={'Location': request.build_absolute_uri()})


class NodesStatusView(ListAPIView):
    """This view is the endpoint for retrieving overall node status information."""
    queryset = []
    serializer_class = NodeStatusSerializer

    def list(self, request):
        """Retrieves the list of all nodes with execution status and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        # Get a list of all node status counts
        started = rest_util.parse_timestamp(request, 'started', 'PT3H0M0S')
        ended = rest_util.parse_timestamp(request, 'ended', required=False)
        node_statuses = Node.objects.get_status(started, ended)

        # Get the online nodes
        try:
            sched = Scheduler.objects.get_master()
            slaves = mesos_api.get_slaves(sched.master_hostname, sched.master_port)
            slaves_dict = {s.hostname for s in slaves}
        except:
            logger.exception('Unable to fetch nodes online status')
            slaves_dict = dict()

        # Add the online status to each node
        for node_status in node_statuses:
            node_status.is_online = node_status.node.hostname in slaves_dict

        page = self.paginate_queryset(node_statuses)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)
