"""Defines the class for managing a batch definition"""
from __future__ import unicode_literals

import datetime

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from batch.configuration.definition.exceptions import InvalidDefinition


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
                    'pattern': '^\d{4}-\d{2}-\d{2}$',
                },
                'ended': {
                    'description': 'The end of the range to use when matching recipes to re-process',
                    'type': 'string',
                    'pattern': '^\d{4}-\d{2}-\d{2}$',
                },
            },
        },
    },
}


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
                self.started = datetime.datetime.strptime(date_range['started'], '%Y-%m-%d')
            except ValueError:
                raise InvalidDefinition('Invalid start date format: %s' % date_range['started'])
        self.ended = None
        if date_range and 'ended' in date_range:
            try:
                self.ended = datetime.datetime.strptime(date_range['ended'], '%Y-%m-%d')
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

    def get_dict(self):
        """Returns the internal dictionary that represents this batch definition

        :returns: The internal dictionary
        :rtype: dict
        """

        return self._definition

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
