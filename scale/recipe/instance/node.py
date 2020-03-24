"""Defines the classes for representing nodes within a recipe"""
from __future__ import absolute_import
from __future__ import unicode_literals

from abc import ABCMeta

from recipe.definition.node import ConditionNodeDefinition


class NodeInstance(object):
    """Represents a node within a recipe
    """

    __metaclass__ = ABCMeta

    def __init__(self, definition, is_original):
        """Constructor

        :param definition: The definition of this node in the recipe
        :type definition: :class:`recipe.definition.node.NodeDefinition`
        :param is_original: Whether this node is original
        :type is_original: bool
        """

        self.definition = definition

        self.name = self.definition.name
        self.node_type = self.definition.node_type
        self.parents = {}  # {Name: Node}
        self.children = {}  # {Name: Node}
        self.already_created = True  # Whether this node has already been created
        self.children_can_be_created = True  # Whether this node's children can be created
        self.blocks_child_nodes = False  # Whether this node blocks child nodes from running
        self.is_original = is_original  # Whether this node is the original version (not copied from superseded recipe)
        self.is_real_node = True  # Flag used to "hide" placeholders
        self.parental_acceptance = {} # Flags used to define whether this node should created based on parents' acceptance states

    def add_dependency(self, node, acceptance=True):
        """Adds a dependency that this node has on the given node

        :param node: The dependency node to add
        :type node: :class:`recipe.instance.node.NodeInstance`
        :param acceptance: Whether this node should run when the parent is accepted or when it is not accepted
        :type acceptance: bool
        """

        self.parents[node.name] = node
        self.parental_acceptance[node.name] = acceptance
        node.children[self.name] = self

    def get_jobs_to_update(self, pending_job_ids, blocked_job_ids):
        """Adds a job ID to one of the given lists if it needs to be updated to PENDING or BLOCKED status

        :param pending_job_ids: The list of IDs for jobs that should be set to PENDING
        :type pending_job_ids: :func:`list`
        :param blocked_job_ids: The list of IDs for jobs that should be set to BLOCKED
        :type blocked_job_ids: :func:`list`
        """

        self.blocks_child_nodes = False

        # If any of this node's parents block child jobs, then this job blocks child jobs as well
        for parent_node in self.parents.values():
            self.blocks_child_nodes = self.blocks_child_nodes or parent_node.blocks_child_nodes

    def is_completed(self):
        """Indicates whether this node has completed

        :returns: True if this node has completed, False otherwise
        :rtype: bool
        """

        return False

    def is_accepted(self):
        """Indicates whether this node is accepted.  Used for evaluating condition nodes

        :returns: True if this node is accepted, false otherwise. Will always return true except for condition nodes
        :rtype: bool
        """

        return True
        
    def is_ready_for_children(self):
        """Indicates whether this node is ready for its children to process

        :returns: True if this node is ready for its children to process, False otherwise
        :rtype: bool
        """

        return self.is_completed()

    def needs_to_be_created(self):
        """Indicates whether this node needs to be created

        :returns: True if this node needs to be created, False otherwise
        :rtype: bool
        """

        needs_to_be_created = not self.already_created
        self.children_can_be_created = True

        if needs_to_be_created:
            # If any of this node's parents cannot be created yet, then this node cannot be created yet
            for name in self.parents:
                parent_node = self.parents[name]
                if not parent_node.children_can_be_created:
                    needs_to_be_created = False
                    self.children_can_be_created = False
                    break
                if self.parental_acceptance[name] and not parent_node.is_accepted():
                    needs_to_be_created = False
                    self.children_can_be_created = False
                    break

        return needs_to_be_created

    def needs_to_process_input(self):
        """Indicates whether this node needs to process its input

        :returns: True if this node needs to process its input, False otherwise
        :rtype: bool
        """

        # Ensure all parents are completed and ready for this node to process its input
        for parent_node in self.parents.values():
            if not parent_node.is_ready_for_children():
                return False

        return True


class ConditionNodeInstance(NodeInstance):
    """Represents a condition within a recipe
    """

    def __init__(self, definition, condition, is_original):
        """Constructor

        :param definition: The definition of this node in the recipe
        :type definition: :class:`recipe.definition.node.ConditionNodeDefinition`
        :param condition: The condition model
        :type condition: :class:`recipe.models.RecipeCondition`
        :param is_original: Whether this condition is original
        :type is_original: bool
        """

        super(ConditionNodeInstance, self).__init__(definition, is_original)

        self.condition = condition

    def is_completed(self):
        """See :meth:`recipe.instance.node.NodeInstance.is_completed`
        """

        return self.condition.is_processed
        
    def is_accepted(self):
        """Indicates whether this node is accepted.  Used for evaluating condition nodes

        :returns: True if the condition for this node is accepted, false otherwise.
        :rtype: bool
        """

        return self.condition.is_accepted

    def is_ready_for_children(self):
        """See :meth:`recipe.instance.node.NodeInstance.is_ready_for_children`
        """

        return self.condition.is_processed and self.condition.is_accepted

    def needs_to_be_created(self):
        """See :meth:`recipe.instance.node.NodeInstance.needs_to_be_created`
        """

        # Check parent nodes
        needs_to_be_created = super(ConditionNodeInstance, self).needs_to_be_created()

        # Children can be created once the condition has been processed
        # We need to check later which children to create depending on the condition passing/failing
        self.children_can_be_created = self.condition.is_processed

        return needs_to_be_created

    def needs_to_process_input(self):
        """See :meth:`recipe.instance.node.NodeInstance.needs_to_process_input`
        """

        # Check parent nodes
        can_process_input = super(ConditionNodeInstance, self).needs_to_process_input()

        return can_process_input and not self.condition.is_processed


