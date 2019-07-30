"""Manages the DataSet definition schema"""
from __future__ import unicode_literals

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from data.data.json.data_v6 import DATA_SCHEMA, DataV6
from data.interface.json.interface_v6 import INTERFACE_SCHEMA, InterfaceV6
from dataset.exceptions import InvalidDataSetDefinition
from dataset.definition.definition import DataSetDefinition

SCHEMA_VERSION = '6'

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
    :type definition: :class:`??`
    :returns: The v6 dataset definition JSON
    :rtype: :class:`dataset.DataSetDefinition
    """

    def_dict = {
        'version': SCHEMA_VERSION,
        'global_parameters': definition['global_parameters'],
        'global_data': definition['global_data'],
        'parameters': definition['parameters']
    }

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

        self._populate_default_values()
        
        self._check_for_name_collisions()

        try:
            if do_validate:
                validate(self._definition, DATASET_DEFINITION_SCHEMA)
                dd = self.get_definition()
                gd = DataV6(data=definition['global_data'], do_validate=True).get_data()
                dd.validate(data=gd)
        except ValidationError as ex:
            raise InvalidDataSetDefinition('INVALID_DATASET_DEFINITION', 'Error validating against schema: %s' % unicode(ex))

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

        if 'parameter' not in self._definition:
            self._definition['parameter'] = InterfaceV6().get_dict()

    def _check_for_name_collisions(self):
        """Ensures all global and regular parameter names are unique, and throws a
        :class:`data.dataset.exceptions.InvalidDataSetDefinition` if they are not unique.
        """

        names = []

        names.extend(self._definition['parameters'])
        
        names += [global_param['name'] for global_param in self._definition['global_parameters']]

        if len(names) != len(set(names)):
            raise InvalidDataSetDefinition('NAME_COLLISION_ERROR','Parameter names must be unique.' )
