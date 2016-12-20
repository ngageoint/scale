"""Defines the interface for executing a job"""
from __future__ import unicode_literals

import logging
import os

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from job.configuration.interface import job_interface_1_0 as previous_interface
from job.configuration.interface.exceptions import InvalidInterfaceDefinition
from job.execution.container import SCALE_JOB_EXE_INPUT_PATH


logger = logging.getLogger(__name__)

SCHEMA_VERSION = '1.1'

JOB_INTERFACE_SCHEMA = {
    'type': 'object',
    'required': ['command', 'command_arguments'],
    'additionalProperties': False,
    'properties': {
        'version': {
            'description': 'version of the job_interface schema',
            "default": SCHEMA_VERSION,
            "type": "string"
        },
        'command': {
            'description': 'The command that will be called.  Uses variable replacement',
            'type': 'string',
        },
        'command_arguments': {
            'description': 'The arguments that are passed to the command',
            'type': 'string',
        },
        'input_data': {
            'type': 'array',
            'items': {
                '$ref': '#/definitions/input_data_item',
            },
        },
        'output_data': {
            'type': 'array',
            'items': {
                '$ref': '#/definitions/output_data_item',
            },
        },
        'shared_resources': {
            'type': 'array',
            'items': {
                '$ref': '#/definitions/shared_resource',
            },
        },
    },
    'definitions': {
        'input_data_item': {
            'type': 'object',
            'required': ['name', 'type'],
            'additionalProperties': False,
            'properties': {
                'name': {
                    'type': 'string',
                    'pattern': '^[a-zA-Z0-9\\-_ ]{1,255}$',
                },
                'type': {
                    'type': 'string',
                    'enum': ['file', 'files', 'property'],
                },
                'required': {
                    'type': 'boolean',
                },
                'partial': {
                    'description': 'file/files type only flag indicating input may be mounted vs downloaded',
                    'type': 'boolean'
                },
                'media_types': {
                    'type': 'array',
                },
            },
        },
        'output_data_item': {
            'type': 'object',
            'required': ['name', 'type'],
            'additionalProperties': False,
            'properties': {
                'name': {
                    'type': 'string',
                    'pattern': '^[a-zA-Z0-9\\-_ ]{1,255}$',
                },
                'type': {
                    'type': 'string',
                    'enum': ['file', 'files'],
                },
                'required': {
                    'type': 'boolean',
                },
                'media_type': {
                    'type': 'string',
                },
            },
        },
        'shared_resource': {
            'type': 'object',
            'required': ['name', 'type'],
            'additionalProperties': False,
            'properties': {
                'name': {
                    'type': 'string',
                },
                'type': {
                    'type': 'string',
                },
                'required': {
                    'type': 'boolean',
                },
            },
        },
    },
}


class JobInterface(previous_interface.JobInterface):
    """Represents the interface for executing a job"""

    def __init__(self, definition):
        """Creates a job interface from the given definition. If the definition is invalid, a
        :class:`job.configuration.interface.exceptions.InvalidInterfaceDefinition` exception will be thrown.

        :param definition: The interface definition
        :type definition: dict
        """
        self.definition = definition
        self._param_names = set()

        # Tuples used for validation with other classes
        self._property_validation_dict = {}  # str->bool
        self._input_file_validation_dict = {}  # str->tuple
        self._output_file_validation_list = []

        self._output_file_manifest_dict = {}  # str->bool

        if self.definition['version'] != SCHEMA_VERSION:
            self.convert_interface(definition)

        try:
            validate(definition, JOB_INTERFACE_SCHEMA)
        except ValidationError as validation_error:
            raise InvalidInterfaceDefinition(validation_error)

        self._populate_default_values()

        self._check_param_name_uniqueness()
        self._validate_command_arguments()
        self._create_validation_dicts()

    @staticmethod
    def convert_interface(interface):
        """Convert the previous Job interface schema to the 1.1 schema

        :param interface: The previous interface
        :type interface: dict
        :return: converted interface
        :rtype: dict
        """
        previous = previous_interface.JobInterface(interface)

        converted = previous.get_dict()

        converted['version'] = SCHEMA_VERSION

        if 'input_data' in converted:
            for inputs in converted['input_data']:
                if inputs['type'] in ('file', 'files'):
                    # Default value should be False for partial
                    inputs['partial'] = False

        return converted

    def _create_retrieve_files_dict(self):
        """creates parameter folders and returns the dict needed to call
        :classmethod:`job.configuration.data.job_data.JobData.retrieve_files_dict`

        :return: a dictionary representing the files to retrieve
        :rtype:  dist of str->tuple with input_name->(is_multiple, input_path)
        """

        retrieve_files_dict = {}
        for input_data in self.definition['input_data']:
            input_name = input_data['name']
            input_type = input_data['type']
            if input_type in ['file', 'files']:
                is_multiple = input_type == 'files'
                partial = input_data['partial']
                input_path = os.path.join(SCALE_JOB_EXE_INPUT_PATH, input_name)
                retrieve_files_dict[input_name] = (is_multiple, input_path, partial)
        return retrieve_files_dict

    def _populate_default_values(self):
        """Goes through the definition and fills in any missing default values"""
        if 'version' not in self.definition:
            self.definition['version'] = SCHEMA_VERSION
        if 'input_data' not in self.definition:
            self.definition['input_data'] = []
        if 'shared_resources' not in self.definition:
            self.definition['shared_resources'] = []
        if 'output_data' not in self.definition:
            self.definition['output_data'] = []

        self._populate_input_data_defaults()
        self._populate_resource_defaults()
        self._populate_output_data_defaults()

    def _populate_input_data_defaults(self):
        """populates the default values for any missing input_data values"""
        for input_data in self.definition['input_data']:
            if 'required' not in input_data:
                input_data['required'] = True
            if input_data['type'] in ['file', 'files'] and 'media_types' not in input_data:
                input_data['media_types'] = []
            if input_data['type'] in ['file', 'files'] and 'partial' not in input_data:
                input_data['partial'] = False

    def _populate_output_data_defaults(self):
        """populates the default values for any missing output_data values"""
        for output_data in self.definition['output_data']:
            if 'required' not in output_data:
                output_data['required'] = True

    def _populate_resource_defaults(self):
        """populates the default values for any missing shared_resource values"""
        for shared_resource in self.definition['shared_resources']:
            if 'required' not in shared_resource:
                shared_resource['required'] = True
