"""This module is concerned with the scale output manifest. Scale jobs are expected to produce an output manifest.
Scale needs to parse this manifest to bring the information into the system. The output files should match the job
interface
"""
from __future__ import unicode_literals

import copy
import logging

from jsonschema import validate
from jsonschema.exceptions import ValidationError
from job.configuration.results.exceptions import InvalidResultsManifest, MissingRequiredOutput

logger = logging.getLogger(__name__)

MANIFEST_VERSION = '1.0'

RESULTS_MANIFEST_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "version": {
            "description": "version of the results_manifest schema",
            "default": "1.0",
            "type": "string"
        },
        "files": {
            "description": "The files that should be ingested into the system",
            "default": [],
            "type": "array",
            "items": {"$ref": "#/definitions/files"}
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
        "files": {
            "description": "An output file or files.  The parameter is expected to match the output_interface",
            "type": "object",
            "required": ["name"],
            "properties": {
                "name": {
                    "type": "string"
                },
                "path": {
                    "type": "string"
                },
                "paths": {
                    "type": "array",
                    "items": {
                        "type": "string"
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
                "data_started": {
                    "type": "string"
                },
                "data_ended": {
                    "type": "string"
                },
                "data_types": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                },
                "gis_data_path": {
                    "type": "string"
                }
            }
        }
    }
}


class ResultsManifest(object):
    """Represents the interface for executing a job
    """

    def __init__(self, json_manifest):
        """Creates a result manifest from the json_manifest
        :param json_manifest: a dict in the format described by RESULTS_MANIFEST_SCHEMA
        :type json_manifest: dict
        """

        self._json_manifest = json_manifest

        try:
            validate(json_manifest, RESULTS_MANIFEST_SCHEMA)
        except ValidationError as validation_error:
            raise InvalidResultsManifest(str(validation_error))

        self._populate_defaults()
        self._validate_manifest()

    def _convert_schema(self, json_manifest):
        """Convert the previous manifest schema to the 1.0 manifest schema

        :param json_manifest: The old manifest
        :type json_manifest: dict
        :return: converted manifest
        :rtype: dict
        """

        # There are no supported manifest versions before 1.0
        raise InvalidResultsManifest('%s is an invalid results manifest version' % json_manifest['version'])

    def get_json_dict(self):
        """Return the json dictionary associated with this manifest

        :return: json dict representing this manifest
        :rtype: dict
        """
        return self._json_manifest

    def add_files(self, files_array):
        """adds the files to the manifest if they are not already in the manifest.  If there is already an entry
        for that file name it will be ignored
        :param files_array: an array of files that should be added to the manifest
        :type files_array: an array of the format RESULTS_MANIFEST_SCHEMA["definitions"]["files"]
        """
        filenames = set()
        for manifest_file_entry in self._json_manifest['files']:
            filenames.add(manifest_file_entry['name'])

        for new_file_entry in files_array:
            new_entry_name = new_file_entry['name']
            if new_entry_name not in filenames:
                filenames.add(new_entry_name)
                self._json_manifest['files'].append(new_file_entry)

    def get_files(self):
        """gets the output files associated with this manifest
        :return: an array of dictionaries.  Each dictionary describes a file in the manifest.
        The format of the dict is described
        by results_manifest.RESULTS_MANIFEST_SCHEMA["definitions"]["files"]
        :rtype: array of dict"""

        return self._json_manifest['files']

    def get_parse_results(self):
        """gets the parsed input files associated with this manifest
        :return: an array of dictionaries.  Each dictionary describes the location of a
        geojson associated with an input filein the manifest. The format of the dict is descibed by
        results_manifest.RESULTS_MANIFEST_SCHEMA["definitions"]["parse_results"]
        :rtype: array of dict"""
        return self._json_manifest['parse_results']

    def validate(self, output_file_definitions):
        """Validates the results manifest against given output file definitions.  Throws a
        :class `job.configuration.results.exceptions.ResultsManifestAndInterfaceDontMatch`: if the
        manifest doesn't match the outputs.  This does not validate that the parse_data matches the job
        data inputs.
        :param output_file_definitions: A dictionary with each output param name mapped to a tuple with
        (is_multiple (bool), required(bool))
        :type output_file_definitions: dict of tuples
        """

        self._trim(output_file_definitions)

        file_entry_map = {}
        for manifest_file_entry in self._json_manifest['files']:
            entry_name = manifest_file_entry['name']
            file_entry_map[entry_name] = manifest_file_entry

        for file_name, (is_multiple, is_required) in output_file_definitions.items():
            if file_name not in file_entry_map:
                if is_required:
                    raise MissingRequiredOutput(file_name)
                else:
                    continue

            manifest_file_entry = file_entry_map[file_name]
            if is_multiple and 'paths' not in manifest_file_entry:
                msg = 'The output parameter %s must have a paths object in the results manifest' % file_name
                raise InvalidResultsManifest(msg)
            if not is_multiple and 'path' not in manifest_file_entry:
                msg = 'The output parameter %s must have a path object in the results manifest' % file_name
                raise InvalidResultsManifest(msg)

    def _populate_defaults(self):
        """populates the defaults in the json that was passed in"""

        if 'version' not in self._json_manifest:
            self._json_manifest['version'] = copy.copy(RESULTS_MANIFEST_SCHEMA['properties']['version']['default'])
        if 'files' not in self._json_manifest:
            self._json_manifest['files'] = copy.copy(RESULTS_MANIFEST_SCHEMA['properties']['files']['default'])
        if 'parse_results' not in self._json_manifest:
            default_parse_results = copy.copy(RESULTS_MANIFEST_SCHEMA['properties']['parse_results']['default'])
            self._json_manifest['parse_results'] = default_parse_results
        if 'errors' not in self._json_manifest:
            self._json_manifest['errors'] = copy.copy(RESULTS_MANIFEST_SCHEMA['properties']['errors']['default'])

    def _trim(self, output_file_definitions):
        """Removes any extra entries in the manifest that aren't in the provided output_file definitions
        :param output_file_definitions: A dictionary with each output param name mapped to a tuple with
        (is_multiple (bool), required(bool))
        :type output_file_definitions: dict of tuples
        """
        updated_entries = []
        for manifest_file_entry in self._json_manifest['files']:
            entry_name = manifest_file_entry['name']
            if entry_name in output_file_definitions:
                updated_entries.append(manifest_file_entry)
            else:
                #Don't include any files that aren't in the output definition
                logger.info('trimming %s from the results since it was not in the output definitions for the job type',
                            entry_name)

        self._json_manifest['files'] = updated_entries

    def _validate_manifest(self):
        """validates portions of the manifest that cannot be validated with the json_schema"""
        file_entries = set()
        for manifest_file_entry in self._json_manifest['files']:
            entry_name = manifest_file_entry['name']
            if entry_name in file_entries:
                msg = 'The output parameter %s appears multiple times in the results manifest' % entry_name
                raise InvalidResultsManifest(msg)
            file_entries.add(entry_name)

            if 'path' in manifest_file_entry and 'paths' in manifest_file_entry:
                msg = 'The output parameter %s cannot have both path and paths objects in the results manifest'
                raise InvalidResultsManifest(msg % entry_name)
            if 'path' not in manifest_file_entry and 'paths' not in manifest_file_entry:
                msg = 'The output parameter %s must have either a path or paths object in the results manifest'
                raise InvalidResultsManifest(msg % entry_name)
