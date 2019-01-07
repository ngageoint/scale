"""Manages the DataSetFile definition schema"""
from __future__ import unicode_literals

from jsonschema import validate
from jsonschema.exceptions import ValidationError
from datasets.exceptions import InvalidDataSetFileDefinition

SCHEMA_VERSION = '6'
DATASET_FILE_SCHEMA = {
    'type': 'object',
    'required': ['definition'],
    'additionalProperties': False,
    'properties': {
        'definition': {
            'description': 'The data',
            'type': 'object',
        }
    }
}

class DataSetFileDefinition(object):
    """
    Represents the definition of a DataSetFile object
    
    
    """
    def __init__(self, definition=None, do_validate=True):
        """Constructor
        """
        
        if not definition:
            definition = {}
        self._definition = definition
        
        if 'version' not in self._definition:
            self._definition['version'] = SCHEMA_VERSION

        self._populate_default_values()

        try:
            if do_validate:
                validate(definition, DATASET_FILE_SCHEMA)
        except ValidationError as validation_error:
            raise InvalidDataSetFileDefinition('JSON_VALIDATION_ERROR', 'Error validating against schema: %s' % validation_error)

    def get_dict(self):
        """Returns the dict of the definition
        """

        return self._definition

    def _populate_default_values(self):
        """Populates any missing required valudes with defaults
        """