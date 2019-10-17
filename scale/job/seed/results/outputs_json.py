import json
import logging
import os
from jsonschema import validate

from job.execution.container import SCALE_JOB_EXE_OUTPUT_PATH

logger = logging.getLogger(__name__)

SEED_OUTPUTS_JSON_FILENAME = 'seed.outputs.json'
SEED_OUTPUTS_PARSE_RESULTS = 'parse_results'

SCHEMA_FILENAME = os.path.join(os.path.dirname(os.path.realpath(__file__)), '/../schema/seed.metadata.schema.json')
with open(SCHEMA_FILENAME) as schema_file:
    SOURCE_METADATA_SCHEMA = json.load(schema_file)


class SeedOutputsJson(object):
    def __init__(self, data, schema=None):
        self._dict = data

        if schema:
            validate(self._dict, schema)

    @staticmethod
    def read_outputs(schema):
        file_path = os.path.join(SCALE_JOB_EXE_OUTPUT_PATH, SEED_OUTPUTS_JSON_FILENAME)
        with open(file_path) as in_file:
            in_json = json.load(in_file)

        return SeedOutputsJson(in_json, schema)

    @staticmethod
    def construct_schema(interface_outputs):
        """Dynamically build a schema to validate seed.outputs.json

        :param interface_outputs: Seed Interface definition for types of JSON outputs
        :type interface_outputs: [:class:`job.seed.types.SeedOutputJson`]
        :return: Schema for validation of seed.outputs.json
        :rtype: dict
        """

        required = []
        schema = { 'type': 'object',
                   'properties': {},
                   'required': [] }
        for output in interface_outputs:
            schema['properties'][output.json_key] = {
                'type': output.type
            }
            if output.required:
                required.append(output.json_key)

        if len(required):
            schema['required'] = required

        return schema

    def get_values(self, interface_outputs):
        """Returns all data needed in the interface. Any keys not indicated in the interface are ignored.

        :param interface_outputs: Seed Interface definition for types of JSON outputs
        :type interface_outputs: :class:`job.seed.types.SeedOutputJson`
        :return: All outputs captured from seed.outputs.json in { key: value } format
        :rtype: { string: typed_value }
        """

        # Used to remap any keys to the associated named interface JSON output
        remap = {x.json_key: x.name for x in interface_outputs}

        values = {}
        for key, value in self._dict.iteritems():
            if key in remap:
                values[remap[key]] = value

        return values

    def get_supplemental_metadata(self, job_data):
        """Special handling for reserved keyword within output file for supplemental metadata.

        Will look for key inputFileMetadata

        :param job_data: The job data
        :type job_data: :class:`job.data.job_data.JobData`
        :return: All supplemental metadata discovered that matches an input file provided to job
        :rtype: dict
        """

        response = {}

        if SEED_OUTPUTS_PARSE_RESULTS in self._dict:
            logger.info('Found {} key in {} file...'.format(SEED_OUTPUTS_PARSE_RESULTS,
                                                            SEED_OUTPUTS_JSON_FILENAME))
            # Grab all keys in the parse_results dict
            for local_path, metadata in self._dict[SEED_OUTPUTS_PARSE_RESULTS].iteritems():
                file_id = job_data.get_id_from_path(local_path)
                if file_id:
                    validate(metadata, SOURCE_METADATA_SCHEMA)
                    response[file_id] = metadata
                else:
                    logger.warning('Unable to find corresponding file id for local path: ', local_path)

        return response
