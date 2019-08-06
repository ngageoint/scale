"""Defines the database model for a node"""
from __future__ import unicode_literals

import logging

from django.db import models, transaction
from django.utils.timezone import now

from job.models import JobExecution

logger = logging.getLogger(__name__)


class NodeManager(models.Manager):
    """Provides additional methods for handling nodes
    """

    def create_nodes(self, hostnames):
        """Creates and returns new nodes with the given host names

        :param hostnames: The list of host names
        :type hostnames: list
        :returns: The list of new nodes
        :rtype: list
        """

        nodes = []
        for i in range(len(hostnames)):
            node = Node(hostname=hostnames[i])
            nodes.append(node)
        self.bulk_create(nodes)
        return nodes

    def get_details(self, node_id):
        """Gets additional details for the given node model based on related model attributes.

        The additional fields include: job executions.

        :param node_id: The unique identifier of the node.
        :type node_id: int
        :returns: The node with extra related attributes.
        :rtype: :class:`node.models.Node`
        """

        return Node.objects.get(pk=node_id)

    def get_nodes(self, started=None, ended=None, order=None, is_active=None):
        """Returns a list of nodes within the given time range.

        :param started: Query nodes updated after this amount of time.
        :type started: :class:`datetime.datetime`
        :param ended: Query nodes updated before this amount of time.
        :type ended: :class:`datetime.datetime`
        :param order: A list of fields to control the sort order.
        :type order: list[str]
        :param is_active: Include only active nodes, only inactive nodes or both?
        :type is_active: boolean
        :returns: The list of nodes that match the time range.
        :rtype: list[:class:`node.models.Node`]
        """

        # Fetch a list of nodes
        if is_active is None:
            nodes = Node.objects.all()
        else:
            nodes = Node.objects.filter(is_active=is_active)

        # Apply time range filtering
        if started:
            nodes = nodes.filter(last_modified__gte=started)
        if ended:
            nodes = nodes.filter(last_modified__lte=ended)

        # Apply sorting
        if order:
            nodes = nodes.order_by(*order)
        else:
            nodes = nodes.order_by('last_modified')
        return nodes

    def get_nodes_running_job_exes(self):
        """Returns a list of nodes that are currently running job_exes.

        :returns: The list of node ids running job_exes
        :rtype: list
        """

        exclude_statuses = ['COMPLETED', 'FAILED', 'CANCELED']
        job_exes = JobExecution.objects.all().exclude(jobexecutionend__status__in=exclude_statuses)
        return Node.objects.filter(id__in=job_exes, is_active=True).values_list('id', flat=True)

    def get_scheduler_nodes(self, hostnames):
        """Returns a list of all nodes that either have one of the given host names or is active.

        :param hostnames: The list of host names
        :type hostnames: list
        :returns: The list of nodes for the scheduler
        :rtype: list
        """

        return Node.objects.filter(models.Q(hostname__in=hostnames) | models.Q(is_active=True))

    @transaction.atomic
    def update_node(self, new_data, node_id=None):
        """Update the data for a node.

        :param new_data: Updated data for the node
        :type new_data: dict
        :param node_id: The ID of the node to modify
        :type node_id: int
        """

        node_query = self.select_for_update().filter(id=node_id)
        node = node_query.first()
        if node.is_active != new_data.get('is_active', None):
            if node.is_active:
                new_data['deprecated'] = now()
            else:
                new_data['deprecated'] = None
        if new_data.get('is_paused', None) == False:
            # restarting the node, we should clear the pause_reason
            new_data['pause_reason'] = None
        node_query.update(**new_data)

    @transaction.atomic
    def update_node_offers(self, hostnames, when):
        """Update the last_offer_received field for nodes.

        :param updates: List of maps to be updated [{hostname: string, offer_received: datetime},]
        :type new_data: [str]
        """
        
        Node.objects.filter(hostname__in=hostnames).update(last_offer_received=when)


class Node(models.Model):
    """Represents a cluster node on which jobs can be run

    :keyword hostname: The full domain-qualified hostname of the node
    :type hostname: :class:`django.db.models.CharField`

    :keyword pause_reason: User or system specified reason why this node is paused. Should be used for display only.
    :type pause_reason: :class:`django.db.models.CharField`
    :keyword is_paused: True if the node is currently paused and should not accept new jobs
    :type is_paused: :class:`django.db.models.BooleanField()`
    :keyword is_active: True if the node is currently active or is deprecated for historical purposes
    :type is_active: :class:`django.db.models.BooleanField()`

    :keyword created: When the node model was created
    :type created: :class:`django.db.models.DateTimeField`
    :keyword deprecated: When the node was deprecated (no longer active)
    :type deprecated: :class:`django.db.models.DateTimeField`
    :keyword last_offer_received: When mesos last offered resources for this node
    :type last_offer_received: :class:`django.db.models.DateTimeField`
    :keyword last_modified: When the node model was last modified
    :type last_modified: :class:`django.db.models.DateTimeField`
    """

    hostname = models.CharField(max_length=250, unique=True)

    pause_reason = models.CharField(max_length=250, null=True)
    is_paused = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    created = models.DateTimeField(auto_now_add=True)
    deprecated = models.DateTimeField(blank=True, null=True)
    last_offer_received = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    objects = NodeManager()

    class Meta(object):
        """meta information for the db"""
        db_table = 'node'
