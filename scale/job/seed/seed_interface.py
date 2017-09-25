"""Defines the interface for executing a job"""
from __future__ import unicode_literals

import glob
import json
import logging
import os
import re

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from job.configuration.configurators import normalize_env_var_name
from job.configuration.data.exceptions import InvalidData, InvalidConnection
from job.configuration.interface.exceptions import InvalidInterfaceDefinition
from job.configuration.interface.scale_file import ScaleFileDescription
from job.configuration.exceptions import MissingMount, MissingSetting
from job.configuration.results.exceptions import InvalidResultsManifest, OutputCaptureError
from job.configuration.results.results_manifest.results_manifest import ResultsManifest
from job.execution.container import SCALE_JOB_EXE_INPUT_PATH, SCALE_JOB_EXE_OUTPUT_PATH
from job.seed.metadata import SeedMetadata
from scheduler.vault.manager import secrets_mgr

logger = logging.getLogger(__name__)

SCHEMA_VERSION = '0.1.0'
MODE_RO = 'ro'
MODE_RW = 'rw'

JOB_INTERFACE_SCHEMA = {
  '$schema': 'http://json-schema.org/draft-04/schema#',
  'type': 'object',
  'additionalProperties': False,
  'properties': {
    'seedVersion': {
      'type': 'string',
      'pattern': '0.1.0'
    },
    'job': {
      'type': 'object',
      'additionalProperties': False,
      'properties': {
        'name': {
          'type': 'string',
          'pattern': '^[a-z0-9_-]+$'
        },
        'jobVersion': {
          'type': 'string',
          'pattern': '^(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)(-(0|[1-9][0-9]*|[0-9]*[a-zA-Z-][0-9a-zA-Z-]*)(\\.(0|[1-9][0-9]*|[0-9]*[a-zA-Z-][0-9a-zA-Z-]*))*)?(\\+[0-9a-zA-Z-]+(\\.[0-9a-zA-Z-]+)*)?$'
        },
        'packageVersion': {
          'type': 'string',
          'pattern': '^(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)(-(0|[1-9][0-9]*|[0-9]*[a-zA-Z-][0-9a-zA-Z-]*)(\\.(0|[1-9][0-9]*|[0-9]*[a-zA-Z-][0-9a-zA-Z-]*))*)?(\\+[0-9a-zA-Z-]+(\\.[0-9a-zA-Z-]+)*)?$'
        },
        'title': {
          'type': 'string'
        },
        'description': {
          'type': 'string'
        },
        'tags': {
          'type': 'array',
          'items': {
            'type': 'string'
          }
        },
        'maintainer': {
          'type': 'object',
          'additionalProperties': False,
          'properties': {
            'name': {
              'type': 'string'
            },
            'organization': {
              'type': 'string'
            },
            'email': {
              'type': 'string'
            },
            'url': {
              'type': 'string'
            },
            'phone': {
              'type': 'string'
            }
          },
          'required': [
            'name',
            'email'
          ]
        },
        'timeout': {
          'type': 'integer'
        },
        'resources': {
          'type': 'object',
          'additionalProperties': False,
          'properties': {
            'scalar': {
              'type': 'array',
              'items': {
                'type': 'object',
                'additionalProperties': False,
                'properties': {
                  'name': {
                    'type': 'string',
                    'pattern': '^[a-zA-Z_-]+$'
                  },
                  'value': {
                    'type': 'number'
                  },
                  'inputMultiplier': {
                    'type': 'number'
                  }
                },
                'required': [
                  'name',
                  'value'
                ]
              },
              'required': [
                'scalar'
              ]
            }
          }
        },
        'interface': {
          'type': 'object',
          'additionalProperties': False,
          'properties': {
            'command': {
              'type': 'string'
            },
            'inputs': {
              'type': 'object',
              'additionalProperties': False,
              'properties': {
                'files': {
                  'type': 'array',
                  'items': {
                    'type': 'object',
                    'additionalProperties': False,
                    'properties': {
                      'name': {
                        'type': 'string',
                        'pattern': '^[a-zA-Z_-]+$'
                      },
                      'required': {
                        'type': 'boolean',
                        'default': True
                      },
                      'mediaTypes': {
                        'type': 'array',
                        'items': {
                          'type': 'string'
                        }
                      },
                      'multiple': {
                        'type': 'boolean',
                        'default': False
                      }
                    },
                    'required': [
                      'name'
                    ]
                  }
                },
                'json': {
                  'type': 'array',
                  'items': {
                    'type': 'object',
                    'additionalProperties': False,
                    'properties': {
                      'name': {
                        'type': 'string',
                        'pattern': '^[a-zA-Z_-]+$'
                      },
                      'required': {
                        'type': 'boolean',
                        'default': True
                      },
                      'type': {
                        'type': 'string',
                        'enum': [
                          'array',
                          'boolean',
                          'integer',
                          'number',
                          'object',
                          'string'
                        ]
                      }
                    },
                    'required': [
                      'name',
                      'type'
                    ]
                  }
                }
              }
            },
            'outputs': {
              'type': 'object',
              'additionalProperties': False,
              'properties': {
                'files': {
                  'type': 'array',
                  'items': {
                    'type': 'object',
                    'additionalProperties': False,
                    'properties': {
                      'name': {
                        'type': 'string',
                        'pattern': '^[a-zA-Z_-]+$'
                      },
                      'mediaType': {
                        'type': 'string'
                      },
                      'pattern': {
                        'type': 'string'
                      },
                      'count': {
                        'type': 'string',
                        'default': '1',
                        'pattern': '^([0-9]+|\\*)$'
                      },
                      'required': {
                        'type': 'boolean',
                        'default': True
                      }
                    },
                    'required': [
                      'name',
                      'mediaType',
                      'pattern'
                    ]
                  }
                },
                'json': {
                  'type': 'array',
                  'items': {
                    'type': 'object',
                    'additionalProperties': False,
                    'properties': {
                      'name': {
                        'type': 'string',
                        'pattern': '^[a-zA-Z_-]+$'
                      },
                      'key': {
                        'type': 'string'
                      },
                      'type': {
                        'type': 'string',
                        'enum': [
                          'array',
                          'boolean',
                          'integer',
                          'number',
                          'object',
                          'string'
                        ]
                      },
                      'required': {
                        'type': 'boolean',
                        'default': True
                      }
                    },
                    'required': [
                      'name',
                      'type'
                    ]
                  }
                }
              }
            },
            'mounts': {
              'type': 'array',
              'items': {
                'type': 'object',
                'additionalProperties': False,
                'properties': {
                  'name': {
                    'type': 'string',
                    'pattern': '^[a-zA-Z_-]+$'
                  },
                  'path': {
                    'type': 'string'
                  },
                  'mode': {
                    'enum': [
                      'ro',
                      'rw'
                    ],
                    'default': 'ro'
                  }
                },
                'required': [
                  'name',
                  'path'
                ]
              }
            },
            'settings': {
              'type': 'array',
              'items': {
                'type': 'object',
                'additionalProperties': False,
                'properties': {
                  'name': {
                    'type': 'string',
                    'pattern': '^[a-zA-Z_-]+$'
                  },
                  'secret': {
                    'type': 'boolean',
                    'default': True
                  }
                },
                'required': [
                  'name'
                ]
              }
            }
          }
        },
        'errors': {
          'type': 'array',
          'items': {
            'type': 'object',
            'additionalProperties': False,
            'properties': {
              'code': {
                'type': 'integer'
              },
              'title': {
                'type': 'string'
              },
              'description': {
                'type': 'string'
              },
              'category': {
                'type': 'string',
                'default': 'job',
                'enum': [
                  'job',
                  'data'
                ]
              }
            },
            'required': [
              'code',
              'title'
            ]
          }
        }
      },
      'required': [
        'name',
        'jobVersion',
        'packageVersion',
        'title',
        'description',
        'maintainer',
        'timeout'
      ]
    }
  },
  'required': [
    'seedVersion',
    'job'
  ]
}


