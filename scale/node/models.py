'''Defines the database model for a node'''

import logging

from django.db import models, transaction
from django.utils.timezone import now

logger = logging.getLogger(__name__)


class NodeStatusCounts(object):
    '''Represents job execution counts for a node.

    :keyword status: The job execution status being counted.
    :type status: str
    :keyword count: The number of job executions for the associated status handled by the node.
    :type count: int
    :keyword most_recent: The date/time of the last job execution for the associated status handled by the node.
    :type most_recent: datetime.datetime
    :keyword category: The category of the job execution status being counted. Note that currently this will only be
        populated for types of ERROR status values.
    :type category: str
    '''
    def __init__(self, status, count=0, most_recent=None, category=None):
        self.status = status
        self.count = count
        self.most_recent = most_recent
        self.category = category


class NodeStatus(object):
    '''Represents node statistics.

    :keyword node: The actual node being counted.
    :type node: :class:`node.models.Node`
    :keyword job_exe_counts: A list of counts for the job executions handled by the node organized by status.
    :type job_exe_counts: list[:class:`node.models.NodeStatusCounts`]
    :keyword job_exes_running: A list of the job executions currently running on the node.
    :type job_exes_running: list[:class:`job.models.JobExecution`]
    :keyword is_online: Indicates whether or not the node is currently online.
    :type is_online: bool
    '''
    def __init__(self, node, job_exe_counts=None, job_exes_running=None, is_online=False):
        self.node = node
        self.job_exe_counts = job_exe_counts
        self.job_exes_running = job_exes_running
        self.is_online = is_online


class NodeManager(models.Manager):
    '''Provides additional methods for handling nodes
    '''

    def get_nodes(self, started=None, ended=None, order=None, include_inactive=True):
        '''Returns a list of nodes within the given time range.

        :param started: Query nodes updated after this amount of time.
        :type started: :class:`datetime.datetime`
        :param ended: Query nodes updated before this amount of time.
        :type ended: :class:`datetime.datetime`
        :param order: A list of fields to control the sort order.
        :type order: list[str]
        :param include_inactive: Should nodes marked as inactive be included?
        :type include_inactive: boolean
        :returns: The list of nodes that match the time range.
        :rtype: list[:class:`node.models.Node`]
        '''

        # Fetch a list of nodes
        if include_inactive:
            nodes = Node.objects.all()
        else:
            nodes = Node.objects.filter(is_active=True)

        # Apply time range filtering
        if started:
            nodes = nodes.filter(last_modified__gte=started)
        if ended:
            nodes = nodes.filter(last_modified__lte=ended)

        # Apply sorting
        if order:
            nodes = nodes.order_by(*order)
        else:
            nodes = nodes.order_by(u'last_modified')
        return nodes

    def get_details(self, node_id):
        '''Gets additional details for the given node model based on related model attributes.

        The additional fields include: job executions.

        :param node_id: The unique identifier of the node.
        :type node_id: int
        :returns: The node with extra related attributes.
        :rtype: :class:`node.models.Node`
        '''
        node = Node.objects.get(pk=node_id)

        # Lazy load the the execution model since it is an optional lower level dependency
        try:
            from job.models import JobExecution
        except:
            node.job_exes_running = []
            return node

        # Augment the node with running job executions
        running_exes = JobExecution.objects.filter(node_id=node_id, status=u'RUNNING').order_by(u'last_modified')
        running_exes = running_exes.select_related(u'job').defer(u'stdout', u'stderr')
        node.job_exes_running = running_exes
        return node

    def register_node(self, hostname, port, slave_id):
        '''Registers a node with the given properties and saves the properties
        in the database. If a node with the given hostname does not exist it is
        created, else the existing node is updated.

        :param hostname: The full domain-qualified hostname of the node
        :type hostname: str
        :param port: The port being used by the executor on this node
        :type port: int
        :param slave_id: The slave ID used by Mesos for the node
        :type slave_id: str
        :returns: The node model
        :rtype: :class:`node.models.Node`
        '''

        props = {u'port': port, u'slave_id': slave_id}
        node, _created = Node.objects.update_or_create(hostname=hostname, defaults=props)
        return node

    @transaction.atomic
    def update_node(self, new_data, node_id=None):
        '''Update the data for a node.

        :param new_data: Updated data for the node
        :type new_data: dict
        :param node_id: The ID of the node to modify
        :type node_id: int
        '''

        node_query = self.select_for_update().filter(id=node_id)
        node = node_query.first()
        if node.is_active != new_data.get('is_active', None):
            if node.is_active:
                new_data['archived'] = now()
            else:
                new_data['archived'] = None
        if 'is_paused' in new_data:
            # always clear the high error rate field when changing pause state
            # the scheduler will explicitly set this flag when necessary
            new_data['is_paused_errors'] = False
        if new_data.get('is_paused', None) == False:
            # restarting the node, we should clear the pause_reason
            new_data['pause_reason'] = None
        node_query.update(**new_data)

    def get_status(self, started, ended=None):
        '''Returns a list of nodes with job execution counts broken down by status.

        This will only return active nodes. For historical node data use get_nodes()

        :param started: Query nodes updated after this amount of time.
        :type started: :class:`datetime.datetime`
        :param ended: Query nodes updated before this amount of time.
        :type ended: :class:`datetime.datetime`
        :returns: The list of nodes with supplemented statistics.
        :rtype: list[:class:`node.models.NodeStatus`]
        '''

        # Fetch the list of nodes
        nodes = list(Node.objects.filter(is_active=True))

        # Lazy load the the execution model since it is an optional lower level dependency
        try:
            from job.models import JobExecution
        except:
            return [NodeStatus(node) for node in nodes]

        # Fetch a list of recent job executions
        job_exes = JobExecution.objects.values(u'node_id', u'last_modified', u'status', u'error__category')
        job_exes = job_exes.select_related(u'error')
        job_exes = job_exes.filter(last_modified__gte=started)
        if ended:
            job_exes = job_exes.filter(last_modified__lte=ended)

        # Build a mapping of node_id -> (status + error category) -> associated counts
        job_exes_dict = {}
        for job_exe in job_exes:

            # Make sure the node mapping entry exists
            if job_exe[u'node_id'] not in job_exes_dict:
                job_exes_dict[job_exe[u'node_id']] = {}
            job_exe_dict = job_exes_dict[job_exe[u'node_id']]

            # Make sure the counts mapping entry exists
            status_key = u'%s.%s' % (job_exe[u'status'], job_exe[u'error__category'])
            if status_key not in job_exe_dict:
                job_exe_dict[status_key] = NodeStatusCounts(job_exe[u'status'])

            # Update the count based on the status
            status_counts = job_exe_dict[status_key]
            status_counts.count += 1
            if not status_counts.most_recent or job_exe[u'last_modified'] > status_counts.most_recent:
                status_counts.most_recent = job_exe[u'last_modified']
            if job_exe[u'error__category']:
                status_counts.category = job_exe[u'error__category']

        # Build a mapping of node_id -> running job executions
        running_dict = {}
        running_exes = JobExecution.objects.filter(status=u'RUNNING').order_by(u'last_modified')
        running_exes = running_exes.select_related(u'job').defer(u'stdout', u'stderr')
        for job_exe in running_exes:
            if job_exe.node_id not in running_dict:
                running_dict[job_exe.node_id] = []
            running_dict[job_exe.node_id].append(job_exe)

        # Build results for each registered node and add the extra status fields
        results = []
        for node in nodes:
            job_exe_counts = job_exes_dict[node.id].values() if node.id in job_exes_dict else []
            job_exes_running = running_dict[node.id] if node.id in running_dict else []

            node_status = NodeStatus(node, job_exe_counts, job_exes_running)
            results.append(node_status)
        return results

    # TODO: This is deprecated and currently unused. Remove this and last_offer field when next changes are made to Node
    # model
    @transaction.atomic
    def update_last_offer(self, slave_id):
        '''Update the last offer for a node with the given slave id.
        Throws a :class:`django.core.excpetions.ObjectDoesNotExist` if there is no node for the given slave id

        :param slave_id: the slave id for the node
        :type slave_id: str
        '''
        node = Node.objects.select_for_update().get(slave_id=slave_id)
        node.last_offer = now()


