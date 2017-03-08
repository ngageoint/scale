from __future__ import unicode_literals

import django
from django.test import TransactionTestCase

import ingest.test.utils as ingest_test_utils
import source.test.utils as source_test_utils


class TestPerformIngest(TransactionTestCase):
    fixtures = ['ingest_job_types.json']

    def setUp(self):
        django.setup()

        self.ingest = ingest_test_utils.create_ingest(status='QUEUED')
        self.source_file = source_test_utils.create_source(workspace=self.ingest.workspace)

    def test_successful(self):
        """Tests processing a new ingest successfully."""

        pass
