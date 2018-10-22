"""Defines a command message that evaluates and updates a recipe"""
from __future__ import unicode_literals

import logging

from django.utils.timezone import now

from job.messages.blocked_jobs import create_blocked_jobs_messages
from job.messages.create_jobs import create_jobs_messages_for_recipe, RecipeJob
from job.messages.pending_jobs import create_pending_jobs_messages
from job.messages.process_job_input import create_process_job_input_messages
from job.models import JobType
from messaging.messages.message import CommandMessage
from recipe.definition.node import JobNodeDefinition, RecipeNodeDefinition
from recipe.diff.forced_nodes import ForcedNodes
from recipe.diff.json.forced_nodes_v6 import convert_forced_nodes_to_v6, ForcedNodesV6
from recipe.messages.create_recipes import create_subrecipes_messages, SubRecipe
from recipe.messages.process_recipe_input import create_process_recipe_input_messages
from recipe.models import Recipe, RecipeType, RecipeTypeRevision
from recipe.models import RecipeTypeSubLink, RecipeTypeJobLink


logger = logging.getLogger(__name__)


def create_sub_update_recipe_definition_message(recipe_type_id, sub_recipe_type_id):
    """Creates a message to update the given recipe type to use the latest revision of the sub recipe type

    :param recipe_type_id: The recipe type to update
    :type recipe_type_id: int
    :param sub_recipe_type_id: The sub recipe type
    :type sub_recipe_type_id: int
    :return: The message
    :rtype: :class:`recipe.messages.update_recipe.UpdateRecipeDefinition`
    """

    message = UpdateRecipeDefinition()
    message.recipe_type_id = recipe_type_id
    message.sub_recipe_type_id = sub_recipe_type_id
    return message


def create_job_update_recipe_definition_message(recipe_type_id, job_type_id):
    """Creates a message to update the given recipe type to use the latest revision of the job type

    :param recipe_type_id: The recipe type to update
    :type recipe_type_id: int
    :param job_type_id: The job type
    :type job_type_id: int
    :return: The list of messages
    :rtype: list
    """

    message = UpdateRecipeDefinition()
    message.recipe_type_id = recipe_type_id
    message.job_type_id = job_type_id
    return message


class UpdateRecipeDefinition(CommandMessage):
    """Command message that evaluates and updates a recipe
    """

    def __init__(self):
        """Constructor
        """

        super(UpdateRecipeDefinition, self).__init__('update_recipe_definition')

        self.recipe_type_id = None
        self.sub_recipe_type_id = None
        self.job_type_id = None

    def to_json(self):
        """See :meth:`messaging.messages.message.CommandMessage.to_json`
        """

        json_dict = {
            'recipe_type_id': self.recipe_type_id,
            'sub_recipe_type_id': self.sub_recipe_type_id,
            'job_type_id': self.job_type_id
        }

        return json_dict

    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`
        """

        message = UpdateRecipeDefinition()
        message.recipe_type_id = json_dict['recipe_type_id']
        message.sub_recipe_type_id = json_dict['sub_recipe_type_id']
        message.job_type_id = json_dict['job_type_id']

        return message

    def execute(self):
        """See :meth:`messaging.messages.message.CommandMessage.execute`
        """

        # Acquire model lock
        recipe_type = RecipeType.objects.select_for_update().get(pk=self.recipe_type_id)

        definition = recipe_type.get_definition()

        updated_node = True
        if self.sub_recipe_type_id:
            sub = RecipeType.objects.get(pk=self.sub_recipe_type_id)
            updated_node = definition.update_recipe_nodes(recipe_type_name=sub.name,
                                           revision_num=sub.revision_num)
        if self.job_type_id:
            jt = JobType.objects.get(pk=self.job_type_id)
            updated_node = definition.update_job_nodes(job_type_name=jt.name, job_type_version=jt.version,
                                        revision_num=jt.revision_num)

        valid = False
        
        if updated_node:
            #RecipeType.objects.edit_recipe_type(definition=definition)
            for n in definition.graph.values():
                n.

        if valid:
            recipe_type.definition = definition.get_dict()
            recipe_type.revision_num = recipe_type.revision_num + 1
            recipe_type.save()
            RecipeTypeRevision.objects.create_recipe_type_revision(recipe_type)
            parents = RecipeTypeSubLink.objects.get_recipe_type_ids([self.recipe_type_id])
            for p in parents:
                #avoid infinite recursion
                if p != self.sub_recipe_type_id:
                    msg = create_sub_update_recipe_definition_message(p, self.recipe_type_id)
                    self.new_messages.extend(msg)
        return True
