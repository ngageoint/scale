"""Defines the class for managing a batch definition"""
from __future__ import unicode_literals

from jsonschema import validate
from jsonschema.exceptions import ValidationError

import util.parse as parse
from batch.definition.exceptions import InvalidDefinition
from storage.models import Workspace
from trigger.configuration.exceptions import InvalidTriggerRule
from trigger.configuration.trigger_rule import TriggerRuleConfiguration


DEFAULT_VERSION = '1.0'

BATCH_DEFINITION_SCHEMA = {
    'type': 'object',
    'additionalProperties': False,
    'properties': {
        'version': {
            'description': 'Version of the batch definition schema',
            'type': 'string',
            'pattern': '^.{0,50}$',
        },
        'date_range': {
            '$ref': '#/definitions/date_range_item',
        },
        'job_names': {
            'description': 'A list of job names that should be re-processed',
            'type': ['array', 'null'],
            'items': {
                'type': 'string',
            },
        },
        'all_jobs': {
            'description': 'A flag that indicates all jobs should be re-processed even if they are identical',
            'type': 'boolean',
        },
        'priority': {
            'description': 'The priority to use when creating new jobs for the batch',
            'type': 'integer',
        },
        'trigger_rule': {
            '$ref': '#/definitions/trigger_rule_item',
        }
    },
    'definitions': {
        'date_range_item': {
            'description': 'A range of dates used to determine which recipes should be re-processed',
            'type': 'object',
            'anyOf': [
                {'required': ['started']},
                {'required': ['ended']},
            ],
            'additionalProperties': False,
            'properties': {
                'type': {
                    'description': 'Indicates how the date range should be interpreted',
                    'type': 'string',
                    'enum': ['created', 'data'],
                },
                'started': {
                    'description': 'The start of the range to use when matching recipes to re-process',
                    'type': 'string',
                },
                'ended': {
                    'description': 'The end of the range to use when matching recipes to re-process',
                    'type': 'string',
                },
            },
        },
        'trigger_rule_item': {
            'description': 'Configuration used to evaluate a file for potential batch processing',
            'type': ['object', 'boolean'],
            'condition': {
                'description': 'Condition for an input file to trigger an event',
                'type': 'object',
                'additionalProperties': False,
                'properties': {
                    'media_type': {
                        'description': 'Media type required by an input file to trigger an event',
                        'type': 'string',
                    },
                    'data_types': {
                        'description': 'Data types required by an input file to trigger an event',
                        'type': 'array',
                        'items': {'$ref': '#/definitions/data_type_tag'}
                    },
                }
            },
            'data': {
                'description': 'The input data to pass to a triggered job/recipe',
                'type': 'object',
                'required': ['input_data_name', 'workspace_name'],
                'additionalProperties': False,
                'properties': {
                    'input_data_name': {
                        'description': 'The name of the job/recipe input data to pass the input file to',
                        'type': 'string',
                    },
                    'workspace_name': {
                        'description': 'The name of the workspace to use for the triggered job/recipe',
                        'type': 'string',
                    }
                }
            }
        },
        'data_type_tag': {
            'description': 'A simple data type tag string',
            'type': 'string',
        },
    },
}


class ValidationWarning(object):
    """Tracks batch definition warnings during validation that may not prevent the batch from working."""

    def __init__(self, key, details):
        """Constructor sets basic attributes.

        :param key: A unique identifier clients can use to recognize the warning.
        :type key: string
        :param details: A user-friendly description of the problem, including field names and/or associated values.
        :type details: string
        """
        self.key = key
        self.details = details