class SeedInterface(object):
    """Represents the interface defined by an algorithm developer to a Seed job"""

    def __init__(self, definition, do_validate=True):
        """Creates a seed interface from the given definition. If the definition is invalid, a
        :class:`job.configuration.interface.exceptions.InvalidInterfaceDefinition` exception will be thrown.

        :param definition: The interface definition
        :type definition: dict
        :param do_validate: Whether to perform validation on the JSON schema
        :type do_validate: bool
        """

        self.definition = definition

        # Tuples used for validation with other classes
        self._property_validation_dict = {}  # str->bool
        self._input_file_validation_dict = {}  # str->tuple
        self._output_file_validation_list = []

        self._output_file_manifest_dict = {}  # str->bool

        try:
            if do_validate:
                validate(definition, JOB_INTERFACE_SCHEMA)
        except ValidationError as validation_error:
            raise InvalidInterfaceDefinition(validation_error)

        self._populate_default_values()

        self._check_for_name_collisions()
        self._check_mount_name_uniqueness()

        self._validate_mount_paths()
        self._create_validation_dicts()

    def add_output_to_connection(self, output_name, job_conn, input_name):
        """Adds the given output from the interface as a new input to the given job connection

        :param output_name: The name of the output to add to the connection
        :type output_name: str
        :param job_conn: The job connection
        :type job_conn: :class:`job.configuration.data.job_connection.JobConnection`
        :param input_name: The name of the connection input
        :type input_name: str
        """

        output_data = self._get_output_data_item_by_name(output_name)
        if output_data:
            output_type = output_data['type']
            if output_type in ['file', 'files']:
                multiple = (output_type == 'files')
                optional = not output_data['required']
                media_types = []
                if 'media_type' in output_data and output_data['media_type']:
                    media_types.append(output_data['media_type'])
                # TODO: How do we want to handle down-stream partial handling? Setting to False presently
                job_conn.add_input_file(input_name, multiple, media_types, optional, False)

    def add_workspace_to_data(self, job_data, workspace_id):
        """Adds the given workspace ID to the given job data for every output in this job interface

        :param job_data: The job data
        :type job_data: :class:`job.configuration.data.job_data.JobData`
        :param workspace_id: The workspace ID
        :type workspace_id: int
        """

        for file_output_name in self.get_file_output_names():
            job_data.add_output(file_output_name, workspace_id)

    def get_command(self):
        """Gets the command
        :return: the command
        :rtype: str
        """

        return self.definition['command']

    def get_command_args(self):
        """Gets the command arguments
        :return: the command args
        :rtype: str
        """

        return self.definition['command_arguments']

    def get_interface(self):
        """Gets the interface for the Seed job

        :return: the interface object
        :rtype: dict
        """

        return self.definition['job']['interface']

    def get_output_files(self):
        """Gets the list of output files defined in the interface

        Commonly used when matching globs to capture output files

        :return: the output file definitions for job
        :rtype: list
        """

        return self.get_interface()['outputs']['files']

    def get_scalar_resources(self):
        """Gets the scalar resources defined the Seed job

        :return: the scalar resources required by job
        :rtype: list
        """

        return self.definition['job']['resources']['scalar']

    def get_maintainer(self):
        """Gets the maintainer details for the Seed job

        :return: the maintainer details of job
        :rtype: dict
        """

        return self.definition['job']['maintainer']

    def get_errors(self):
        """Get the error mapping defined for the Seed job

        :return: the error codes mapped for job
        :rtype: list
        """

        return self.definition['job']['errors']

    def get_dict(self):
        """Returns the internal dictionary that represents this job interface

        :returns: The internal dictionary
        :rtype: dict
        """

        return self.definition

    def get_file_output_names(self):
        """Returns the output parameter names for all file outputs

        :return: The file output parameter names
        :rtype: list of str
        """

        names = []
        for output_data in self.definition['output_data']:
            if output_data['type'] in ['file', 'files']:
                names.append(output_data['name'])
        return names

    def perform_post_steps(self, job_exe, job_data, stdoutAndStderr):
        """Stores the files or JSON output of job and deletes any working directories

        :param job_exe: The job execution model with related job and job_type fields
        :type job_exe: :class:`job.models.JobExecution`
        :param job_data: The job data
        :type job_data: :class:`job.configuration.data.job_data.JobData`
        :param stdoutAndStderr: the standard out from the job execution
        :type stdoutAndStderr: str
        :return: A tuple of the job results and the results manifest generated by the job execution
        :rtype: (:class:`job.configuration.results.job_results.JobResults`,
            :class:`job.configuration.results.results_manifest.results_manifest.ResultsManifest`)
        """

        # For compliance with Seed we must capture all files directly from the output directory.
        # The capture expressions can be found within interface.outputs.files.pattern


        files_to_store = {}

        for output_file in self.get_output_files():
            # lookup by pattern
            path_pattern = os.path.join(SCALE_JOB_EXE_OUTPUT_PATH, output_file['pattern'])
            results = glob.glob(path_pattern)

            # Handle required validation
            if output_file['required'] and len(results) == 0:
                raise OutputCaptureError("No glob match for pattern '%s' defined for required output files"
                                         " key '%s'." % (output_file['pattern'], output_file['name']))

            # Check against count to verify we are matching the files as defined.
            if output_file['count'] is not '*':
                count = int(output_file['count'])
                if len(results) is not count:
                    raise OutputCaptureError("Pattern matched %i, which does not match the output count of %i "
                                             "identified in interface." % (len(results), count))

            # For files that are detected, check to see if there is side-car metadata files
            for matched_file in results:
                metadata_file = os.path.join(matched_file, job.seed.metadata.METADATA_SUFFIX)
                with open(metadata_file) as metadata_file_handle:
                    metadata = SeedMetadata(metadata_file_handle.read())
                    metadata.get_geometry()
                    metadata.get_time()


        manifest_data = {}
        path_to_manifest_file = os.path.join(SCALE_JOB_EXE_OUTPUT_PATH, 'results_manifest.json')
        if os.path.exists(path_to_manifest_file):
            logger.info('Opening results manifest...')
            with open(path_to_manifest_file, 'r') as manifest_file:
                manifest_data = json.loads(manifest_file.read())
                logger.info('Results manifest:')
                logger.info(manifest_data)
        else:
            logger.info('No results manifest found')

        results_manifest = ResultsManifest(manifest_data)
        stdout_files = self._get_artifacts_from_stdout(stdoutAndStderr)
        results_manifest.add_files(stdout_files)

        results_manifest.validate(self._output_file_manifest_dict)

        # For files that are detected, check to see if there is side-car metadata files
        files_to_store = {}
        for manifest_file_entry in results_manifest.get_files():
            param_name = manifest_file_entry['name']

            media_type = None
            output_data_item = self._get_output_data_item_by_name(param_name)
            if output_data_item:
                media_type = output_data_item.get('media_type')

            msg = 'Output %s has invalid/missing file path "%s"'
            if 'file' in manifest_file_entry:
                file_entry = manifest_file_entry['file']
                if not os.path.isfile(file_entry['path']):
                    raise InvalidResultsManifest(msg % (param_name, file_entry['path']))
                if 'geo_metadata' in file_entry:
                    files_to_store[param_name] = (file_entry['path'], media_type, file_entry['geo_metadata'])
                else:
                    files_to_store[param_name] = (file_entry['path'], media_type)
            elif 'files' in manifest_file_entry:
                file_tuples = []
                for file_entry in manifest_file_entry['files']:
                    if not os.path.isfile(file_entry['path']):
                        raise InvalidResultsManifest(msg % (param_name, file_entry['path']))
                    if 'geo_metadata' in file_entry:
                        file_tuples.append((file_entry['path'], media_type, file_entry['geo_metadata']))
                    else:
                        file_tuples.append((file_entry['path'], media_type))
                files_to_store[param_name] = file_tuples

        # Capture any JSON output provided in seed.ouputs.json
        job_data_parse_results = {}  # parse results formatted for job_data
        for parse_result in results_manifest.get_parse_results():
            filename = parse_result['filename']
            assert filename not in job_data_parse_results
            geo_metadata = parse_result.get('geo_metadata', {})
            geo_json = geo_metadata.get('geo_json', None)
            data_started = geo_metadata.get('data_started', None)
            data_ended = geo_metadata.get('data_ended', None)
            data_types = parse_result.get('data_types', [])
            new_workspace_path = parse_result.get('new_workspace_path', None)
            if new_workspace_path:
                new_workspace_path = os.path.join(new_workspace_path, filename)
            job_data_parse_results[filename] = (geo_json, data_started, data_ended, data_types, new_workspace_path)

        job_data.save_parse_results(job_data_parse_results)
        return (job_data.store_output_data_files(files_to_store, job_exe), results_manifest)

    def perform_pre_steps(self, job_data, job_environment):
        """Performs steps prep work before a job can actually be run.  This includes downloading input files.
        This returns the command that should be executed for these parameters.
        :param job_data: The job data
        :type job_data: :class:`job.configuration.data.job_data.JobData`
        :param job_environment: The job environment
        :type job_environment: dict
        """
        retrieve_files_dict = self._create_retrieve_files_dict()
        job_data.setup_job_dir(retrieve_files_dict)

    def populate_env_vars_arguments(self, param_replacements):
        """Populates the environment variables with the requested values.

        :param param_replacements: The parameter replacements
        :type param_replacements: dict

        :return: env_vars populated with values
        :rtype: dict
        """

        env_vars = self.definition['env_vars']
        env_vars = self._replace_env_var_parameters(env_vars, param_replacements)

        return env_vars

    def validate_connection(self, job_conn):
        """Validates the given job connection to ensure that the connection will provide sufficient data to run a job
        with this interface

        :param job_conn: The job data
        :type job_conn: :class:`job.configuration.data.job_connection.JobConnection`
        :returns: A list of warnings discovered during validation.
        :rtype: list[:class:`job.configuration.data.job_data.ValidationWarning`]

        :raises :class:`job.configuration.data.exceptions.InvalidConnection`: If there is a configuration problem.
        """

        warnings = []
        warnings.extend(job_conn.validate_input_files(self._input_file_validation_dict))
        warnings.extend(job_conn.validate_properties(self._property_validation_dict))
        # Make sure connection has a workspace if the interface has any output files
        if self._output_file_validation_list and not job_conn.has_workspace():
            raise InvalidConnection('No workspace provided for output files')
        return warnings

    def validate_data(self, job_data):
        """Ensures that the job_data matches the job_interface description

        :param job_data: The job data
        :type job_data: :class:`job.configuration.data.job_data.JobData`
        :returns: A list of warnings discovered during validation.
        :rtype: list[:class:`job.configuration.data.job_data.ValidationWarning`]

        :raises :class:`job.configuration.data.exceptions.InvalidData`: If there is a configuration problem.
        """

        warnings = []
        warnings.extend(job_data.validate_input_files(self._input_file_validation_dict))
        warnings.extend(job_data.validate_properties(self._property_validation_dict))
        warnings.extend(job_data.validate_output_files(self._output_file_validation_list))
        return warnings

    def validate_populated_mounts(self, exe_configuration):
        """Ensures that all required mounts are defined in the execution configuration

        :param exe_configuration: The execution configuration
        :type exe_configuration: :class:`job.configuration.json.execution.exe_config.ExecutionConfiguration`
        """

        for name, mount_volume in exe_configuration.get_mounts('main').items():
            if mount_volume is None:
                raise MissingMount('Required mount %s was not provided' % name)

    def validate_populated_settings(self, exe_configuration):
        """Ensures that all required settings are defined in the execution configuration

        :param exe_configuration: The execution configuration
        :type exe_configuration: :class:`job.configuration.json.execution.exe_config.ExecutionConfiguration`
        """

        for name, value in exe_configuration.get_settings('main').items():
            if value is None:
                raise MissingSetting('Required setting %s was not provided' % name)

    def _check_for_env_var_collisions(self):
        """Ensures all the environmental variable names are unique, and throws a
        :class:`job.configuration.interface.exceptions.InvalidInterfaceDefinition` if they are not unique.

        Per Seed specification for implementors we must validate that all reserved keywords, settings
        and inputs are unique as they are ultimately injected as environment variables.
        """

        # Include reserved keywords
        env_vars = ["OUTPUT_DIR"]

        env_vars += [normalize_env_var_name(setting['name']) for setting in self._interface['settings']]
        env_vars += [normalize_env_var_name(files['name']) for files in self._interface['inputs']['files']]
        env_vars += [normalize_env_var_name(json['name']) for json in self._interface['inputs']['json']]
        env_vars += [normalize_env_var_name('ALLOCATED_' + resource['name']) for resource in self._scalar_resources]

        if len(env_vars) != len(set(env_vars)):
            raise InvalidInterfaceDefinition('Collisions are not allowed between reserved keywords, resources, settings'
                                             'and input names.')

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

    def _check_mount_name_uniqueness(self):
        """Ensures all the mount names are unique, and throws a
        :class:`job.configuration.interface.exceptions.InvalidInterfaceDefinition` if they are not unique
        """

        mounts = []
        for mount in self._interface['mounts']:
            mounts.append(mount['name'])

        if len(mounts) != len(set(mounts)):
            raise InvalidInterfaceDefinition('Mount names must be unique.')

    def _create_validation_dicts(self):
        """Creates the validation dicts required by job_data to perform its validation"""
        for input_data in self.definition['input_data']:
            name = input_data['name']
            required = input_data['required']
            if input_data['type'] == 'property':
                self._property_validation_dict[name] = required
            elif input_data['type'] == 'file':
                file_desc = ScaleFileDescription()
                for media_type in input_data['media_types']:
                    file_desc.add_allowed_media_type(media_type)
                self._input_file_validation_dict[name] = (required, False, file_desc)
            elif input_data['type'] == 'files':
                file_desc = ScaleFileDescription()
                for media_type in input_data['media_types']:
                    file_desc.add_allowed_media_type(media_type)
                self._input_file_validation_dict[name] = (required, True, file_desc)

        for ouput_data in self.definition['output_data']:
            output_type = ouput_data['type']
            if output_type in ['file', 'files']:
                name = ouput_data['name']
                required = ouput_data['required']
                self._output_file_validation_list.append(name)
                self._output_file_manifest_dict[name] = (output_type == 'files', required)

    @staticmethod
    def _get_artifacts_from_stdout(stdout):
        """Parses stdout looking for artifacts of the form ARTIFACT:<ouput_name>:<output_path>
        :param stdout: the standard out from the job execution
        :type stdout: str

        :return: a list of artifacts that were found by parsing stdout
        :rtype: a list of artifact dicts.  each artifact dict has a "name" and either a "path" or "paths
        see job.configuration.results.manifest.RESULTS_MANIFEST_SCHEMA
        """
        artifacts_found = {}
        artifacts_pattern = '^ARTIFACT:([^:]*):(.*)'
        for artifact_match in re.findall(artifacts_pattern, stdout, re.MULTILINE):
            artifact_name = artifact_match[0]
            artifact_path = artifact_match[1]
            if artifact_name in artifacts_found:
                paths = []
                if 'paths' in artifacts_found[artifact_name]:
                    paths = artifacts_found[artifact_name]['paths']
                else:
                    paths = [artifacts_found[artifact_name]['path']]
                    artifacts_found[artifact_name].pop('path')
                paths.append(artifact_path)
                artifacts_found[artifact_name]['paths'] = paths
            else:
                artifacts_found[artifact_name] = {'name': artifact_name, 'path': artifact_path}
        return artifacts_found.values()

    @staticmethod
    def _get_one_file_from_directory(dir_path):
        """Checks a directory for one and only one file.  If there is not one file, raise a
        :exception:`job.configuration.data.exceptions.InvalidData`.  If there is one file, this method
        returns the full path of that file.

        :param dir_path: The directories path
        :type dir_path: string
        :return: The path to the one file in a given directory
        :rtype: str
        """
        entries_in_dir = os.listdir(dir_path)
        if len(entries_in_dir) != 1:
            raise InvalidData('Unable to create run command.  Expected one file in %s', dir_path)
        return os.path.join(dir_path, entries_in_dir[0])

    def _get_output_data_item_by_name(self, data_item_name):
        """gets an output data item with the given name
        :param data_item_name: The name of the data_item_name
        :type data_item_name: str
        """

        for output_data in self.definition['output_data']:
            if data_item_name == output_data['name']:
                return output_data

    def _get_settings_values(self, settings, exe_configuration, job_type, censor):
        """
        :param settings: The settings
        :type settings: dict
        :param exe_configuration: The execution configuration
        :type exe_configuration: :class:`job.configuration.json.execution.exe_config.ExecutionConfiguration`
        :param job_type: The job type definition
        :type job_type: :class:`job.models.JobType`
        :param censor: Whether to censor secrets
        :type censor: bool
        :return: settings name and the value to replace it with
        :rtype: dict
        """

        config_settings = exe_configuration.get_dict()
        param_replacements = {}
        secret_settings = {}

        # Isolate the job_type settings and convert to list
        for task_dict in config_settings['tasks']:
            if task_dict['type'] == 'main':
                config_settings_dict = task_dict['settings']

        for setting in settings:
            setting_name = setting['name']
            setting_is_secret = setting['secret']

            if setting_is_secret:
                job_index = job_type.get_secrets_key()

                if not secret_settings:
                    secret_settings = secrets_mgr.retrieve_job_type_secrets(job_index)

                if setting_name in secret_settings.keys():
                    if censor:
                        settings_value = '*****'
                    else:
                        settings_value = secret_settings[setting_name]
                    param_replacements[setting_name] = settings_value
                else:
                    param_replacements[setting_name] = ''
            else:
                if setting_name in config_settings_dict:
                    param_replacements[setting_name] = config_settings_dict[setting_name]
                else:
                    param_replacements[setting_name] = ''

        return param_replacements

    def _populate_default_values(self):
        """Goes through the definition and fills in any missing default values"""
        if 'version' not in self.definition:
            self.definition['version'] = SCHEMA_VERSION

        # Populate placeholder for interface if undefined
        if 'interface' not in self.definition:
            self.definition['interface'] = {}

        # Populate placeholder for errors
        if 'errors' not in self.definition:
            self.definition['errors'] = []

        self._populate_resource_defaults()
        self._populate_inputs_defaults()
        self._populate_outputs_defaults()
        self._populate_mounts_defaults()
        self._populate_settings_defaults()

    def _populate_mounts_defaults(self):
        """Populates the default values for any missing mounts values"""

        # Populate placeholder for mounts
        if 'mounts' not in self.definition['interface']:
            self.definition['interface']['mounts'] = []

        for mount in self.definition['interface']['mounts']:
            if 'mode' not in mount:
                mount['mode'] = MODE_RO

    def _populate_settings_defaults(self):
        """populates the default values for any missing settings values"""

        if 'settings' not in self.definition:
            self.definition['settings'] = []

        for setting in self.definition['settings']:
            if 'required' not in setting:
                setting['required'] = True

            if 'secret' not in setting:
                setting['secret'] = False

    def _populate_inputs_defaults(self):
        """populates the default values for any missing inputs values"""

        # Populate placeholders for inputs
        if 'inputs' not in self.definition['interface']:
            self.definition['interface']['inputs'] = {}
        if 'files' not in self.definition['interface']['inputs']:
            self.definition['interface']['inputs']['files'] = []
        if 'json' not in self.definition['interface']['inputs']:
            self.definition['interface']['inputs']['json'] = []

        for input_file in self.definition['inputs']['files']:
            if 'required' not in input_file:
                input_file['required'] = True
            if 'mediaType' not in input_file:
                input_file['media_types'] = []
            if 'multiple' not in input_file:
                input_file['multiple'] = False
            # TODO: Address partial functionality through extended configuration outside of the Seed interface

        for input_json in self.definition['inputs']['json']:
            if 'required' not in input_json:
                input_json['required'] = True

    def _populate_outputs_defaults(self):
        """populates the default values for any missing outputs values"""

        # Populate placeholders for outputs
        if 'outputs' not in self.definition['interface']:
            self.definition['interface']['ouputs'] = {}
        if 'files' not in self.definition['interface']['ouputs']:
            self.definition['interface']['ouputs']['files'] = []
        if 'json' not in self.definition['interface']['ouputs']:
            self.definition['interface']['ouputs']['json'] = []

        for output_file in self.definition['interface']['outputs']:
            if 'count' not in output_file:
                output_file['count'] = '1'
            if 'required' not in output_file:
                output_file['required'] = True

        for output_json in self.definition['interface']['outputs']:
            if 'required' not in output_json:
                output_json['required'] = True

    def _populate_resource_defaults(self):
        """populates the default values for any missing shared_resource values"""

        # Populate placeholders for scalar resources
        if 'resources' not in self.definition:
            self.definition['resources'] = {}
        if 'scalar' not in self.definition['resources']:
            self.definition['resources']['scalar'] = []

        for scalar in self.definition['resources']['scalar']:
            if 'required' not in scalar:
                scalar['required'] = True

    def _validate_mount_paths(self):
        """Ensures that all mount paths are valid

        :raises :class:`job.configuration.data.exceptions.InvalidInterfaceDefinition`: If a mount path is invalid
        """

        for mount in self.definition['mounts']:
            name = mount['name']
            path = mount['path']
            if not os.path.isabs(path):
                raise InvalidInterfaceDefinition('%s mount must have an absolute path' % name)
