"""Defines a command message that supersedes recipe nodes"""
from __future__ import unicode_literals

import logging

from job.messages.cancel_jobs import create_cancel_jobs_messages
from job.messages.unpublish_jobs import create_unpublish_jobs_messages
from messaging.messages.message import CommandMessage
from recipe.models import RecipeNode
from util.parse import datetime_to_string, parse_datetime


# This is the maximum number of recipe models that can fit in one message. This maximum ensures that every message of
# this type is less than 25 KiB long and that each message can be processed quickly.
MAX_NUM = 100


logger = logging.getLogger(__name__)


def create_supersede_recipe_nodes_messages(recipe_ids, when, supersede_jobs, supersede_subrecipes, unpublish_jobs,
                                           supersede_recursive, unpublish_recursive):
    """Creates messages to supersede nodes in the given recipes

    :param recipe_ids: The recipe IDs
    :type recipe_ids: list
    :param when: When the jobs/sub-recipes were superseded
    :type when: :class:`datetime.datetime`
    :param supersede_jobs: The node names for jobs to supersede
    :type supersede_jobs: set
    :param supersede_subrecipes: The node names for sub-recipes to supersede
    :type supersede_subrecipes: set
    :param unpublish_jobs: The node names for jobs to unpublish
    :type unpublish_jobs: set
    :param supersede_recursive: The node names for sub-recipes that should recursively supersede all of their nodes
    :type supersede_recursive: set
    :param unpublish_recursive: The node names for sub-recipes that should recursively supersede/unpublish all of their
        nodes
    :type unpublish_recursive: set
    :return: The list of messages
    :rtype: list
    """

    messages = []

    message = None
    for recipe_id in recipe_ids:
        if not message:
            message = SupersedeRecipeNodes()
            message.when = when
            message.supersede_jobs = supersede_jobs
            message.supersede_subrecipes = supersede_subrecipes
            message.unpublish_jobs = unpublish_jobs
            message.supersede_recursive = supersede_recursive
            message.unpublish_recursive = unpublish_recursive
        elif not message.can_fit_more():
            messages.append(message)
            message = SupersedeRecipeNodes()
            message.when = when
            message.supersede_jobs = supersede_jobs
            message.supersede_subrecipes = supersede_subrecipes
            message.unpublish_jobs = unpublish_jobs
            message.supersede_recursive = supersede_recursive
            message.unpublish_recursive = unpublish_recursive
        message.add_recipe(recipe_id)
    if message:
        messages.append(message)

    return messages


def _create_recursive_supersede_messages(recipe_ids, when):
    """Creates messages to recursively supersede all nodes in the given recipes

    :param recipe_ids: The recipe IDs
    :type recipe_ids: list
    :param when: When the jobs/sub-recipes were superseded
    :type when: :class:`datetime.datetime`
    :return: The list of messages
    :rtype: list
    """

    messages = []

    message = None
    for recipe_id in recipe_ids:
        if not message:
            message = SupersedeRecipeNodes()
            message.when = when
            message.supersede_all = True
            message.supersede_recursive_all = True
        elif not message.can_fit_more():
            messages.append(message)
            message = SupersedeRecipeNodes()
            message.when = when
            message.supersede_all = True
            message.supersede_recursive_all = True
        message.add_recipe(recipe_id)
    if message:
        messages.append(message)

    return messages


def _create_recursive_unpublish_messages(recipe_ids, when):
    """Creates messages to recursively supersede/unpublish all nodes in the given recipes

    :param recipe_ids: The recipe IDs
    :type recipe_ids: list
    :param when: When the jobs/sub-recipes were superseded
    :type when: :class:`datetime.datetime`
    :return: The list of messages
    :rtype: list
    """

    messages = []

    message = None
    for recipe_id in recipe_ids:
        if not message:
            message = SupersedeRecipeNodes()
            message.when = when
            message.supersede_all = True
            message.unpublish_all = True
            message.supersede_recursive_all = True
            message.unpublish_recursive_all = True
        elif not message.can_fit_more():
            messages.append(message)
            message = SupersedeRecipeNodes()
            message.when = when
            message.supersede_all = True
            message.unpublish_all = True
            message.supersede_recursive_all = True
            message.unpublish_recursive_all = True
        message.add_recipe(recipe_id)
    if message:
        messages.append(message)

    return messages