class DummyNodeInstance(NodeInstance):
    """Represents a placeholder node that stands in for a node that doesn't exist in this recipe instance
    """

    def __init__(self, definition):
        """Constructor

        :param definition: The definition of this node in the recipe
        :type definition: :class:`recipe.definition.node.RecipeNodeDefinition`
        """

        super(DummyNodeInstance, self).__init__(definition, True)

        self.already_created = False
        self.is_real_node = False

    def is_completed(self):
        """See :meth:`recipe.instance.node.NodeInstance.is_completed`
        """

        return True

    def is_ready_for_children(self):
        """See :meth:`recipe.instance.node.NodeInstance.is_ready_for_children`
        """

        return False

    def needs_to_be_created(self):
        """See :meth:`recipe.instance.node.NodeInstance.needs_to_be_created`
        """

        # Check parent nodes
        needs_to_be_created = super(DummyNodeInstance, self).needs_to_be_created()

        if self.node_type == ConditionNodeDefinition.NODE_TYPE:
            # Cannot create children of a condition until the condition has been processed and accepted
            self.children_can_be_created = False

        return needs_to_be_created


class JobNodeInstance(NodeInstance):
    """Represents a job within a recipe
    """

    def __init__(self, definition, job, is_original):
        """Constructor

        :param definition: The definition of this node in the recipe
        :type definition: :class:`recipe.definition.node.JobNodeDefinition`
        :param job: The job model
        :type job: :class:`job.models.Job`
        :param is_original: Whether this job is original
        :type is_original: bool
        """

        super(JobNodeInstance, self).__init__(definition, is_original)

        self.job = job

    def get_jobs_to_update(self, pending_job_ids, blocked_job_ids):
        """See :meth:`recipe.instance.node.NodeInstance.get_jobs_to_update`
        """

        # Check parent nodes
        super(JobNodeInstance, self).get_jobs_to_update(pending_job_ids, blocked_job_ids)

        # A job must block child nodes if it is CANCELED or FAILED
        if self.job.status in ['CANCELED', 'FAILED']:
            self.blocks_child_nodes = True

        # If this job is BLOCKED and it does not block child nodes, it should be updated to PENDING
        if self.job.status == 'BLOCKED' and not self.blocks_child_nodes:
            pending_job_ids.append(self.job.id)

        # If this job is PENDING and it blocks child nodes, it should be updated to BLOCKED
        if self.job.status == 'PENDING' and self.blocks_child_nodes:
            blocked_job_ids.append(self.job.id)

    def is_completed(self):
        """See :meth:`recipe.instance.node.NodeInstance.is_completed`
        """

        return self.job.is_ready_for_children()

    def needs_to_process_input(self):
        """See :meth:`recipe.instance.node.NodeInstance.needs_to_process_input`
        """

        if self.job.status not in ['PENDING', 'BLOCKED']:
            return False
            
        # Check parent nodes
        can_process_input = super(JobNodeInstance, self).needs_to_process_input()

        return can_process_input and not self.job.has_input()


class RecipeNodeInstance(NodeInstance):
    """Represents a recipe within a recipe
    """

    def __init__(self, definition, recipe, is_original):
        """Constructor

        :param definition: The definition of this node in the recipe
        :type definition: :class:`recipe.definition.node.RecipeNodeDefinition`
        :param recipe: The recipe model
        :type recipe: :class:`recipe.models.Recipe`
        :param is_original: Whether this node is original
        :type is_original: bool
        """

        super(RecipeNodeInstance, self).__init__(definition, is_original)

        self.recipe = recipe

    def get_jobs_to_update(self, pending_job_ids, blocked_job_ids):
        """See :meth:`recipe.instance.node.NodeInstance.get_jobs_to_update`
        """

        # Check parent nodes
        super(RecipeNodeInstance, self).get_jobs_to_update(pending_job_ids, blocked_job_ids)

        # A recipe blocks child nodes if it has any BLOCKED, CANCELED, or FAILED jobs in it
        num_blocking_jobs = self.recipe.jobs_blocked + self.recipe.jobs_canceled + self.recipe.jobs_failed
        if num_blocking_jobs > 0:
            self.blocks_child_nodes = True

    def is_completed(self):
        """See :meth:`recipe.instance.node.NodeInstance.is_completed`
        """

        return self.recipe.is_completed

    def needs_to_process_input(self):
        """See :meth:`recipe.instance.node.NodeInstance.needs_to_process_input`
        """

        # Check parent nodes
        can_process_input = super(RecipeNodeInstance, self).needs_to_process_input()

        return can_process_input and not self.recipe.has_input()
