from __future__ import unicode_literals

import django
from django.test import TestCase

from job.seed.manifest import SeedManifest
from storage.media_type import UNKNOWN_MEDIA_TYPE


class TestSeedManifest(TestCase):
    """Tests functions in the manifest module."""

    def setUp(self):
        django.setup()

    def test_init_validation(self):
        """Tests creating and validating a Seed manifest JSON"""

        manifest_dict = {
            'seedVersion': '1.0.0',
            'job': {
                'name': 'image-watermark',
                'jobVersion': '0.1.0',
                'packageVersion': '0.1.0',
                'title': 'Image Watermarker',
                'description': 'Processes an input PNG and outputs watermarked PNG.',
                'maintainer': {
                    'name': 'John Doe',
                    'email': 'jdoe@example.com'
                },
                'timeout': 30,
                'interface': {
                    'command': '${INPUT_IMAGE} ${OUTPUT_DIR}',
                    'inputs': {
                        'files': [{'name': 'INPUT_IMAGE'}]
                    },
                    'outputs': {
                        'files': [{'name': 'OUTPUT_IMAGE', 'pattern': '*_watermark.png'}]
                    }
                },
                'resources': {
                    'scalar': [
                        {
                            'name': 'cpus',
                            'value': 1
                        },
                        {
                            'name': 'mem',
                            'value': 64
                        }
                    ]
                },
                'errors': [
                    {
                        'code': 1,
                        'name': 'image-Corrupt-1',
                        'description': 'Image input is not recognized as a valid PNG.',
                        'category': 'data'
                    },
                    {
                        'code': 2,
                        'name': 'algorithm-failure'
                    }
                ]
            }
        }

        # No exception is success
        SeedManifest(manifest_dict, do_validate=True)

    def test_init_default_values(self):
        """Tests creating and validating a Seed manifest JSON and ensures the correct defaults are used"""

        manifest_dict = {
            'seedVersion': '1.0.0',
            'job': {
                'name': 'my-job',
                'jobVersion': '0.1.0',
                'packageVersion': '0.1.0',
                'title': 'My Job',
                'description': 'Processes my job',
                'maintainer': {
                    'name': 'John Doe',
                    'email': 'jdoe@example.com'
                },
                'timeout': 30,
                'interface': {
                    'command': '${INPUT_IMAGE} ${JSON_FILES} ${OUTPUT_DIR}',
                    'inputs': {
                        'files': [{'name': 'INPUT_IMAGE'},
                                  {'name': 'JSON_FILES', 'mediaTypes': ['application/json'], 'multiple': True,
                                   'partial': True, 'required': False}]
                    },
                    'outputs': {
                        'files': [{'name': 'OUTPUT_IMAGE_A', 'pattern': '*.tif'},
                                  {'name': 'OUTPUT_IMAGE_B', 'pattern': '*.tif', 'mediaType': 'image/tiff',
                                   'multiple': True, 'required': False}]
                    }
                },
                'resources': {
                    'scalar': [
                        {
                            'name': 'cpus',
                            'value': 1
                        },
                        {
                            'name': 'mem',
                            'value': 64
                        }
                    ]
                },
                'errors': []
            }
        }

        manifest = SeedManifest(manifest_dict, do_validate=True)

        # Check input and output files for correct values
        input_files = manifest.get_input_files()
        input_image_dict = input_files[0]
        json_files_dict = input_files[1]
        self.assertDictEqual(input_image_dict, {'name': 'INPUT_IMAGE', 'mediaTypes': [], 'multiple': False,
                                                'partial': False, 'required': True})
        self.assertDictEqual(json_files_dict, {'name': 'JSON_FILES', 'mediaTypes': ['application/json'],
                                               'multiple': True, 'partial': True, 'required': False})
        output_files = manifest.get_output_files()
        output_image_a_dict = output_files[0]
        output_image_b_dict = output_files[1]
        self.assertDictEqual(output_image_a_dict, {'name': 'OUTPUT_IMAGE_A', 'pattern': '*.tif',
                                                   'mediaType': UNKNOWN_MEDIA_TYPE, 'multiple': False,
                                                   'required': True})
        self.assertDictEqual(output_image_b_dict, {'name': 'OUTPUT_IMAGE_B', 'pattern': '*.tif',
                                                   'mediaType': 'image/tiff', 'multiple': True, 'required': False})
