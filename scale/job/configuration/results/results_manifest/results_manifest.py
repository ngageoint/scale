'''This module is concerned with the scale output manifest. Scale jobs are expected to produce an output manifest.
Scale needs to parse this manifest to bring the information into the system. The output files should match
the job interface
'''

import copy
import logging

from jsonschema import validate
from jsonschema.exceptions import ValidationError

import job.configuration.results.results_manifest.results_manifest_1_0 as previous_manifest
from job.configuration.results.exceptions import InvalidResultsManifest,\
    ResultsManifestAndInterfaceDontMatch

logger = logging.getLogger(__name__)

MANIFEST_VERSION = '1.1'

RESULTS_MANIFEST_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "version": {
            "description": "version of the results_manifest schema",
            "default": MANIFEST_VERSION,
            "type": "string"
        },
        "output_data": {
            "description": "The files that should be ingested into the system",
            "default": [],
            "type": "array",
            "items": {"$ref": "#/definitions/output_data"}
        },
        "parse_results": {
            "description": "meta-data associated with parsed input files",
            "default": [],
            "type": "array",
            "items": {"$ref": "#/definitions/parse_results"}
        },
        "info": {
            "type": "array",
            "default": []  # TODO:define info schema
        },
        "errors": {
            "type": "array",
            "default": []  # TODO:define errors schema
        }
    },
    "definitions": {
        "output_data": {
            "description": "An output file or files.  The parameter is expected to match the output_interface",
            "type": "object",
            "required": ["name"],
            "properties": {
                "name": {
                    "type": "string"
                },
                "file": {
                    "type": "object",
                    "required": ["path"],
                    "properties": {
                        "path": {
                            "type": "string"
                        },
                        "geo_metadata": {
                            "type": "object",
                            "properties": {
                                "data_started": {
                                    "type": "string"
                                },
                                "data_ended": {
                                    "type": "string"
                                },
                                "geo_json": {
                                    "type": "object"
                                }
                            }
                        }
                    }
                },
                "files": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["path"],
                        "properties": {
                            "path": {
                                "type": "string"
                            },
                            "geo_metadata": {
                                "type": "object",
                                "properties": {
                                    "data_started": {
                                        "type": "string"
                                    },
                                    "data_ended": {
                                        "type": "string"
                                    },
                                    "geo_json": {
                                        "type": "object"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "parse_results": {
            "description": "A geojson file associated with an input to the job",
            "type": "object",
            "required": ["filename"],
            "properties": {
                "filename": {
                    "type": "string"
                },
                "new_workspace_path": {
                    "type": "string"
                },
                "data_types": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                },
                "geo_metadata": {
                    "type": "object",
                    "properties": {
                        "data_started": {
                           "type": "string"
                        },
                        "data_ended": {
                            "type": "string"
                        },
                        "geo_json": {
                            "type": "object"
                        }
                    }
                }
            }
        }
    }
}


class ResultsManifest(object):
    '''Represents the interface for executing a job
    '''

    def __init__(self, json_manifest=None):
        '''Creates a result manifest from the json_manifest
        :param json_manifest: a dict in the format described by RESULTS_MANIFEST_SCHEMA
        :type json_manifest: dict
        '''

        if json_manifest is None:
            json_manifest = {}

        if u'version' in json_manifest:
            version = json_manifest[u'version']
        else:
            version = MANIFEST_VERSION

        if version != MANIFEST_VERSION:
            json_manifest = self._convert_schema(json_manifest)

        self._json_manifest = json_manifest

        try:
            validate(json_manifest, RESULTS_MANIFEST_SCHEMA)
        except ValidationError as validation_error:
            raise InvalidResultsManifest(validation_error)

        self._populate_defaults()
        self._validate_manifest()

    def _convert_schema_files_to_output_data(self, files):
        '''Convert the files section of the 1.0 manifest schema to the new 1.1 output_data

        :param files: The version 1.0 files portion of the manifest
        :type files: dict
        :return: converted output_data
        :rtype: dict
        '''
        output_data = []
        for product_info in files:
            converted_product = dict()
            converted_product[u'name'] = product_info[u'name']

            if u'path' in product_info:
                file_info = dict()
                file_info[u'path'] = product_info[u'path']
                converted_product['file'] = file_info
            elif u'paths' in product_info:
                files_info = []
                paths = product_info[u'paths']
                for path in paths:
                    file_info = dict()
                    file_info[u'path'] = path
                    files_info.append(file_info)

                converted_product[u'files'] = files_info

            output_data.append(converted_product)
        return output_data

    def _convert_schema(self, json_manifest):
        '''Convert the 1.0 manifest schema to the new 1.1 manifest schema

        :param json_manifest: The version 1.0 manifest
        :type json_manifest: dict
        :return: converted manifest
        :rtype: dict
        '''
        # Convert manifest from the previous version
        previous = previous_manifest.ResultsManifest(json_manifest)
        previous_json = previous.get_json_dict()

        converted = dict()
        converted[u'version'] = MANIFEST_VERSION

        if u'parse_results' in previous_json:
            converted[u'parse_results'] = previous_json[u'parse_results']
        if u'info' in previous_json:
            converted[u'info'] = previous_json[u'info']
        if u'errors' in previous_json:
            converted[u'errors'] = previous_json[u'errors']

        if u'files' in previous_json:
            output_data = self._convert_schema_files_to_output_data(previous_json[u'files'])
            converted[u'output_data'] = output_data
        return converted

    def get_json_dict(self):
        '''Return the json dictionary associated with this manifest

        :return: json dict representing this manifest
        :rtype: dict
        '''
        return self._json_manifest

    def add_files(self, files_array):
        '''adds the files to the manifest if they are not already in the manifest.  If there is already an entry
        for that file name it will be ignored
        :param files_array: an array of files that should be added to the manifest
        :type files_array: an array of the format RESULTS_MANIFEST_SCHEMA["definitions"]["files"]
        '''
        filenames = set()
        for manifest_file_entry in self._json_manifest[u'output_data']:
            filenames.add(manifest_file_entry[u'name'])

        files_to_add = []
        for new_file_entry in files_array:
            new_entry_name = new_file_entry[u'name']
            if new_entry_name not in filenames:
                filenames.add(new_entry_name)
                files_to_add.append(new_file_entry)

        if len(files_to_add):
            output_data = self._convert_schema_files_to_output_data(files_to_add)
            self._json_manifest[u'output_data'].extend(output_data)

    def get_files(self):
        '''gets the output files associated with this manifest
        :return: an array of dictionaries.  Each dictionary describes a file in the manifest.
        The format of the dict is described
        by results_manifest.RESULTS_MANIFEST_SCHEMA["definitions"]["files"]
        :rtype: array of dict'''

        return self._json_manifest[u'output_data']

    def get_parse_results(self):
        '''gets the parsed input files associated with this manifest
        :return: an array of dictionaries.  Each dictionary describes the location of a
        geojson associated with an input filein the manifest. The format of the dict is descibed by
        results_manifest.RESULTS_MANIFEST_SCHEMA["definitions"]["parse_results"]
        :rtype: array of dict'''
        return self._json_manifest[u'parse_results']

    def validate(self, output_file_definitions):
        '''Validates the results manifest against given output file definitions.  Throws a
        :class `job.configuration.results.exceptions.ResultsManifestAndInterfaceDontMatch`: if the
        manifest doesn't match the outputs.  This does not validate that the parse_data matches the job
        data inputs.
        :param output_file_definitions: A dictionary with each output param name mapped to a tuple with
        (is_multiple (bool), required(bool))
        :type output_file_definitions: dict of tuples
        '''

        untrimmed_files = self._json_manifest[u'output_data']
        self._trim(output_file_definitions)

        file_entry_map = {}
        for manifest_file_entry in self._json_manifest[u'output_data']:
            entry_name = manifest_file_entry[u'name']
            file_entry_map[entry_name] = manifest_file_entry

        try:
            for file_name, (is_multiple, is_required) in output_file_definitions.items():
                if file_name not in file_entry_map:
                    if is_required:
                        raise ResultsManifestAndInterfaceDontMatch
                    else:
                        continue

                manifest_file_entry = file_entry_map[file_name]
                if is_multiple and u'files' not in manifest_file_entry:
                    raise ResultsManifestAndInterfaceDontMatch
                if not is_multiple and u'file' not in manifest_file_entry:
                    raise ResultsManifestAndInterfaceDontMatch
        except ResultsManifestAndInterfaceDontMatch as ex:
            msg = ('output_file_definitions did not match expected manifest\n'
                   'manifest: %s\n'
                   'output_definitions:%s\n'
                   'untrimmed_manifest_files=%s')
            logger.exception(msg, self._json_manifest, output_file_definitions, untrimmed_files)
            raise ex

    def _populate_defaults(self):
        '''populates the defaults in the json that was passed in'''

        if u'version' not in self._json_manifest:
            self._json_manifest[u'version'] = copy.copy(RESULTS_MANIFEST_SCHEMA[u'properties'][u'version'][u'default'])
        if u'output_data' not in self._json_manifest:
            self._json_manifest[u'output_data'] = copy.copy(RESULTS_MANIFEST_SCHEMA[u'properties'][u'output_data'][u'default'])
        if u'parse_results' not in self._json_manifest:
            default_parse_results = copy.copy(RESULTS_MANIFEST_SCHEMA[u'properties'][u'parse_results'][u'default'])
            self._json_manifest[u'parse_results'] = default_parse_results
        if u'errors' not in self._json_manifest:
            self._json_manifest[u'errors'] = copy.copy(RESULTS_MANIFEST_SCHEMA[u'properties'][u'errors'][u'default'])

    def _trim(self, output_file_definitions):
        '''Removes any extra entries in the manifest that aren't in the provided output_file definitions
        :param output_file_definitions: A dictionary with each output param name mapped to a tuple with
        (is_multiple (bool), required(bool))
        :type output_file_definitions: dict of tuples
        '''
        updated_entries = []
        for manifest_file_entry in self._json_manifest[u'output_data']:
            entry_name = manifest_file_entry[u'name']
            if entry_name in output_file_definitions:
                updated_entries.append(manifest_file_entry)
            else:
                #Don't include any files that aren't in the output definition
                logger.info('trimming %s from the results since it was not in the output definitions for the job type',
                            entry_name)

        self._json_manifest[u'output_data'] = updated_entries

    def _validate_manifest(self):
        '''validates portions of the manifest that cannot be validated with the json_schema'''
        file_entries = set()
        for manifest_file_entry in self._json_manifest[u'output_data']:
            entry_name = manifest_file_entry[u'name']
            if entry_name in file_entries:
                raise InvalidResultsManifest(u'output names cannot be repeated')
            file_entries.add(entry_name)

            if u'file' in manifest_file_entry and u'files' in manifest_file_entry:
                raise InvalidResultsManifest(u'an output_data entry can only have file or files, not both')
            if u'file' not in manifest_file_entry and u'files' not in manifest_file_entry:
                raise InvalidResultsManifest(u'an output_data entry must have either file or files')
