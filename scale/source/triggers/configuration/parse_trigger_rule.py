'''Defines the configuration for a parse trigger'''
from __future__ import unicode_literals

import logging

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from job.configuration.data.job_connection import JobConnection
from recipe.configuration.data.recipe_connection import RecipeConnection
from recipe.triggers.configuration.trigger_rule import RecipeTriggerRuleConfiguration
from source.triggers.parse_trigger_condition import ParseTriggerCondition
from storage.models import Workspace
from trigger.configuration.exceptions import InvalidTriggerRule


logger = logging.getLogger(__name__)


PARSE_TRIGGER_SCHEMA = {
    "type": "object",
    "required": ["data"],
    "additionalProperties": False,
    "properties": {
        "version": {
            "description": "Version of the parse trigger schema",
            "type": "string",
        },
        "condition": {
            "description": "Condition for a parsed file to trigger an event",
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "media_type": {
                    "description": "Media type required by a parsed file to trigger an event",
                    "type": "string",
                },
                "data_types": {
                    "description": "Data types required by a parsed file to trigger an event",
                    "type": "array",
                    "items": {"$ref": "#/definitions/data_type_tag"}
                },
            }
        },
        "data": {
            "description": "The input data to pass to a triggered job/recipe",
            "type": "object",
            "required": ["input_data_name", "workspace_name"],
            "additionalProperties": False,
            "properties": {
                "input_data_name": {
                    "description": "The name of the job/recipe input data to pass the parsed file to",
                    "type": "string",
                },
                "workspace_name": {
                    "description": "The name of the workspace to use for the triggered job/recipe",
                    "type": "string",
                }
            }
        }
    },
    "definitions": {
        "data_type_tag": {
            "description": "A simple data type tag string",
            "type": "string",
        }
    }
}


class ParseTriggerRuleConfiguration(RecipeTriggerRuleConfiguration):
    '''Represents a rule that triggers when parsed source files meet the defined conditions
    '''

    def __init__(self, trigger_rule_type, configuration):
        '''Creates a parse trigger from the given configuration

        :param trigger_rule_type: The trigger rule type
        :type trigger_rule_type: str
        :param configuration: The parse trigger configuration
        :type configuration: dict

        :raises trigger.configuration.exceptions.InvalidTriggerRule: If the configuration is invalid
        '''

        super(ParseTriggerRuleConfiguration, self).__init__(trigger_rule_type, configuration)

        try:
            validate(configuration, PARSE_TRIGGER_SCHEMA)
        except ValidationError as validation_error:
            raise InvalidTriggerRule(validation_error)

        self._populate_default_values()

        version = self._dict['version']
        if version != '1.0':
            raise InvalidTriggerRule('%s is an unsupported version number' % version)

    def get_condition(self):
        '''Returns the condition for this parse trigger rule

        :return: The trigger condition
        :rtype: :class:`source.triggers.parse_trigger_condition.ParseTriggerCondition`
        '''

        media_type = None
        if self._dict['condition']['media_type']:
            media_type = self._dict['condition']['media_type']

        data_types = set(self._dict['condition']['data_types'])

        return ParseTriggerCondition(media_type, data_types)

    def get_input_data_name(self):
        '''Returns the name of the input data that the parsed file should be passed to

        :return: The input data name
        :rtype: str
        '''

        return self._dict['data']['input_data_name']

    def get_workspace_name(self):
        '''Returns the name of the workspace to use for the triggered job/recipe

        :return: The workspace name
        :rtype: str
        '''

        return self._dict['data']['workspace_name']

    def validate(self):
        '''See :meth:`trigger.configuration.trigger_rule.TriggerRuleConfiguration.validate`
        '''

        workspace_name = self.get_workspace_name()

        if Workspace.objects.filter(name=workspace_name).count() == 0:
            raise InvalidTriggerRule('%s is an invalid workspace name' % workspace_name)

    def validate_trigger_for_job(self, job_interface):
        '''See :meth:`job.triggers.configuration.trigger_rule.JobTriggerRuleConfiguration.validate_trigger_for_job`
        '''

        input_file_name = self.get_input_data_name()
        media_type = self.get_condition().get_media_type()
        media_types = [media_type] if media_type else None

        connection = JobConnection()
        connection.add_input_file(input_file_name, False, media_types, False)
        connection.add_workspace()

        return job_interface.validate_connection(connection)

    def validate_trigger_for_recipe(self, recipe_definition):
        '''See :meth:`recipe.triggers.configuration.trigger_rule.RecipeTriggerRuleConfiguration.validate_trigger_for_recipe`
        '''

        input_file_name = self.get_input_data_name()
        media_type = self.get_condition().get_media_type()
        media_types = [media_type] if media_type else None

        connection = RecipeConnection()
        connection.add_input_file(input_file_name, False, media_types, False)
        connection.add_workspace()

        return recipe_definition.validate_connection(connection)

    def _populate_default_values(self):
        '''Populates any missing default values in the configuration
        '''

        if 'version' not in self._dict:
            self._dict['version'] = '1.0'

        if 'condition' not in self._dict:
            self._dict['condition'] = {}
        if 'media_type' not in self._dict['condition']:
            self._dict['condition']['media_type'] = ''
        if 'data_types' not in self._dict['condition']:
            self._dict['condition']['data_types'] = []
