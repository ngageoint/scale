"""Manages the DataSet definition schema"""
from __future__ import unicode_literals

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from data.data.exceptions import InvalidData
from data.data.json.data_v6 import DATA_SCHEMA, DataV6, convert_data_to_v6_json
from data.interface.json.interface_v6 import INTERFACE_SCHEMA, InterfaceV6, convert_interface_to_v6_json
from dataset.exceptions import InvalidDataSetDefinition
from dataset.definition.definition import DataSetDefinition

import util.rest as rest_utils

SCHEMA_VERSION = '7'
SCHEMA_VERSIONS = ['6', '7']

DATASET_DEFINITION_SCHEMA = {
    'type': 'object',
    'required': ['version', 'parameters'],
    'additionalProperties': False,
    'properties': {
        'version': {
            'description': 'The version of the dataset definition schema',
            'type': 'string',
        },
        'global_parameters': INTERFACE_SCHEMA,
        'global_data': DATA_SCHEMA,
        'parameters': INTERFACE_SCHEMA,
    },
}

def convert_definition_to_v6_json(definition):
    """Returns the v6 dataset definition JSON for the given definition

    :param definition: The dataset definition
    :type definition: :class:`dataset.definition.DataSetDefinition'
    :returns: The v6 dataset definition JSON
    :rtype: :class:`dataset.json.DataSetDefinitionV6
    """

    def_dict = {
        'version': SCHEMA_VERSION
    }

    if definition.parameters:
        interface_dict = convert_interface_to_v6_json(definition.parameters).get_dict()
        def_dict['parameters'] = rest_utils.strip_schema_version(interface_dict)

    if definition.global_parameters:
        interface_dict = convert_interface_to_v6_json(definition.global_parameters).get_dict()
        def_dict['global_parameters'] = rest_utils.strip_schema_version(interface_dict)

    if definition.global_data:
        data_dict = convert_data_to_v6_json(definition.global_data).get_dict()
        def_dict['global_data'] = rest_utils.strip_schema_version(data_dict)

    return DataSetDefinitionV6(definition=def_dict, do_validate=False)

class DataSetDefinitionV6(object):
    """
    Represents the definition of a DataSet object

    :keyword definition: The dataset definition JSON dict
    :type definition: dict
    :keyword do_validate: Whether to perform validation on the JSON schema
    :type created_time: bool
    """
    def __init__(self, definition=None, do_validate=False):
        """Constructor
        """

        if not definition:
            definition = {}
        self._definition = definition

        if 'version' not in self._definition:
            self._definition['version'] = SCHEMA_VERSION

        if self._definition['version'] not in SCHEMA_VERSIONS:
            msg = '%s is an unsupported version number'
            raise InvalidDataSetDefinition('INVALID_VERSION', msg % self._definition['version'])

        self._populate_default_values()

        try:
            if do_validate:
                validate(self._definition, DATASET_DEFINITION_SCHEMA)
                if 'global_data' in definition:
                    dd = self.get_definition()
                    dd.validate()
        except ValidationError as ex:
            raise InvalidDataSetDefinition('INVALID_DATASET_DEFINITION', 'Error validating against schema: %s' % unicode(ex))
        except InvalidData as ex:
            raise InvalidDataSetDefinition('INVALID_GLOBAL_DATA', 'Error validating global data: %s' % unicode(ex))

        self._check_for_name_collisions()

    def get_definition(self):
        """Returns the definition

        :returns: The DataSetDefinition object
        :rtype: :class:`dataset.definition.definition.DataSetDefinition`
        """

        return DataSetDefinition(definition=self.get_dict())

    def get_dict(self):
        """Returns the dict of the definition
        """

        return self._definition

    def _populate_default_values(self):
        """Populates any missing JSON fields that have default values
        """

        if 'parameters' not in self._definition:
            self._definition['parameters'] = InterfaceV6().get_dict()
        else:
            self._definition['parameters'] = InterfaceV6(interface=self._definition['parameters']).get_dict()

        if 'global_parameters' not in self._definition:
            self._definition['global_parameters'] = InterfaceV6().get_dict()
        else:
            self._definition['global_parameters'] = InterfaceV6(interface=self._definition['global_parameters']).get_dict()


    def _check_for_name_collisions(self):
        """Ensures all global and regular parameter names are unique, and throws a
        :class:`data.dataset.exceptions.InvalidDataSetDefinition` if they are not unique.
        """

        names = []

        for file_dict in self._definition['parameters']['files']:
            names.append(file_dict['name'])
        for json_dict in self._definition['parameters']['json']:
            names.append(json_dict['name'])

        for file_dict in self._definition['global_parameters']['files']:
            names.append(file_dict['name'])
        for json_dict in self._definition['global_parameters']['json']:
            names.append(json_dict['name'])

        if len(names) != len(set(names)):
            raise InvalidDataSetDefinition('NAME_COLLISION_ERROR','Parameter names must be unique.' )
