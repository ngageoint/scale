"""Defines the class for managing a batch definition"""
from __future__ import unicode_literals

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
