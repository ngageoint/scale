'''Node Views'''
from __future__ import unicode_literals

import logging

import rest_framework.status as status
from django.http.response import Http404
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

import mesos_api.api as mesos_api
import util.rest as rest_util
from node.models import Node
from node.serializers import NodeSerializer, NodeListSerializer
from node.serializers_extra import NodeDetailsSerializer, NodeStatusListSerializer
from scheduler.models import Scheduler

logger = logging.getLogger(__name__)


class NodesView(APIView):
    '''This view is the endpoint for viewing a list of nodes with metadata'''
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def get(self, request):
        '''Retrieves the list of all nodes and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        '''
        started = rest_util.parse_timestamp(request, 'started', required=False)
        ended = rest_util.parse_timestamp(request, 'ended', required=False)
        rest_util.check_time_range(started, ended)
        include_inactive = rest_util.parse_bool(request, 'include_inactive', False, False)

        order = rest_util.parse_string_list(request, 'order', required=False)

        nodes = Node.objects.get_nodes(started, ended, order, include_inactive=include_inactive)

        page = rest_util.perform_paging(request, nodes)
        serializer = NodeListSerializer(page, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class NodeDetailsView(APIView):
    '''This view is the endpoint for viewing and modifying a node'''
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    update_fields = ('hostname', 'port', 'pause_reason', 'is_paused', 'is_active')
    required_fields = ('hostname', 'port', 'is_paused', 'is_active')

    def get(self, request, node_id):
        '''Gets node info

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param node_id: The ID for the node.
        :type node_id: str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        '''

        # Fetch the basic node attributes
        try:
            node = Node.objects.get_details(node_id)
        except Node.DoesNotExist:
            raise Http404
        serializer = NodeDetailsSerializer(node)
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

        return Response(serializer.data)

    def put(self, request, node_id):
        '''Modify node info by replacing an object

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param node_id: The ID for the node.
        :type node_id: str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        '''

        missing = filter(lambda x, y=request.DATA.keys(): x not in y, self.required_fields)
        if len(missing):
            return Response('Missing required fields: %s' % ', '.join(missing), status=status.HTTP_400_BAD_REQUEST)

        extra = filter(lambda x, y=self.update_fields: x not in y, request.DATA.keys())
        if len(extra):
            return Response('Unexpected fields: %s' % ', '.join(extra), status=status.HTTP_400_BAD_REQUEST)

        try:
            Node.objects.get(id=node_id)
        except Node.DoesNotExist:
            raise Http404

        Node.objects.update_node(dict(request.DATA), node_id=node_id)

        node = Node.objects.get(id=node_id)
        serializer = NodeSerializer(node)
        return Response(serializer.data, status=status.HTTP_201_CREATED,
                        headers={'Location': request.build_absolute_uri()})

    def patch(self, request, node_id):
        '''Modify node info with a subset of fields

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param node_id: The ID for the node.
        :type node_id: str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        '''

        extra = filter(lambda x, y=self.update_fields: x not in y, request.DATA.keys())
        if len(extra) > 0:
            return Response('Unexpected fields: %s' % ', '.join(extra), status=status.HTTP_400_BAD_REQUEST)

        if not len(request.DATA):
            return Response('No fields specified for update.', status=status.HTTP_400_BAD_REQUEST)

        try:
            Node.objects.get(id=node_id)
        except Node.DoesNotExist:
            raise Http404

        Node.objects.update_node(dict(request.DATA), node_id=node_id)
        node = Node.objects.get(id=node_id)
        serializer = NodeSerializer(node)
        return Response(serializer.data, status=status.HTTP_201_CREATED,
                        headers={'Location': request.build_absolute_uri()})


class NodesStatusView(APIView):
    '''This view is the endpoint for retrieving overall node status information.'''

    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def get(self, request):
        '''Retrieves the list of all nodes with execution status and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        '''

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

        page = rest_util.perform_paging(request, node_statuses)
        serializer = NodeStatusListSerializer(page, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
