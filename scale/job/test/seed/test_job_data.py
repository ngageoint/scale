from __future__ import unicode_literals
import datetime

import django
from django.test import TestCase
from django.utils.timezone import utc
from mock import MagicMock, patch

import job.clock as clock
import job.test.utils as job_test_utils
from job.clock import ClockEventError, ClockEventProcessor

from job.configuration.results.exceptions import OutputCaptureError
from job.execution.container import SCALE_JOB_EXE_INPUT_PATH, SCALE_JOB_EXE_OUTPUT_PATH
from product.models import ProductFileMetadata
from trigger.models import TriggerEvent


from job.seed.data.job_data import JobData

class TestJobData(TestCase):
    """Tests functions in the clock module."""

    def setUp(self):
        django.setup()

        self.test_output_snippet = {
            "name": "OUTPUT_TIFFS",
            "mediaType": "image/tiff",
            "pattern": "outfile*.tif",
            "multiple": False,
            "required": True
        }

    @patch('job.seed.data.job_data.SeedOutputFiles.get_files')
    def test_capture_output_files_missing(self, get_files):
        get_files.side_effect = OutputCaptureError('message')

        with self.assertRaises(OutputCaptureError) as exc:
            JobData.capture_output_files([self.test_output_snippet])

    @patch('job.seed.data.job_data.SeedOutputFiles.get_files')
    def test_capture_output_files_multiple(self, get_files):
        name = 'OUTPUT_TIFFS'
        get_files.return_value = ['outfile0.tif', 'outfile1.tif']

        outputs = JobData.capture_output_files([self.test_output_snippet])

        self.assertIn(name, outputs)
        files = outputs[name]
        self.assertEqual(len(files), 2)
        self.assertEqual(files[0].__dict__, ProductFileMetadata(name, 'outfile0.tif', media_type='image/tiff').__dict__)
        self.assertEqual(files[1].__dict__, ProductFileMetadata(name, 'outfile1.tif', media_type='image/tiff').__dict__)

