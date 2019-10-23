from __future__ import unicode_literals

import json

import django
import os
from django.test import TransactionTestCase
from job.configuration.results.exceptions import OutputCaptureError
from job.seed.results.job_results import JobResults
from job.seed.types import SeedOutputFiles, SeedOutputJson, SeedInputFiles
from mock import patch, mock_open
from product.types import ProductFileMetadata


class TestSeedJobResults(TransactionTestCase):
    """Tests functions in the manifest module."""

    def setUp(self):
        django.setup()

        self.test_input_snippets = [
            {
                "name": "INPUT_FILE",
                "multiple": False
            },
            {
                "name": "INPUT_COLLECTION",
                "multiple": True
            }
        ]

        self.test_output_snippet = {
            "name": "OUTPUT_TIFFS",
            "mediaType": "image/tiff",
            "pattern": "outfile*.tif",
            "multiple": False,
            "required": True
        }

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

    @patch('job.seed.types.SeedOutputFiles.get_files')
    def test_capture_output_files_missing(self, get_files):
        output_files = [SeedOutputFiles(self.test_output_snippet)]

        get_files.side_effect = OutputCaptureError('message')

        with self.assertRaises(OutputCaptureError) as exc:
            JobResults()._capture_output_files(output_files)

    @patch('job.seed.types.SeedOutputFiles.get_files')
    def test_capture_output_files_multiple(self, get_files):
        output_files = [SeedOutputFiles(self.test_output_snippet)]
        name = 'OUTPUT_TIFFS'
        get_files.return_value = ['outfile0.tif', 'outfile1.tif']

        outputs = JobResults()._capture_output_files(output_files)

        self.assertIn(name, outputs)
        files = outputs[name]
        self.assertEqual(len(files), 2)
        self.assertEqual(files[0].__dict__, ProductFileMetadata(name, 'outfile0.tif', media_type='image/tiff').__dict__)
        self.assertEqual(files[1].__dict__, ProductFileMetadata(name, 'outfile1.tif', media_type='image/tiff').__dict__)

    @patch('job.seed.types.SeedOutputFiles.get_files')
    def test_capture_output_files_metadata(self, get_files):
        output_files = [SeedOutputFiles(self.test_output_snippet)]
        name = 'OUTPUT_TIFFS'
        get_files.return_value = ['outfile0.tif']

        metadata = {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [0, 1]
            },
            'properties':
            {
                'dataStarted': '2018-06-01T00:00:00Z',
                'dataEnded': '2018-06-01T01:00:00Z',
                'sourceStarted': '2018-06-01T00:00:00Z',
                'sourceEnded': '2018-06-01T06:00:00Z',
                'sourceSensorClass': 'Platform',
                'sourceSensor': 'X1',
                'sourceCollection': '12345A',
                'sourceTask': 'Calibration'
            }
        }

        metadata_name = 'outfile0.tif.metadata.json'
        with open(metadata_name, 'w') as metadata_file:
            json.dump(metadata, metadata_file)

        outputs = JobResults()._capture_output_files(output_files)

        os.remove(metadata_name)

        self.assertIn(name, outputs)
        files = outputs[name]

        self.assertEqual(len(files), 1)
        self.assertDictEqual(files[0].__dict__, ProductFileMetadata(output_name=name,
                                                                    local_path='outfile0.tif',
                                                                    media_type='image/tiff',
                                                                    data_start='2018-06-01T00:00:00Z',
                                                                    data_end='2018-06-01T01:00:00Z',
                                                                    geojson=metadata,
                                                                    source_started='2018-06-01T00:00:00Z',
                                                                    source_ended='2018-06-01T06:00:00Z',
                                                                    source_sensor_class='Platform',
                                                                    source_sensor='X1',
                                                                    source_collection='12345A',
                                                                    source_task='Calibration').__dict__)

    @patch('os.path.join')
    def test_capture_source_metadata_files(self, join):
        input_files = [SeedInputFiles(x) for x in self.test_input_snippets]
        name_to_id = {"INPUT_FILE": [1]}
        metadata_name = 'INPUT_FILE.metadata.json'
        join.return_value = metadata_name

        metadata = {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [0, 1]
            },
            'properties':
            {
                'dataStarted': '2018-06-01T00:00:00Z',
                'dataEnded': '2018-06-01T01:00:00Z',
                'dataTypes': ['one', 'two', 'three']
            }
        }

        with open(metadata_name, 'w') as metadata_file:
            json.dump(metadata, metadata_file)

        outputs = JobResults()._capture_source_metadata_files(input_files, name_to_id)

        os.remove(metadata_name)

        self.assertEqual(len(outputs), 1)
        self.assertDictEqual(outputs[1].data, metadata)

    def test_capture_output_json(self):
        results = JobResults()
        with patch("__builtin__.open", mock_open(read_data=json.dumps(self.outputs_json_dict))):
            results._capture_output_json(self.seed_outputs_json)

        self.assertDictEqual(results.get_dict(), {'files': {}, 'json': {'INPUT_SIZE': 50}, 'version': '7'})
