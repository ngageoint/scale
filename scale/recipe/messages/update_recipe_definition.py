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
        
        with transaction.atomic():
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
                job_types = definition.get_job_type_keys()
                inputs, outputs = self._get_interfaces(definition)
                warnings = []
                try:
                    warnings = definition.validate(inputs, outputs)
                    valid = True
                except InvalidDefinition as ex:
                    logger.info("Invalid definition automatically updating recipe type with id=%i: %s", self.recipe_type_id, ex)
                    valid = False
    
                if len(warnings) > 0:
                    logger.info('Warnings found when validating updated recipe definition: %s', warnings)
    
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
                        self.new_messages.append(msg)
        return True

    def _get_interfaces(self, definition):
        """Gets the input and output interfaces for each node in this recipe

        :returns: A dict of input interfaces and a dict of output interfaces
        :rtype: dict, dict
        """

        inputs = {}
        outputs = {}
        
        for node_name in definition.get_topological_order():
            node = self.graph[node_name]
            if node.node_type == JobNodeDefinition.NODE_TYPE:
                inputs[node_name], outputs[node_name] = _get_job_interfaces(node)
            elif node.node_type == RecipeNodeDefinition.NODE_TYPE:
                inputs[node_name], outputs[node_name] = _get_recipe_interfaces(node)

        return inputs, outputs
        
    def _get_job_interfaces(self, node):
        """Gets the input/output interfaces for a job type node
        """
        
        from job.models import JobTypeRevision
        input = Interface()
        output = Interface()
        jtr = JobTypeRevision.objects.get_details_v6(self.job_type_name, self.job_type_version, self.revision_num)
        if jtr:
            input = jtr.get_input_interface()
            output = jtr.get_output_interface()
            
        return input, output
        
    def _get_recipe_interfaces(self, node):
        """Gets the input/output interfaces for a recipe type node
        """
        
        from recipe.models import RecipeTypeRevision
        input = Interface()
        output = Interface()
        rtr = RecipeTypeRevision.objects.get_revision(self.recipe_type_name, self.revision_num)
        if jtr:
            input = jtr.get_input_interface() # no output interface
            
        return input, output