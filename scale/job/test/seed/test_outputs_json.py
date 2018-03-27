from __future__ import unicode_literals

import json

import django
from django.test import TestCase
from job.seed.results.outputs_json import SeedOutputsJson
from mock import patch, mock_open

from job.seed.types import SeedOutputJson


class TestSeedOutputsJson(TestCase):
    """Tests functions in the JobData module."""

    def setUp(self):
        django.setup()

        outputs_json_interface = [
            {
                'name': 'INPUT_SIZE',
                'type': 'integer'
            },
            {
                'name': 'MISSING_KEY',
                'type': 'string',
                'required': False
            }
        ]

        self.seed_outputs_json = [SeedOutputJson(x) for x in outputs_json_interface]

        self.outputs_json_dict = {'INPUT_FILE_NAME': '/my/file', 'INPUT_SIZE': 50}

        self.schema = {'required': ['INPUT_SIZE'], 'type': 'object',
                       'properties': {'INPUT_SIZE': {'type': 'integer'}, 'MISSING_KEY': {'type': 'string'}}}

    def test_construct_schema(self):
        self.assertDictEqual(self.schema, SeedOutputsJson.construct_schema(self.seed_outputs_json))

    def test_read_outputs(self):
        schema = SeedOutputsJson.construct_schema(self.seed_outputs_json)

        with patch("__builtin__.open", mock_open(read_data=json.dumps(self.outputs_json_dict))):
            result = SeedOutputsJson.read_outputs(schema)

        self.assertDictEqual(self.outputs_json_dict, result._dict)


    def test_get_values(self):
        outputs_obj = SeedOutputsJson(self.outputs_json_dict, self.schema)

        results = outputs_obj.get_values(self.seed_outputs_json)

        self.assertDictEqual(results, {'INPUT_SIZE': 50})
