import json

import os
from jsonschema import validate

from job.execution.container import SCALE_JOB_EXE_OUTPUT_PATH

SEED_OUPUTS_JSON_FILENAME = 'seed.outputs.json'

class SeedOutputsJson(object):
    def __init__(self, data, schema=None):
        self._dict = data

        if schema:
            validate(self._dict, schema)

    @staticmethod
    def read_outputs(schema):
        file_path = os.path.join(SCALE_JOB_EXE_OUTPUT_PATH, SEED_OUPUTS_JSON_FILENAME)
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
        :type: { string: typed_value }
        """

        # Used to remap any keys to the associated named interface JSON output
        remap = {x.json_key: x.name for x in interface_outputs}

        values = {}
        for key, value in self._dict.iteritems():
            if key in remap:
                values[remap[key]] = value

        return values
