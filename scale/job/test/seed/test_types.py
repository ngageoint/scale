from __future__ import unicode_literals

import json

import django
from django.test import TestCase
from job.seed.results.outputs_json import SeedOutputsJson
from mock import patch, mock_open

from job.seed.types import SeedInputFiles, SeedOutputJson, SeedOutputFiles


class TestSeedInputsJson(TestCase):

    def setUp(self):
        django.setup()


class TestSeedOutputsFiles(TestCase):

    def setUp(self):
        django.setup()

    @patch('glob.glob', return_value=['output.txt', 'output.txt.metadata.json'])
    def test_get_files(self, glob):
        seed_output_file = SeedOutputFiles({
            'name': 'OUTPUT_FILE',
            'pattern': 'output*',
            'multiple': False,
            'required': True
        })

        files = seed_output_file.get_files()

        self.assertEqual(['output.txt'], files)

    @patch('glob.glob', return_value=['outputs1.txt',
                                      'outputs2.txt', 'outputs2.txt.metadata.json',
                                      'outputs3.metadata.json'])
    def test_get_files_multiple(self, glob):
        seed_output_file = SeedOutputFiles({
                'name': 'OUTPUT_FILES',
                'pattern': 'outputs*',
                'multiple': True,
                'required': True
            })

        files = seed_output_file.get_files()

        self.assertEqual(['outputs1.txt', 'outputs2.txt'], files)


class TestSeedOutputsJson(TestCase):

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
