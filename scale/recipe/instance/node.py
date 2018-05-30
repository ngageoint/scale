"""Defines the classes for representing nodes within a recipe"""
from __future__ import unicode_literals

from abc import ABCMeta


class NodeInstance(object):
    """Represents a node within a recipe
    """

    __metaclass__ = ABCMeta

    def __init__(self, definition):
        """Constructor

        :param definition: The definition of this node in the recipe
        :type definition: :class:`recipe.definition.node.NodeDefinition`
        """

        self.definition = definition

        self.name = self.definition.name
        self.node_type = self.definition.node_type
        self.parents = {}  # {Name: Node}
        self.children = {}  # {Name: Node}
        self.blocks_child_jobs = False  # Whether this node blocks child jobs from running

    def add_dependency(self, node):
        """Adds a dependency that this node has on the given node

        :param node: The dependency node to add
        :type node: :class:`recipe.instance.node.NodeInstance`
        """

        self.parents[node.name] = node
        node.children[self.name] = self

    def get_jobs_to_update(self, pending_job_ids, blocked_job_ids):
        """Adds a job ID to one of the given lists if it needs to be updated to PENDING or BLOCKED status

        :param pending_job_ids: The list of IDs for jobs that should be set to PENDING
        :type pending_job_ids: list
        :param blocked_job_ids: The list of IDs for jobs that should be set to BLOCKED
        :type blocked_job_ids: list
        """

        self.blocks_child_jobs = False

        # If any of this node's parents block child jobs, then this job blocks child jobs as well
        for parent_node in self.parents.values():
            self.blocks_child_jobs = self.blocks_child_jobs or parent_node.blocks_child_jobs


class JobNodeInstance(NodeInstance):
    """Represents a job within a recipe
    """

    def __init__(self, definition, job):
        """Constructor

        :param definition: The definition of this node in the recipe
        :type definition: :class:`recipe.definition.node.JobNodeDefinition`
        :param job: The job model
        :type job: :class:`job.models.Job`
        """

        super(JobNodeInstance, self).__init__(definition)

        self.job = job

    def get_jobs_to_update(self, pending_job_ids, blocked_job_ids):
        """See :meth:`recipe.instance.node.NodeInstance.get_jobs_to_update`
        """

        # Check parent nodes
        super(JobNodeInstance, self).get_jobs_to_update(pending_job_ids, blocked_job_ids)

        # A job must block child nodes if it is CANCELED or FAILED
        if self.job.status in ['CANCELED', 'FAILED']:
            self.blocks_child_jobs = True

        # If this job is BLOCKED and it does not block child jobs, it should be updated to PENDING
        if self.job.status == 'BLOCKED' and not self.blocks_child_jobs:
            pending_job_ids.append(self.job.id)

        # If this job is PENDING and it blocks child jobs, it should be updated to BLOCKED
        if self.job.status == 'PENDING' and self.blocks_child_jobs:
            blocked_job_ids.append(self.job.id)


class RecipeNodeInstance(NodeInstance):
    """Represents a recipe within a recipe
    """

    def __init__(self, definition, recipe):
        """Constructor

        :param definition: The definition of this node in the recipe
        :type definition: :class:`recipe.definition.node.RecipeNodeDefinition`
        :param recipe: The recipe model
        :type recipe: :class:`recipe.models.Recipe`
        """

        super(RecipeNodeInstance, self).__init__(definition)

        self.recipe = recipe

    def get_jobs_to_update(self, pending_job_ids, blocked_job_ids):
        """See :meth:`recipe.instance.node.NodeInstance.get_jobs_to_update`
        """

        # Check parent nodes
        super(RecipeNodeInstance, self).get_jobs_to_update(pending_job_ids, blocked_job_ids)

        # A recipe blocks child nodes if it has any BLOCKED, CANCELED, or FAILED jobs in it
        num_blocking_jobs = self.recipe.jobs_blocked + self.recipe.jobs_canceled + self.recipe.jobs_failed
        if num_blocking_jobs > 0:
            self.blocks_child_jobs = True