class BatchDefinition(object):
    """Represents the definition for a batch."""

    def __init__(self, definition):
        """Creates a batch definition object from the given dictionary. The general format is checked for correctness.

        :param definition: The batch definition
        :type definition: dict

        :raises :class:`batch.configuration.definition.exceptions.InvalidDefinition`:
            If the given definition is invalid
        """

        self._definition = definition

        try:
            validate(definition, BATCH_DEFINITION_SCHEMA)
        except ValidationError as ex:
            raise InvalidDefinition('Invalid batch definition: %s' % unicode(ex))

        self._populate_default_values()
        if not self._definition['version'] == '1.0':
            raise InvalidDefinition('%s is an unsupported version number' % self._definition['version'])

        date_range = self._definition['date_range'] if 'date_range' in self._definition else None
        self.date_range_type = None
        if date_range and 'type' in date_range:
            self.date_range_type = date_range['type']

        self.started = None
        if date_range and 'started' in date_range:
            try:
                self.started = parse.parse_datetime(date_range['started'])
            except ValueError:
                raise InvalidDefinition('Invalid start date format: %s' % date_range['started'])
        self.ended = None
        if date_range and 'ended' in date_range:
            try:
                self.ended = parse.parse_datetime(date_range['ended'])
            except ValueError:
                raise InvalidDefinition('Invalid end date format: %s' % date_range['ended'])

        self.job_names = self._definition['job_names']
        self.all_jobs = self._definition['all_jobs']

        self.priority = None
        if 'priority' in self._definition:
            try:
                self.priority = self._definition['priority']
            except ValueError:
                raise InvalidDefinition('Invalid priority: %s' % self._definition['priority'])

        self.trigger_rule = False
        self.trigger_config = None
        if 'trigger_rule' in self._definition:
            if isinstance(self._definition['trigger_rule'], bool):
                self.trigger_rule = self._definition['trigger_rule']
            else:
                self.trigger_config = BatchTriggerConfiguration('BATCH', self._definition['trigger_rule'])

    def get_dict(self):
        """Returns the internal dictionary that represents this batch definition

        :returns: The internal dictionary
        :rtype: dict
        """

        return self._definition

    def validate(self, recipe_type):
        """Validates the given recipe type to make sure it is valid with respect to the batch definition.

        :param recipe_type: The recipe type associated with the batch.
        :type recipe_type: :class:`recipe.models.RecipeType`
        :returns: A list of warnings discovered during validation.
        :rtype: list
        """

        if self.trigger_config:
            self.trigger_config.validate()

        warnings = []
        if self._definition['trigger_rule'] is True and recipe_type.trigger_rule is None:
            warnings.append(ValidationWarning('trigger_rule',
                                              'Recipe type does not have a trigger rule: %i' % recipe_type.id))
        return warnings

    def _populate_default_values(self):
        """Goes through the definition and populates any missing values with defaults"""

        if 'version' not in self._definition:
            self._definition['version'] = DEFAULT_VERSION

        if 'date_range' in self._definition:
            if 'type' not in self._definition['date_range']:
                self._definition['date_range']['type'] = 'created'

        if 'job_names' not in self._definition:
            self._definition['job_names'] = None
        if 'all_jobs' not in self._definition:
            self._definition['all_jobs'] = False

        if 'trigger_rule' not in self._definition:
            self._definition['trigger_rule'] = False


class BatchTriggerConfiguration(TriggerRuleConfiguration):

    def __init__(self, trigger_rule_type, configuration):
        """Creates a batch trigger from the given configuration

        :param trigger_rule_type: The trigger rule type
        :type trigger_rule_type: string
        :param configuration: The batch trigger configuration
        :type configuration: dict

        :raises trigger.configuration.exceptions.InvalidTriggerRule: If the configuration is invalid
        """

        super(BatchTriggerConfiguration, self).__init__(trigger_rule_type, configuration)

        self._populate_default_values()

    def get_condition(self):
        """Returns the condition for this batch trigger rule

        :return: The trigger condition
        :rtype: :class:`batch.definition.json.old.batch_definition.BatchTriggerCondition`
        """

        media_type = None
        if self._dict['condition']['media_type']:
            media_type = self._dict['condition']['media_type']

        data_types = set(self._dict['condition']['data_types'])

        return BatchTriggerCondition(media_type, data_types)

    def get_input_data_name(self):
        """Returns the name of the input data that the triggered input files should be passed to.

        :return: The input data name
        :rtype: string
        """

        return self._dict['data']['input_data_name']

    def get_workspace_name(self):
        """Returns the name of the workspace to use for the triggered input files.

        :return: The workspace name
        :rtype: string
        """

        return self._dict['data']['workspace_name']

    def validate(self):
        """Validates the trigger rule configuration. This is a more thorough validation than the basic schema checks
        performed in trigger rule constructors and may include database queries.

        :raises trigger.configuration.exceptions.InvalidTriggerRule: If the configuration is invalid
        """

        workspace_name = self.get_workspace_name()
        if Workspace.objects.filter(name=workspace_name).count() == 0:
            raise InvalidTriggerRule('%s is an invalid workspace name' % workspace_name)

    def _populate_default_values(self):
        """Goes through the definition and populates any missing values with defaults"""

        if 'condition' not in self._dict:
            self._dict['condition'] = {}
        if 'media_type' not in self._dict['condition']:
            self._dict['condition']['media_type'] = ''
        if 'data_types' not in self._dict['condition']:
            self._dict['condition']['data_types'] = []


class BatchTriggerCondition(object):
    """Represents the condition for a batch trigger rule."""

    def __init__(self, media_type, data_types):
        """Creates a batch trigger condition.

        :param media_type: The media type that a file must match, possibly None
        :type media_type: string
        :param data_types: The set of data types that a file must match, possibly None
        :type data_types: {string}
        """

        self._media_type = media_type
        self._data_types = data_types if data_types is not None else set()

    def get_media_type(self):
        """Returns the file media type for this batch trigger condition.

        :return: The media type
        :rtype: string
        """

        return self._media_type

    def is_condition_met(self, input_file):
        """Indicates whether the given input file meets this batch trigger condition.

        :param input_file: The input file to test
        :type input_file: :class:`source.models.ScaleFile`
        :return: True if the condition is met, False otherwise
        :rtype: bool
        """

        if self._media_type and self._media_type != input_file.media_type:
            return False

        return self._data_types <= input_file.get_data_type_tags()
