"""Manages the DataSetMember definition schema"""
from __future__ import unicode_literals

from jsonschema import validate
from jsonschema.exceptions import ValidationError
from datasets.exceptions import InvalidDataSetMemberDefinition

SCHEMA_VERSION = '6'
DATASET_MEMBER_SCHEMA = {
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

class DataSetMemberDefinition(object):
    """
    Represents the definition of a DataSet object
    
    :keyword description: The description of the data set (optional)
    :type description: :class:`django.db.models.CharField`
    """
    def __init__(self, definition=None, do_validate=True):
        """Constructor
        """
        title = None
        description = None
        created_time = None

        if not definition:
            definition = {}
        self._definition = definition
        
        if 'version' not in self._definition:
            self._definition['version'] = SCHEMA_VERSION

        self._populate_default_values()
        
        try:
            if do_validate:
                validate(definition, DATASET_MEMBER_SCHEMA)
        except ValidationError as validation_error:
            raise InvalidDataSetMemberDefinition('JSON_VALIDATION_ERROR', 'Error validating against schema: %s' % validation_error)
            
    def get_dict(self):
        """Returns the dict of the definition
        """

        return self._definition

    def _populate_default_values(self):
        """Populates any missing required valudes with defaults
        """
        