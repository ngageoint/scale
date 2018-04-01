"""Manages the v6 batch definition schema"""
from __future__ import unicode_literals

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from batch.definition.definition import BatchDefinition
from batch.definition.exceptions import InvalidDefinition


SCHEMA_VERSION = '6'

BATCH_DEFINITION_SCHEMA = {
    'type': 'object',
    'required': ['version'],
    'additionalProperties': False,
    'properties': {
        'version': {
            'description': 'Version of the batch definition schema',
            'type': 'string',
        },
        'previous_batch': {
            '$ref': '#/definitions/previous_batch',
        }
    },
    'definitions': {
        'previous_batch': {
            'description': 'Links this batch to a previous batch and re-processes the previous batch\'s recipes',
            'type': 'object',
            'required': ['root_batch_id'],
            'additionalProperties': False,
            'properties': {
                'root_batch_id': {
                    'description': 'The root ID of the previous batch',
                    'type': 'integer',
                },
                'job_names': {
                    'description': 'A list of job names that should be re-processed',
                    'type': ['array'],
                    'items': {
                        'type': 'string',
                    },
                },
                'all_jobs': {
                    'description': 'A flag that indicates all jobs should be re-processed',
                    'type': 'boolean',
                },
            },
        },
    },
}


def convert_definition_to_v6(definition):
    """Returns the v6 definition JSON for the given batch definition

    :param definition: The batch definition
    :type definition: :class:`batch.definition.definition.BatchDefinition`
    :returns: The v6 definition JSON
    :rtype: :class:`batch.definition.json.definition_v6.BatchDefinitionV6`
    """

    json_dict = {'version': '6'}
    if definition.root_batch_id is not None:
        json_dict['previous_batch'] = {'root_batch_id': definition.root_batch_id, 'job_names': definition.job_names,
                                       'all_jobs': definition.all_jobs}
    return BatchDefinitionV6(definition=json_dict, do_validate=False)


class BatchDefinitionV6(object):
    """Represents a v6 definition JSON for a batch"""

    def __init__(self, definition=None, do_validate=False):
        """Creates a v6 batch definition JSON object from the given dictionary

        :param definition: The batch definition JSON dict
        :type definition: dict
        :param do_validate: Whether to perform validation on the JSON schema
        :type do_validate: bool

        :raises :class:`batch.definition.exceptions.InvalidDefinition`: If the given definition is invalid
        """

        if not definition:
            definition = {}
        self._definition = definition

        if 'version' not in self._definition:
            self._definition['version'] = SCHEMA_VERSION

        if self._definition['version'] != SCHEMA_VERSION:
            raise InvalidDefinition('%s is an unsupported version number' % self._definition['version'])

        try:
            if do_validate:
                validate(definition, BATCH_DEFINITION_SCHEMA)
        except ValidationError as ex:
            raise InvalidDefinition('Invalid batch definition: %s' % unicode(ex))

    def get_definition(self):
        """Returns the batch definition represented by this JSON

        :returns: The batch definition
        :rtype: :class:`batch.definition.definition.BatchDefinition`:
        """

        definition = BatchDefinition()
        if 'previous_batch' in self._definition:
            prev_batch_dict = self._definition['previous_batch']
            definition.root_batch_id = prev_batch_dict['root_batch_id']
            if 'job_names' in prev_batch_dict:
                definition.job_names = prev_batch_dict['job_names']
            if 'all_jobs' in prev_batch_dict:
                definition.all_jobs = prev_batch_dict['all_jobs']

        return definition

    def get_dict(self):
        """Returns the internal dictionary

        :returns: The internal dictionary
        :rtype: dict
        """

        return self._definition
