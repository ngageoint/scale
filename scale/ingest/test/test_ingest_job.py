from __future__ import unicode_literals

import django
from django.test import TransactionTestCase
from mock import patch

import ingest.ingest_job as ingest_job
import ingest.test.utils as ingest_test_utils
import source.test.utils as source_test_utils
from ingest.models import Ingest
from job.models import JobExecution


class TestPerformIngest(TransactionTestCase):

    fixtures = ['ingest_job_types.json']

    def setUp(self):
        django.setup()

        self.ingest = ingest_test_utils.create_ingest(status='INGESTING')
        self.job_exe_id = JobExecution.objects.get(job_id=self.ingest.job).id
        self.source_file = source_test_utils.create_source(workspace=self.ingest.workspace)

    @patch('ingest.ingest_job.cleanup_job_exe')
    @patch('ingest.ingest_job.os.makedirs')
    @patch('ingest.ingest_job.os.path.exists')
    @patch('ingest.ingest_job._delete_ingest_file')
    @patch('ingest.ingest_job._move_ingest_file')
    @patch('ingest.ingest_job.SourceFile')
    @patch('ingest.ingest_job.nfs_umount')
    @patch('ingest.ingest_job.nfs_mount')
    def test_successful(self, mock_nfs_mount, mock_nfs_umount, mock_SourceFile, mock_move_ingest_file,
                        mock_delete_ingest_file, mock_exists, mock_makedirs, mock_cleanup):
        """Tests processing a new ingest successfully."""
        # Set up mocks
        def new_exists(file_path):
            return True
        mock_exists.side_effect = new_exists
        mock_SourceFile.objects.store_file.return_value = self.source_file

        ingest_job.perform_ingest(self.ingest.id, 'host:/mount')

        ingest = Ingest.objects.get(pk=self.ingest.id)
        self.assertEqual(ingest.status, 'INGESTED')
        self.assertEqual(ingest.source_file_id, self.source_file.id)
        mock_cleanup.assert_called_with(self.job_exe_id)
