"""Defines a command message that evaluates and updates a recipe"""
from __future__ import unicode_literals

import logging

from job.models import JobType
from messaging.messages.message import CommandMessage
from recipe.definition.definition import InvalidDefinition
from recipe.definition.json.definition_v6 import convert_recipe_definition_to_v6_json
from recipe.models import RecipeType, RecipeTypeRevision
from recipe.models import RecipeTypeSubLink

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
            inputs, outputs = definition.get_interfaces()
            warnings = []
            try:
                warnings = definition.validate(inputs, outputs)
                valid = True
            except InvalidDefinition as ex:
                logger.exception("Invalid definition updating recipe type with id=%i: %s", self.recipe_type_id, ex)
                valid = False

            if len(warnings) > 0:
                logger.warning('Warnings found when validating updated recipe definition: %s', warnings)

        if valid:
            recipe_type.definition = convert_recipe_definition_to_v6_json(definition).get_dict()
            recipe_type.revision_num = recipe_type.revision_num + 1
            recipe_type.save()
            RecipeTypeRevision.objects.create_recipe_type_revision(recipe_type)
            parents = RecipeTypeSubLink.objects.get_recipe_type_ids([self.recipe_type_id])
            for p in parents:
                # avoid infinite recursion
                if p != self.sub_recipe_type_id:
                    msg = create_sub_update_recipe_definition_message(p, self.recipe_type_id)
                    self.new_messages.extend(msg)
        return True
