"""Defines a command message that creates condition models"""
from __future__ import unicode_literals

import logging
from collections import namedtuple

from django.db import transaction

from job.messages.process_job_input import create_process_job_input_messages
from messaging.messages.message import CommandMessage
from recipe.messages.process_condition import create_process_condition_messages
from recipe.models import Recipe, RecipeNode


# This is the maximum number of condition models that can fit in one message. This maximum ensures that every message of
# this type is less than 25 KiB long and that each message can be processed quickly.
MAX_NUM = 100


# Tuple for specifying each condition to create
RecipeCondition = namedtuple('RecipeCondition', ['node_name', 'process_input'])


logger = logging.getLogger(__name__)


def create_conditions_messages(recipe, conditions):
    """Creates messages to create conditions with a recipe

    :param recipe: The recipe model
    :type recipe: :class:`recipe.models.Recipe`
    :param conditions: The list of RecipeCondition tuples describing the conditions to create
    :type conditions: list
    :return: The list of messages
    :rtype: list
    """

    messages = []

    message = None
    for condition in conditions:
        if not message:
            message = CreateConditions()
            message.recipe_id = recipe.id
            message.root_recipe_id = recipe.root_superseded_recipe_id
            message.batch_id = recipe.batch_id
        elif not message.can_fit_more():
            messages.append(message)
            message = CreateConditions()
            message.recipe_id = recipe.id
            message.root_recipe_id = recipe.root_superseded_recipe_id
            message.batch_id = recipe.batch_id
        message.add_recipe_condition(condition)
    if message:
        messages.append(message)

    return messages


class CreateConditions(CommandMessage):
    """Command message that creates condition models
    """

    def __init__(self):
        """Constructor
        """

        super(CreateConditions, self).__init__('create_conditions')

        self.batch_id = None
        self.recipe_id = None
        self.root_recipe_id = None
        self.conditions = []
        self._process_input = {}  # process_input flags stored by new condition ID

    def add_recipe_condition(self, recipe_condition):
        """Adds the given recipe condition to this message to be created

        :param recipe_condition: The recipe condition
        :type recipe_condition: :class:`recipe.messages.create_conditions.RecipeCondition`
        """

        self.conditions.append(recipe_condition)

    def can_fit_more(self):
        """Indicates whether more conditions can fit in this message

        :return: True if more conditions can fit, False otherwise
        :rtype: bool
        """

        return len(self.conditions) < MAX_NUM

    def to_json(self):
        """See :meth:`messaging.messages.message.CommandMessage.to_json`
        """

        json_dict = {'recipe_id': self.recipe_id}

        if self.root_recipe_id:
            json_dict['root_recipe_id'] = self.root_recipe_id
        if self.batch_id:
            json_dict['batch_id'] = self.batch_id
        conditions = []
        for condition in self.conditions:
            conditions.append({'node_name': condition.node_name, 'process_input': condition.process_input})
        json_dict['conditions'] = conditions

        return json_dict

    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`
        """

        message = CreateConditions()

        message.recipe_id = json_dict['recipe_id']
        if 'root_recipe_id' in json_dict:
            message.root_recipe_id = json_dict['root_recipe_id']
        if 'batch_id' in json_dict:
            message.batch_id = json_dict['batch_id']
        for condition_dict in json_dict['conditions']:
            condition = RecipeCondition(condition_dict['node_name'], condition_dict['process_input'])
            message.add_recipe_condition(condition)

        return message

    def execute(self):
        """See :meth:`messaging.messages.message.CommandMessage.execute`
        """

        with transaction.atomic():
            self._perform_locking()
            condition_models = self._find_existing_conditions()
            if not condition_models:
                condition_models = self._create_conditions()

        process_input_condition_ids = []
        for condition_model in condition_models:
            # process_input indicates if condition is ready to get its input from its dependencies
            process_input = self._process_input.get(condition_models.id, False)
            if process_input:
                # This new condition is all ready to have its input processed
                process_input_condition_ids.append(condition_model.id)
        self.new_messages.extend(create_process_condition_messages(process_input_condition_ids))

        return True

    def _create_conditions(self):
        """Creates the condition models for the message

        :returns: The list of condition models created
        :rtype: list
        """

        condition_models = {}  # {Node name: condition model}

        # Create new condition models
        process_input_by_node = {}
        for condition in self.conditions:
            node_name = condition.node_name
            process_input_by_node[node_name] = condition.process_input
            condition = RecipeCondition.objects.create_condition(self.recipe_id, root_recipe_id=self.root_recipe_id,
                                                                 batch_id=self.batch_id)
            condition_models[node_name] = condition

        RecipeCondition.objects.bulk_create(condition_models.values())
        logger.info('Created %d condition(s)', len(condition_models))

        # Create recipe nodes
        recipe_nodes = RecipeNode.objects.create_recipe_condition_nodes(self.recipe_id, condition_models)
        RecipeNode.objects.bulk_create(recipe_nodes)

        # Set up process input dict
        for condition in self.conditions:
            condition_model = condition_models[condition.node_name]
            self._process_input[condition_model.id] = condition.process_input

        return condition_models.values()

    def _find_existing_conditions(self):
        """Searches to determine if this message already ran and the conditions already exist

        :returns: The list of condition models found
        :rtype: list
        """

        node_names = [condition.node_name for condition in self.conditions]
        qry = RecipeNode.objects.select_related('condition')
        qry = qry.filter(recipe_id=self.recipe_id, node_name__in=node_names)
        condition_models_by_node = {recipe_node.node_name: recipe_node.condition for recipe_node in qry}
        condition_models = conditions_by_node.values()

        if condition_models_by_node:
            # Set up process input dict
            for condition in self.conditions:
                condition_model = condition_models_by_node[condition.node_name]
                self._process_input[condition_model.id] = condition.process_input

        return condition_models

    def _perform_locking(self):
        """Performs locking so that multiple messages don't interfere with each other. The caller must be within an
        atomic transaction.
        """

        Recipe.objects.get_locked_recipe(self.recipe_id)