class SupersedeRecipeNodes(CommandMessage):
    """Command message that supersedes recipe nodes
    """

    def __init__(self):
        """Constructor
        """

        super(SupersedeRecipeNodes, self).__init__('supersede_recipe_nodes')

        self._recipe_ids = []
        self.when = None

        self.supersede_all = False  # Whether all job/sub-recipes should be superseded
        self.supersede_jobs = set()  # Node names for jobs to supersede
        self.supersede_subrecipes = set()  # Node names for sub-recipes to supersede
        self.unpublish_all = False  # Whether all jobs should be unpublished
        self.unpublish_jobs = set()  # Node names for jobs to unpublish

        self.supersede_recursive_all = False  # Whether all sub-recipes should be recursively superseded
        self.supersede_recursive = set()  # Sub-recipes that should recursively supersede all of their nodes
        self.unpublish_recursive_all = False  # Whether all sub-recipes should be recursively unpublished
        self.unpublish_recursive = set()  # Sub-recipes that should recursively unpublish all of their nodes

    def add_recipe(self, recipe_id):
        """Adds the given recipe ID to this message

        :param recipe_id: The recipe ID
        :type recipe_id: int
        """

        self._recipe_ids.append(recipe_id)

    def can_fit_more(self):
        """Indicates whether more recipes can fit in this message

        :return: True if more recipes can fit, False otherwise
        :rtype: bool
        """

        return len(self._recipe_ids) < MAX_NUM

    def to_json(self):
        """See :meth:`messaging.messages.message.CommandMessage.to_json`
        """

        json_dict = {'recipe_ids': self._recipe_ids, 'when': datetime_to_string(self.when),
                     'supersede_all': self.supersede_all, 'supersede_jobs': list(self.supersede_jobs),
                     'supersede_subrecipes': list(self.supersede_subrecipes), 'unpublish_all': self.unpublish_all,
                     'unpublish_jobs': list(self.unpublish_jobs),
                     'supersede_recursive_all': self.supersede_recursive_all,
                     'supersede_recursive': list(self.supersede_recursive),
                     'unpublish_recursive_all': self.unpublish_recursive_all,
                     'unpublish_recursive': list(self.unpublish_recursive)}

        return json_dict

    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`
        """

        message = SupersedeRecipeNodes()

        for recipe_id in json_dict['recipe_ids']:
            message.add_recipe(recipe_id)
        message.when = parse_datetime(json_dict['when'])
        message.supersede_all = json_dict['supersede_all']
        message.supersede_jobs = set(json_dict['supersede_jobs'])
        message.supersede_subrecipes = set(json_dict['supersede_subrecipes'])
        message.unpublish_all = json_dict['unpublish_all']
        message.unpublish_jobs = set(json_dict['unpublish_jobs'])
        message.supersede_recursive_all = json_dict['supersede_recursive_all']
        message.supersede_recursive = set(json_dict['supersede_recursive'])
        message.unpublish_recursive_all = json_dict['unpublish_recursive_all']
        message.unpublish_recursive = set(json_dict['unpublish_recursive'])

        return message

    def execute(self):
        """See :meth:`messaging.messages.message.CommandMessage.execute`
        """

        # Supersede the appropriate jobs and sub-recipes
        RecipeNode.objects.supersede_recipe_jobs(self._recipe_ids, self.when, self.supersede_jobs,
                                                 all_nodes=self.supersede_all)
        RecipeNode.objects.supersede_subrecipes(self._recipe_ids, self.when, self.supersede_subrecipes,
                                                all_nodes=self.supersede_all)

        # Gather job IDs and sub-recipe IDs for new messages to send
        cancel_job_ids = []
        unpublish_job_ids = []
        supersede_recursive_recipe_ids = []
        unpublish_recursive_recipe_ids = []
        for recipe_node in RecipeNode.objects.filter(recipe_id__in=self._recipe_ids).iterator():
            if recipe_node.job_id:
                # Cancel all jobs that were superseded
                if self.supersede_all or recipe_node.node_name in self.supersede_jobs:
                    cancel_job_ids.append(recipe_node.job_id)
                if self.unpublish_all or recipe_node.node_name in self.unpublish_jobs:
                    unpublish_job_ids.append(recipe_node.job_id)
            elif recipe_node.recipe_id:
                if self.unpublish_recursive_all or recipe_node.node_name in self.unpublish_recursive:
                    unpublish_recursive_recipe_ids.append(recipe_node.recipe_id)
                elif self.supersede_recursive_all or recipe_node.node_name in self.supersede_recursive:
                    supersede_recursive_recipe_ids.append(recipe_node.recipe_id)

        # Create messages to cancel and unpublish appropriate jobs
        self.new_messages.extend(create_cancel_jobs_messages(cancel_job_ids, self.when))
        self.new_messages.extend(create_unpublish_jobs_messages(unpublish_job_ids, self.when))

        # Create messages to recursively handle sub-recipes
        self.new_messages.extend(_create_recursive_supersede_messages(supersede_recursive_recipe_ids, self.when))
        self.new_messages.extend(_create_recursive_unpublish_messages(unpublish_recursive_recipe_ids, self.when))

        return True
