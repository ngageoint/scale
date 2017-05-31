from __future__ import unicode_literals

import django
from django.test import TestCase
from mock import patch

import storage.test.utils as storage_test_utils
from ingest.models import Ingest
from ingest.scan.scanners.exceptions import ScannerInterruptRequested
from ingest.scan.scanners.s3_scanner import S3Scanner
from storage.brokers.broker import FileDetails


class TestS3Scanner(TestCase):
    def setUp(self):
        django.setup()

    def test_set_recursive_false(self):
        """Tests calling S3Scanner.set_recursive() to false"""

        scanner = S3Scanner()
        scanner.set_recursive(False)
        self.assertFalse(scanner._recursive)

    def test_recursive_default(self):
        """Tests default property of recursive on S3Scanner instance"""

        scanner = S3Scanner()
        self.assertTrue(scanner._recursive)

    def test_load_configuration(self):
        """Tests calling S3Scanner.load_configuration() successfully"""

        config = {
            'type': 's3',
        }

        scanner = S3Scanner()
        scanner.load_configuration(config)
        self.assertEquals(scanner._scanner_type, 's3')

    def test_validate_configuration_extra_key(self):
        """Tests calling S3Scanner.validate_configuration() with extra key"""

        config = {
            'type': 's3',
            'random_key': ''
        }
        S3Scanner().validate_configuration(config)

    def test_validate_configuration_success(self):
        """Tests calling S3Scanner.validate_configuration() successfully"""

        config = {
            'type': 's3'
        }
        S3Scanner().validate_configuration(config)


class TestScanner(TestCase):
    def setUp(self):
        django.setup()

        self.workspace = storage_test_utils.create_workspace()

    def test_process_scanned_interrupted(self):
        """Tests calling S3Scanner._process_scanned() with interruption"""

        scanner = S3Scanner()
        scanner._stop_received = True
        with self.assertRaises(ScannerInterruptRequested):
            scanner._process_scanned([None])

    def test_process_scanned_no_ingests(self):
        """Tests calling S3Scanner._process_scanned() with no ingests"""

        scanner = S3Scanner()
        scanner._process_scanned([])

        # Ensure no files were detected
        self.assertEquals(scanner._count, 0)

    @patch('ingest.scan.scanners.s3_scanner.S3Scanner._deduplicate_ingest_list')
    @patch('ingest.scan.scanners.s3_scanner.S3Scanner._ingest_file', return_value=None)
    def test_process_scanned_dry_run(self, ingest_file, dedup):
        """Tests calling S3Scanner._process_scanned() during dry run"""

        scanner = S3Scanner()
        scanner._dry_run = True

        scanner._process_scanned([FileDetails('test', 0)])

        # Ensure we counted the one file
        self.assertEquals(scanner._count, 1)
        # Ensure the ingest file method was called
        self.assertTrue(ingest_file.called)
        # Verify we returned prior to calling _deduplicate_ingest_list 
        self.assertFalse(dedup.called)

    @patch('ingest.scan.scanners.s3_scanner.S3Scanner._deduplicate_ingest_list')
    @patch('ingest.scan.scanners.s3_scanner.S3Scanner._process_ingest', return_value=None)
    def test_process_scanned_no_rule_match(self, process_ingest, dedup):
        """Tests calling S3Scanner._process_scanned() during ingest run"""

        scanner = S3Scanner()
        scanner._dry_run = False
        scanner._scanned_workspace = self.workspace

        scanner._process_scanned([FileDetails('test', 0)])

        # Ensure we counted the one file
        self.assertEquals(scanner._count, 1)
        # Ensure the ingest file method was called
        self.assertTrue(process_ingest.called)
        # Verify we returned prior to calling _deduplicate_ingest_list
        self.assertFalse(dedup.called)

    @patch('ingest.models.IngestManager.start_ingest_tasks')
    @patch('ingest.scan.scanners.s3_scanner.S3Scanner._deduplicate_ingest_list')
    @patch('ingest.scan.scanners.s3_scanner.S3Scanner._ingest_file')
    def test_process_scanned_successfully(self, ingest_file, dedup, start_ingests):
        """Tests calling S3Scanner._process_scanned() successfully"""

        scanner = S3Scanner()
        scanner._process_scanned([FileDetails('test1', 0), FileDetails('test2', 0)])

        # Verify that 2 files were received
        self.assertEquals(scanner._count, 2)
        # Verify that _ingest_file was called twice
        self.assertEquals(ingest_file.call_count, 2)

        # Verify that all method calls were made from callback method
        self.assertTrue(dedup.called)
        self.assertTrue(start_ingests.called)

    @patch('ingest.models.Ingest.objects.get_ingests_by_scan')
    def test_deduplicate_ingest_list_no_existing(self, ingests_by_scan):
        """Tests calling S3Scanner._deduplicate_ingest_list() without existing"""

        ingests_by_scan.return_value = []

        ingests = [Ingest(file_name='test1'), Ingest(file_name='test2')]
        final_ingests = S3Scanner._deduplicate_ingest_list(None, ingests)

        self.assertItemsEqual(ingests, final_ingests)

    @patch('ingest.models.Ingest.objects.get_ingests_by_scan')
    def test_deduplicate_ingest_list_with_duplicate_file_names(self, ingests_by_scan):
        """Tests calling S3Scanner._deduplicate_ingest_list() with duplicates"""

        ingests_by_scan.return_value = []

        ingests = [Ingest(file_name='test1'), Ingest(file_name='test1')]
        final_ingests = S3Scanner._deduplicate_ingest_list(None, ingests)

        self.assertEquals(len(final_ingests), 1)
        self.assertEquals(final_ingests[0].file_name, 'test1')

    @patch('ingest.models.Ingest.objects.get_ingests_by_scan')
    def test_deduplicate_ingest_list_with_existing_no_other_dups(self, ingests_by_scan):
        """Tests calling S3Scanner._deduplicate_ingest_list() with existing and no other dups"""

        ingests_by_scan.return_value = [Ingest(file_name='test1')]

        ingests = [Ingest(file_name='test1'), Ingest(file_name='test2')]
        final_ingests = S3Scanner._deduplicate_ingest_list(None, ingests)

        self.assertEquals(len(final_ingests), 1)
        self.assertEquals(final_ingests[0].file_name, 'test2')

    def test_set_recursive_false(self):
        """Tests calling S3Scanner.set_recursive() to false"""

        scanner = S3Scanner()
        scanner.set_recursive(False)
        self.assertFalse(scanner._recursive)

    def test_recursive_default(self):
        """Tests default property of recursive on Scanner instance"""

        scanner = S3Scanner()
        self.assertTrue(scanner._recursive)

    def test_stop(self):
        """Tests calling S3Scanner.stop() successfully"""

        scanner = S3Scanner()

        self.assertFalse(scanner._stop_received)
        scanner.stop()
        self.assertTrue(scanner._stop_received)