class Node(models.Model):
    '''Represents a cluster node on which jobs can be run

    :keyword hostname: The full domain-qualified hostname of the node
    :type hostname: :class:`django.db.models.CharField`
    :keyword port: The port being used by the executor on this node
    :type port: :class:`django.db.models.IntegerField`
    :keyword slave_id: The slave ID used by Mesos for the node
    :type slave_id: :class:`django.db.models.CharField`

    :keyword pause_reason: User or system specified reason why this node is paused. Should be used for display only.
    :type pause_reason: :class:`django.db.models.CharField`
    :keyword is_paused: True if the node is currently paused and should not accept new jobs
    :type is_paused: :class:`django.db.models.BooleanField()`
    :keyword is_paused_errors: If the node is paused, was it do to a high error rate?
    :type is_paused_errors: :class:`django.db.models.BooleanField()`
    :keyword is_active: True if the node is currently active or is archived for historical purposes
    :type is_active: :class:`django.db.models.BooleanField()`

    :keyword created: When the node model was created
    :type created: :class:`django.db.models.DateTimeField`
    :keyword archived: When the node was archived/deactivated
    :type archived: :class:`django.db.models.DateTimeField`
    :keyword last_offer: When the node last received an offer from mesos (regardless of if the offer was used)
    :type last_offer: :class:`django.db.models.DateTimeField`
    :keyword last_modified: When the node model was last modified
    :type last_modified: :class:`django.db.models.DateTimeField`
    '''

    hostname = models.CharField(max_length=250, unique=True)
    port = models.IntegerField()
    slave_id = models.CharField(max_length=250, unique=True, db_index=True)

    pause_reason = models.CharField(max_length=250, null=True)
    is_paused = models.BooleanField(default=False)
    is_paused_errors = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    created = models.DateTimeField(auto_now_add=True)
    archived = models.DateTimeField(blank=True, null=True)
    last_offer = models.DateTimeField(null=True)
    last_modified = models.DateTimeField(auto_now=True)

    objects = NodeManager()

    class Meta(object):
        '''meta information for the db'''
        db_table = u'node'
