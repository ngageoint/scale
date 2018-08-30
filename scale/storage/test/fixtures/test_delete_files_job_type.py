from __future__ import unicode_literals

import json
import os

import django
from django.test import TestCase

from job.seed.manifest import SeedManifest

class TestSeedManifest(TestCase):
    """Validate the seed manifest for a Scale fixture."""

    def setUp(self):
        django.setup()

    def test_validation(self):
        """Tests creating and validating the Seed manifest in delete_files_job_type.json"""

        json_file_name = 'delete_files_job_type.json'
        storage_dir = os.path.abspath(os.path.join(__file__, "../../..")) # storage/test/fixtures
        json_file = os.path.join(storage_dir, 'fixtures', json_file_name)

        with open(json_file) as json_data:
            d = json.load(json_data)
            manifest_dict = d[0]['fields']['manifest']

            # No exception is success
            SeedManifest(manifest_dict, do_validate=True)
