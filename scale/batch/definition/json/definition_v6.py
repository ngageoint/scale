"""Manages the v6 batch definition schema"""
from __future__ import unicode_literals

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from batch.definition.definition import BatchDefinition
from batch.definition.exceptions import InvalidDefinition
from recipe.diff.json.forced_nodes_v6 import convert_forced_nodes_to_v6, ForcedNodesV6


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
                'forced_nodes': {
                    'description': 'The recipe nodes that should be forced to re-process',
                    'type': 'object',
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
        prev_batch_dict = {'root_batch_id': definition.root_batch_id}
        if definition.forced_nodes:
            prev_batch_dict['forced_nodes'] = convert_forced_nodes_to_v6(definition.forced_nodes).get_dict()
        json_dict['previous_batch'] = prev_batch_dict
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
            msg = '%s is an unsupported version number' % self._definition['version']
            raise InvalidDefinition('INVALID_BATCH_DEFINITION', msg)

        try:
            if do_validate:
                validate(self._definition, BATCH_DEFINITION_SCHEMA)
                if 'forced_nodes' in self._definition:
                    ForcedNodesV6(self._definition['forced_nodes'], do_validate=True)
        except ValidationError as ex:
            raise InvalidDefinition('INVALID_BATCH_DEFINITION', 'Invalid batch definition: %s' % unicode(ex))

    def get_definition(self):
        """Returns the batch definition represented by this JSON

        :returns: The batch definition
        :rtype: :class:`batch.definition.definition.BatchDefinition`:
        """

        definition = BatchDefinition()
        if 'previous_batch' in self._definition:
            prev_batch_dict = self._definition['previous_batch']
            definition.root_batch_id = prev_batch_dict['root_batch_id']
            if 'forced_nodes' in prev_batch_dict:
                definition.forced_nodes = ForcedNodesV6(prev_batch_dict['forced_nodes']).get_forced_nodes()

        return definition

    def get_dict(self):
        """Returns the internal dictionary

        :returns: The internal dictionary
        :rtype: dict
        """

        return self._definition
