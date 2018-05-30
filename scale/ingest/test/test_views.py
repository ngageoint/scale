from __future__ import unicode_literals

import datetime
import json

import django
from django.test import TestCase, TransactionTestCase
from django.utils.timezone import utc
from rest_framework import status

import job.test.utils as job_utils
import ingest.test.utils as ingest_test_utils
import storage.test.utils as storage_test_utils
import util.rest as rest_util
from ingest.models import Scan, Strike
from ingest.scan.configuration.scan_configuration import ScanConfiguration
from ingest.strike.configuration.strike_configuration import StrikeConfiguration


class TestIngestsViewV5(TestCase):
    
    version = 'v5'
    fixtures = ['ingest_job_types.json']

    def setUp(self):
        django.setup()

        self.ingest1 = ingest_test_utils.create_ingest(strike=ingest_test_utils.create_strike(), file_name='test1.txt',
                                                       status='QUEUED')
        self.ingest2 = ingest_test_utils.create_ingest(strike=ingest_test_utils.create_strike(), file_name='test2.txt',
                                                       status='INGESTED')

    def test_successful(self):
        """Tests successfully calling the ingests view."""

        url = '/%s/ingests/' % self.version
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 2)
        for entry in result['results']:
            expected = None
            if entry['id'] == self.ingest1.id:
                expected = self.ingest1
            elif entry['id'] == self.ingest2.id:
                expected = self.ingest2
            else:
                self.fail('Found unexpected result: %s' % entry['id'])
            self.assertEqual(entry['file_name'], expected.file_name)
            self.assertEqual(entry['status'], expected.status)

    def test_status(self):
        """Tests successfully calling the ingests view filtered by status."""

        url = '/%s/ingests/?status=%s' % (self.version, self.ingest1.status)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['status'], self.ingest1.status)

    def test_strike_id(self):
        """Tests successfully calling the ingests view filtered by strike processor."""

        url = '/%s/ingests/?strike_id=%i' % (self.version, self.ingest1.strike.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['strike']['id'], self.ingest1.strike.id)

    def test_file_name(self):
        """Tests successfully calling the ingests view filtered by file name."""

        url = '/%s/ingests/?file_name=%s' % (self.version, self.ingest1.file_name)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['file_name'], self.ingest1.file_name)

class TestIngestsViewV6(TestCase):
    
    version = 'v6'
    fixtures = ['ingest_job_types.json']

    def setUp(self):
        django.setup()

        self.ingest1 = ingest_test_utils.create_ingest(strike=ingest_test_utils.create_strike(), file_name='test1.txt',
                                                       status='QUEUED')
        self.ingest2 = ingest_test_utils.create_ingest(strike=ingest_test_utils.create_strike(), file_name='test2.txt',
                                                       status='INGESTED')

    def test_successful(self):
        """Tests successfully calling the ingests view."""

        url = '/%s/ingests/' % self.version
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 2)
        for entry in result['results']:
            expected = None
            if entry['id'] == self.ingest1.id:
                expected = self.ingest1
            elif entry['id'] == self.ingest2.id:
                expected = self.ingest2
            else:
                self.fail('Found unexpected result: %s' % entry['id'])
            self.assertEqual(entry['file_name'], expected.file_name)
            self.assertEqual(entry['status'], expected.status)

    def test_status(self):
        """Tests successfully calling the ingests view filtered by status."""

        url = '/%s/ingests/?status=%s' % (self.version, self.ingest1.status)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['status'], self.ingest1.status)

    def test_strike_id(self):
        """Tests successfully calling the ingests view filtered by strike processor."""

        url = '/%s/ingests/?strike_id=%i' % (self.version, self.ingest1.strike.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['strike']['id'], self.ingest1.strike.id)

    def test_file_name(self):
        """Tests successfully calling the ingests view filtered by file name."""

        url = '/%s/ingests/?file_name=%s' % (self.version, self.ingest1.file_name)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['file_name'], self.ingest1.file_name)

class TestIngestDetailsViewV5(TestCase):
    version = 'v5'
    fixtures = ['ingest_job_types.json']

    def setUp(self):
        django.setup()

        self.ingest = ingest_test_utils.create_ingest(file_name='test1.txt', status='QUEUED')

    def test_id(self):
        """Tests successfully calling the ingests view by id."""

        url = '/%s/ingests/%d/' % (self.version, self.ingest.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(result['id'], self.ingest.id)
        self.assertEqual(result['file_name'], self.ingest.file_name)
        self.assertEqual(result['status'], self.ingest.status)

    def test_file_name(self):
        """Tests successfully calling the ingests view by file name."""

        url = '/%s/ingests/%s/' % (self.version, self.ingest.file_name)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(result['id'], self.ingest.id)
        self.assertEqual(result['file_name'], self.ingest.file_name)
        self.assertEqual(result['status'], self.ingest.status)

    def test_missing(self):
        """Tests calling the ingests view with an invalid id or file name."""

        url = '/%s/ingests/12345/' % self.version
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

        url = '/%s/ingests/missing_file.txt/' % self.version
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)
        
class TestIngestDetailsViewV6(TestCase):
    version = 'v6'
    fixtures = ['ingest_job_types.json']

    def setUp(self):
        django.setup()

        self.ingest = ingest_test_utils.create_ingest(file_name='test1.txt', status='QUEUED')

    def test_id(self):
        """Tests successfully calling the ingests view by id."""

        url = '/%s/ingests/%d/' % (self.version, self.ingest.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(result['id'], self.ingest.id)
        self.assertEqual(result['file_name'], self.ingest.file_name)
        self.assertEqual(result['status'], self.ingest.status)

    def test_missing(self):
        """Tests calling the ingests view with an invalid id or file name."""

        url = '/%s/ingests/12345/' % self.version
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)


class TestIngestStatusViewV5(TestCase):
    version = 'v5'
    fixtures = ['ingest_job_types.json']

    def setUp(self):
        django.setup()

        self.strike = ingest_test_utils.create_strike()
        self.ingest1 = ingest_test_utils.create_ingest(file_name='test1.txt', status='QUEUED', strike=self.strike)
        self.ingest2 = ingest_test_utils.create_ingest(file_name='test2.txt', status='INGESTED', strike=self.strike)
        self.ingest3 = ingest_test_utils.create_ingest(file_name='test3.txt', status='INGESTED', strike=self.strike)
        self.ingest4 = ingest_test_utils.create_ingest(file_name='test4.txt', status='INGESTED', strike=self.strike,
                                                       data_started=datetime.datetime(2015, 1, 1, tzinfo=utc),
                                                       ingest_ended=datetime.datetime(2015, 2, 1, tzinfo=utc))

    def test_successful(self):
        """Tests successfully calling the ingest status view."""

        url = '/%s/ingests/status/' % self.version
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)

        entry = result['results'][0]
        self.assertEqual(entry['strike']['id'], self.strike.id)
        self.assertIsNotNone(entry['most_recent'])
        self.assertEqual(entry['files'], 2)
        self.assertEqual(entry['size'], self.ingest2.file_size + self.ingest3.file_size)

    def test_time_range(self):
        """Tests successfully calling the ingest status view with a time range filter."""

        url = '/%s/ingests/status/?started=2015-01-01T00:00:00Z' % self.version
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)

        entry = result['results'][0]
        self.assertEqual(entry['strike']['id'], self.strike.id)
        self.assertIsNotNone(entry['most_recent'])
        self.assertEqual(entry['files'], 3)
        self.assertEqual(entry['size'], self.ingest2.file_size + self.ingest3.file_size + self.ingest4.file_size)

    def test_use_ingest_time(self):
        """Tests successfully calling the ingest status view grouped by ingest time instead of data time."""

        url = '/%s/ingests/status/?started=2015-02-01T00:00:00Z&' \
              'ended=2015-03-01T00:00:00Z&use_ingest_time=true' % self.version
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)

        entry = result['results'][0]
        self.assertEqual(entry['strike']['id'], self.strike.id)
        self.assertEqual(entry['most_recent'], '2015-02-01T00:00:00Z')
        self.assertEqual(entry['files'], 1)
        self.assertEqual(entry['size'], self.ingest3.file_size)

    def test_fill_empty_slots(self):
        """Tests successfully calling the ingest status view with place holder zero values when no data exists."""

        url = '/%s/ingests/status/?started=2015-01-01T00:00:00Z&ended=2015-01-01T10:00:00Z' % self.version
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)

        entry = result['results'][0]
        self.assertEqual(entry['strike']['id'], self.strike.id)
        self.assertIsNotNone(entry['most_recent'])
        self.assertEqual(entry['files'], 1)
        self.assertEqual(entry['size'], self.ingest3.file_size)
        self.assertEqual(len(entry['values']), 24)

    def test_multiple_strikes(self):
        """Tests successfully calling the ingest status view with multiple strike process groupings."""
        ingest_test_utils.create_strike()
        strike3 = ingest_test_utils.create_strike()
        ingest_test_utils.create_ingest(file_name='test3.txt', status='INGESTED', strike=strike3)

        url = '/%s/ingests/status/' % self.version
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 3)

class TestIngestStatusViewV6(TestCase):
    version = 'v6'
    fixtures = ['ingest_job_types.json']

    def setUp(self):
        django.setup()

        self.strike = ingest_test_utils.create_strike()
        self.ingest1 = ingest_test_utils.create_ingest(file_name='test1.txt', status='QUEUED', strike=self.strike)
        self.ingest2 = ingest_test_utils.create_ingest(file_name='test2.txt', status='INGESTED', strike=self.strike)
        self.ingest3 = ingest_test_utils.create_ingest(file_name='test3.txt', status='INGESTED', strike=self.strike)
        self.ingest4 = ingest_test_utils.create_ingest(file_name='test4.txt', status='INGESTED', strike=self.strike,
                                                       data_started=datetime.datetime(2015, 1, 1, tzinfo=utc),
                                                       ingest_ended=datetime.datetime(2015, 2, 1, tzinfo=utc))

    def test_successful(self):
        """Tests successfully calling the ingest status view."""

        url = '/%s/ingests/status/' % self.version
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)

        entry = result['results'][0]
        self.assertEqual(entry['strike']['id'], self.strike.id)
        self.assertIsNotNone(entry['most_recent'])
        self.assertEqual(entry['files'], 2)
        self.assertEqual(entry['size'], self.ingest2.file_size + self.ingest3.file_size)

    def test_time_range(self):
        """Tests successfully calling the ingest status view with a time range filter."""

        url = '/%s/ingests/status/?started=2015-01-01T00:00:00Z' % self.version
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)

        entry = result['results'][0]
        self.assertEqual(entry['strike']['id'], self.strike.id)
        self.assertIsNotNone(entry['most_recent'])
        self.assertEqual(entry['files'], 3)
        self.assertEqual(entry['size'], self.ingest2.file_size + self.ingest3.file_size + self.ingest4.file_size)

    def test_use_ingest_time(self):
        """Tests successfully calling the ingest status view grouped by ingest time instead of data time."""

        url = '/%s/ingests/status/?started=2015-02-01T00:00:00Z&' \
              'ended=2015-03-01T00:00:00Z&use_ingest_time=true' % self.version
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)

        entry = result['results'][0]
        self.assertEqual(entry['strike']['id'], self.strike.id)
        self.assertEqual(entry['most_recent'], '2015-02-01T00:00:00Z')
        self.assertEqual(entry['files'], 1)
        self.assertEqual(entry['size'], self.ingest3.file_size)

    def test_fill_empty_slots(self):
        """Tests successfully calling the ingest status view with place holder zero values when no data exists."""

        url = '/%s/ingests/status/?started=2015-01-01T00:00:00Z&ended=2015-01-01T10:00:00Z' % self.version
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)

        entry = result['results'][0]
        self.assertEqual(entry['strike']['id'], self.strike.id)
        self.assertIsNotNone(entry['most_recent'])
        self.assertEqual(entry['files'], 1)
        self.assertEqual(entry['size'], self.ingest3.file_size)
        self.assertEqual(len(entry['values']), 24)

    def test_multiple_strikes(self):
        """Tests successfully calling the ingest status view with multiple strike process groupings."""
        ingest_test_utils.create_strike()
        strike3 = ingest_test_utils.create_strike()
        ingest_test_utils.create_ingest(file_name='test3.txt', status='INGESTED', strike=strike3)

        url = '/%s/ingests/status/' % self.version
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 3)

class TestScansView(TestCase):
    def setUp(self):
        django.setup()

        self.scan1 = ingest_test_utils.create_scan(name='test-1', description='test A')
        self.scan2 = ingest_test_utils.create_scan(name='test-2', description='test Z')

    def test_successful(self):
        """Tests successfully calling the get all scans view."""

        url = rest_util.get_url('/scans/')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 2)
        for entry in result['results']:
            expected = None
            if entry['id'] == self.scan1.id:
                expected = self.scan1
            elif entry['id'] == self.scan2.id:
                expected = self.scan2
            else:
                self.fail('Found unexpected result: %s' % entry['id'])
            self.assertEqual(entry['name'], expected.name)
            self.assertEqual(entry['title'], expected.title)

    def test_name(self):
        """Tests successfully calling the scans view filtered by Scan name."""

        url = rest_util.get_url('/scans/?name=%s' % self.scan1.name)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['name'], self.scan1.name)

    def test_sorting(self):
        """Tests custom sorting."""

        url = rest_util.get_url('/scans/?order=description')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 2)
        self.assertEqual(result['results'][0]['name'], self.scan1.name)
        self.assertEqual(result['results'][1]['name'], self.scan2.name)

    def test_reverse_sorting(self):
        """Tests custom sorting in reverse."""

        url = rest_util.get_url('/scans/?order=-description')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 2)
        self.assertEqual(result['results'][0]['name'], self.scan2.name)
        self.assertEqual(result['results'][1]['name'], self.scan1.name)


class TestScanCreateView(TestCase):
    fixtures = ['ingest_job_types.json']

    def setUp(self):
        django.setup()

        self.workspace = storage_test_utils.create_workspace(name='raw')

    def test_missing_configuration(self):
        """Tests calling the create Scan view with missing configuration."""

        json_data = {
            'name': 'scan-name',
            'title': 'Scan Title',
            'description': 'Scan description',
        }

        url = rest_util.get_url('/scans/')
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_configuration_bad_type(self):
        """Tests calling the create Scan view with configuration that is not a dict."""

        json_data = {
            'name': 'scan-name',
            'title': 'Scan Title',
            'description': 'Scan description',
            'configuration': 123,
        }

        url = rest_util.get_url('/scans/')
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_invalid_configuration(self):
        """Tests calling the create Scan view with invalid configuration."""

        json_data = {
            'name': 'scan-name',
            'title': 'Scan Title',
            'description': 'Scan description',
            'configuration': {
                'version': '1.0',
                'workspace': 'raw',
                'scanner': {'type': 'dir', 'transfer_suffix': '_tmp'},
                'files_to_ingest': [{
                    'filename_regex': '.*txt',
                    'workspace_path': 'my/path',
                    'workspace_name': 'BAD',
                }],
            },
        }

        url = rest_util.get_url('/scans/')
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_successful(self):
        """Tests calling the create Scan view successfully."""

        json_data = {
            'name': 'scan-name',
            'title': 'Scan Title',
            'description': 'Scan description',
            'configuration': {
                'version': '1.0',
                'workspace': 'raw',
                'scanner': {'type': 'dir', 'transfer_suffix': '_tmp'},
                'files_to_ingest': [{
                    'filename_regex': '.*txt',
                    'new_file_path': 'my_path',
                    'new_workspace': 'raw',
                }],
            },
        }

        url = rest_util.get_url('/scans/')
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        scans = Scan.objects.filter(name='scan-name')

        result = json.loads(response.content)
        self.assertEqual(len(scans), 1)
        self.assertEqual(result['title'], scans[0].title)
        self.assertEqual(result['description'], scans[0].description)
        self.assertDictEqual(result['configuration'], scans[0].configuration)


class TestScanDetailsView(TestCase):
    def setUp(self):
        django.setup()

        self.workspace = storage_test_utils.create_workspace(name='raw')
        self.scan = ingest_test_utils.create_scan()

    def test_not_found(self):
        """Tests successfully calling the get Scan process details view with a model id that does not exist."""

        url = rest_util.get_url('/scans/100/')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

    def test_successful(self):
        """Tests successfully calling the get Scan process details view."""

        url = rest_util.get_url('/scans/%d/' % self.scan.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertTrue(isinstance(result, dict), 'result  must be a dictionary')
        self.assertEqual(result['id'], self.scan.id)
        self.assertEqual(result['name'], self.scan.name)

        self.assertIsNone(result['file_count'])
        self.assertIsNone(result['job'])
        self.assertIsNone(result['dry_run_job'])
        self.assertIsNotNone(result['configuration'])

    def test_edit_simple(self):
        """Tests editing only the basic attributes of a Scan process"""

        json_data = {
            'title': 'Title EDIT',
            'description': 'Description EDIT',
        }

        url = rest_util.get_url('/scans/%d/' % self.scan.id)
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertTrue(isinstance(result, dict), 'result  must be a dictionary')
        self.assertEqual(result['id'], self.scan.id)
        self.assertEqual(result['title'], 'Title EDIT')
        self.assertEqual(result['description'], 'Description EDIT')
        self.assertDictEqual(result['configuration'], ScanConfiguration(self.scan.configuration).get_dict())

        scan = Scan.objects.get(pk=self.scan.id)
        self.assertEqual(scan.title, 'Title EDIT')
        self.assertEqual(scan.description, 'Description EDIT')
        
    def test_edit_not_found(self):
        """Tests editing non-existent Scan process"""

        json_data = {
            'title': 'Title EDIT',
            'description': 'Description EDIT',
        }

        url = rest_util.get_url('/scans/100/')
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

    def test_edit_config(self):
        """Tests editing the configuration of a Scan process"""

        config = {
            'version': '1.0',
            'workspace': 'raw',
            'scanner': {'type': 'dir', 'transfer_suffix': '_tmp'},
            'files_to_ingest': [{
                'data_types': ['test'],
                'filename_regex': '.*txt',
                'new_file_path': 'my_path',
                'new_workspace': 'raw',
            }],
        }

        json_data = {
            'configuration': config,
        }

        url = rest_util.get_url('/scans/%d/' % self.scan.id)
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(result['id'], self.scan.id)
        self.assertEqual(result['title'], self.scan.title)
        self.assertDictEqual(result['configuration'], ScanConfiguration(config).get_dict())

        scan = Scan.objects.get(pk=self.scan.id)
        self.assertEqual(scan.title, self.scan.title)
        self.assertDictEqual(scan.configuration, config)
        
    def test_edit_config_conflict(self):
        """Tests editing the configuration of a Scan process already launched"""

        json_data = {
            'configuration': {},
        }

        self.scan.job = job_utils.create_job()
        self.scan.save()
        url = rest_util.get_url('/scans/%d/' % self.scan.id)
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT, response.content)

        result = json.loads(response.content)
        self.assertEqual(result['detail'], 'Ingest Scan already launched')

    def test_edit_bad_config(self):
        """Tests attempting to edit a Scan process using an invalid configuration"""

        config = {
            'version': 'BAD',
            'mount': 'host:/my/path',
            'transfer_suffix': '_tmp',
            'files_to_ingest': [{
                'filename_regex': '.*txt',
                'new_file_path': 'my_path',
                'new_workspace': 'raw',
            }],
        }

        json_data = {
            'configuration': config,
        }

        url = rest_util.get_url('/scans/%d/' % self.scan.id)
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)


class TestScansProcessView(TestCase):
    """Tests related to the Scan process endpoint"""
    fixtures = ['ingest_job_types.json']

    def setUp(self):
        django.setup()

        self.scan = ingest_test_utils.create_scan(name='test-1', description='test A')

    def test_successful_dry_run_unspecified(self):
        """Tests validating launch of a dry run Scan process."""

        url = rest_util.get_url('/scans/%i/process/' % self.scan.id)
        response = self.client.generic('POST', url, '', 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)
        
        updated_scan = Scan.objects.get(pk=self.scan.id)
        
        self.assertIsNotNone(updated_scan.dry_run_job)
        self.assertIsNone(updated_scan.job)

        self.assertIn('http', response['Location'])
        
    def test_successful_dry_run_params(self):
        """Tests validating launch of a dry run Scan process with explicit parameterization."""

        url = rest_util.get_url('/scans/%i/process/?ingest=false' % self.scan.id)
        response = self.client.generic('POST', url, '', 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)
        
        updated_scan = Scan.objects.get(pk=self.scan.id)
        
        self.assertIsNotNone(updated_scan.dry_run_job)
        self.assertIsNone(updated_scan.job)
        
        self.assertIn('http', response['Location'])
        
    def test_successful_ingest_body(self):
        """Tests validating launch of an actual ingest Scan process using JSON body parameters."""

        json_data = { 'ingest': True }
        url = rest_util.get_url('/scans/%i/process/' % self.scan.id)
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)
        
        updated_scan = Scan.objects.get(pk=self.scan.id)
        
        self.assertIsNone(updated_scan.dry_run_job)
        self.assertIsNotNone(updated_scan.job)

        self.assertIn('http', response['Location'])
        
    def test_successful_ingest_params(self):
        """Tests validating launch of an actual ingest Scan process."""

        url = rest_util.get_url('/scans/%i/process/?ingest=true' % self.scan.id)
        response = self.client.generic('POST', url, '', 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)
        
        updated_scan = Scan.objects.get(pk=self.scan.id)
        
        self.assertIsNone(updated_scan.dry_run_job)
        self.assertIsNotNone(updated_scan.job)

        self.assertIn('http', response['Location'])


class TestScansValidationView(TestCase):
    """Tests related to the Scan process validation endpoint"""

    def setUp(self):
        django.setup()

        self.workspace = storage_test_utils.create_workspace(name='raw')

    def test_successful(self):
        """Tests validating a new Scan process."""

        json_data = {
            'name': 'scan-name',
            'title': 'Scan Title',
            'description': 'Scan description',
            'configuration': {
                'version': '1.0',
                'workspace': self.workspace.name,
                'scanner': {'type': 'dir'},
                'files_to_ingest': [{
                    'filename_regex': '.*txt'
                }],
            },
        }

        url = rest_util.get_url('/scans/validation/')
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertDictEqual(results, {'warnings': []}, 'JSON result was incorrect')

    def test_missing_configuration(self):
        """Tests validating a new Scan process with missing configuration."""

        json_data = {
            'name': 'scan-name',
            'title': 'Scan Title',
            'description': 'Scan description',
        }

        url = rest_util.get_url('/scans/validation/')
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_configuration_bad_type(self):
        """Tests validating a new Scan process with configuration that is not a dict."""

        json_data = {
            'name': 'scan-name',
            'title': 'Scan Title',
            'description': 'Scan description',
            'configuration': 123,
        }

        url = rest_util.get_url('/scans/validation/')
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_invalid_configuration(self):
        """Tests validating a new Scan process with invalid configuration."""

        json_data = {
            'name': 'scan-name',
            'title': 'Scan Title',
            'description': 'Scan description',
            'configuration': {
                'workspace': 'raw',
                'scanner': {'type': 'dir', 'transfer_suffix': None},
                'files_to_ingest': [{
                    'filename_regex': '.*txt',
                    'new_file_path': 'my_path',
                    'new_workspace': 'BAD',
                }],
            },
        }

        url = rest_util.get_url('/scans/validation/')
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)


class TestScanProcessView(TestCase):
    fixtures = ['ingest_job_types.json']
    
    def setUp(self):
        django.setup()

        self.workspace = storage_test_utils.create_workspace(name='raw')
        self.scan = ingest_test_utils.create_scan()

    def test_not_found(self):
        """Tests a Scan process launch where the id of Scan is missing."""

        url = rest_util.get_url('/scans/100/process/')
        response = self.client.generic('POST', url, json.dumps({ 'ingest': False }), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

    def test_dry_run_process(self):
        """Tests successfully calling the Scan process view for a dry run Scan."""

        url = rest_util.get_url('/scans/%s/process/' % self.scan.id)
        response = self.client.generic('POST', url, json.dumps({ 'ingest': False }), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)
        
        result = json.loads(response.content)
        self.assertTrue(isinstance(result, dict), 'result  must be a dictionary')
        self.assertIsNotNone(result['dry_run_job'])

    def test_ingest_process(self):
        """Tests successfully calling the Scan process view for an ingest Scan."""

        url = rest_util.get_url('/scans/%s/process/' % self.scan.id)
        response = self.client.generic('POST', url, json.dumps({ 'ingest': True }), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        result = json.loads(response.content)
        self.assertTrue(isinstance(result, dict), 'result  must be a dictionary')
        self.assertIsNotNone(result['job'])

    def test_dry_run_process_conflict(self):
        """Tests error response when calling the Scan process view for a dry run Scan when already processed."""
        
        self.scan.job = job_utils.create_job()
        self.scan.save()

        url = rest_util.get_url('/scans/%s/process/' % self.scan.id)
        response = self.client.generic('POST', url, json.dumps({ 'ingest': False }), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT, response.content)

    def test_ingest_process_conflict(self):
        """Tests error response when calling the Scan process view for an ingest Scan when already processed."""

        self.scan.job = job_utils.create_job()
        self.scan.save()

        url = rest_util.get_url('/scans/%s/process/' % self.scan.id)
        response = self.client.generic('POST', url, json.dumps({ 'ingest': True }), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT, response.content)

    def test_dry_run_process_reprocess(self):
        """Tests successfully calling the Scan process view for a 2nd dry run Scan."""
        
        self.scan.dry_run_job = job_utils.create_job()
        old_job_id = self.scan.dry_run_job.id

        url = rest_util.get_url('/scans/%s/process/' % self.scan.id)
        response = self.client.generic('POST', url, json.dumps({ 'ingest': False }), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        result = json.loads(response.content)
        self.assertTrue(isinstance(result, dict), 'result  must be a dictionary')
        self.assertIsNotNone(result['dry_run_job'])
        self.assertNotEqual(result['dry_run_job']['id'], old_job_id)

    def test_ingest_after_dry_run(self):
        """Tests successfully calling the Scan process view for an ingest Scan. following dry run"""

        self.scan.dry_run_job = job_utils.create_job()

        url = rest_util.get_url('/scans/%s/process/' % self.scan.id)
        response = self.client.generic('POST', url, json.dumps({ 'ingest': True }), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        result = json.loads(response.content)
        self.assertTrue(isinstance(result, dict), 'result  must be a dictionary')
        self.assertIsNotNone(result['job'])


class TestStrikesView(TestCase):

    fixtures = ['ingest_job_types.json']

    def setUp(self):
        django.setup()

        self.strike1 = ingest_test_utils.create_strike(name='test-1', description='test A')
        self.strike2 = ingest_test_utils.create_strike(name='test-2', description='test Z')

    def test_successful(self):
        """Tests successfully calling the get all strikes view."""

        url = rest_util.get_url('/strikes/')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 2)
        for entry in result['results']:
            expected = None
            if entry['id'] == self.strike1.id:
                expected = self.strike1
            elif entry['id'] == self.strike2.id:
                expected = self.strike2
            else:
                self.fail('Found unexpected result: %s' % entry['id'])
            self.assertEqual(entry['name'], expected.name)
            self.assertEqual(entry['title'], expected.title)

    def test_name(self):
        """Tests successfully calling the strikes view filtered by Strike name."""

        url = rest_util.get_url('/strikes/?name=%s' % self.strike1.name)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['name'], self.strike1.name)

    def test_sorting(self):
        """Tests custom sorting."""

        url = rest_util.get_url('/strikes/?order=description')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 2)
        self.assertEqual(result['results'][0]['name'], self.strike1.name)
        self.assertEqual(result['results'][1]['name'], self.strike2.name)

    def test_reverse_sorting(self):
        """Tests custom sorting in reverse."""

        url = rest_util.get_url('/strikes/?order=-description')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 2)
        self.assertEqual(result['results'][0]['name'], self.strike2.name)
        self.assertEqual(result['results'][1]['name'], self.strike1.name)


class TestStrikeCreateView(TestCase):

    fixtures = ['ingest_job_types.json']

    def setUp(self):
        django.setup()

        self.workspace = storage_test_utils.create_workspace(name='raw')

    def test_missing_configuration(self):
        """Tests calling the create Strike view with missing configuration."""

        json_data = {
            'name': 'strike-name',
            'title': 'Strike Title',
            'description': 'Strike description',
        }

        url = rest_util.get_url('/strikes/')
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_configuration_bad_type(self):
        """Tests calling the create Strike view with configuration that is not a dict."""

        json_data = {
            'name': 'strike-name',
            'title': 'Strike Title',
            'description': 'Strike description',
            'configuration': 123,
        }

        url = rest_util.get_url('/strikes/')
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_invalid_configuration(self):
        """Tests calling the create Strike view with invalid configuration."""

        json_data = {
            'name': 'strike-name',
            'title': 'Strike Title',
            'description': 'Strike description',
            'configuration': {
                'mount': 'host:/my/path',
                'transfer_suffix': '_tmp',
                'files_to_ingest': [{
                    'filename_regex': '.*txt',
                    'workspace_path': 'my/path',
                    'workspace_name': 'BAD',
                }],
            },
        }

        url = rest_util.get_url('/strikes/')
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_successful(self):
        """Tests calling the create Strike view successfully."""

        json_data = {
            'name': 'strike-name',
            'title': 'Strike Title',
            'description': 'Strike description',
            'configuration': {
                'version': '1.0',
                'mount': 'host:/my/path',
                'transfer_suffix': '_tmp',
                'files_to_ingest': [{
                    'filename_regex': '.*txt',
                    'workspace_path': 'my/path',
                    'workspace_name': 'raw',
                }],
            },
        }

        url = rest_util.get_url('/strikes/')
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        strikes = Strike.objects.filter(name='strike-name')

        result = json.loads(response.content)
        self.assertEqual(len(strikes), 1)
        self.assertEqual(result['title'], strikes[0].title)
        self.assertEqual(result['description'], strikes[0].description)
        self.assertDictEqual(result['configuration'], strikes[0].configuration)


class TestStrikeDetailsView(TestCase):

    fixtures = ['ingest_job_types.json']

    def setUp(self):
        django.setup()

        self.workspace = storage_test_utils.create_workspace(name='raw')
        self.strike = ingest_test_utils.create_strike()

    def test_not_found(self):
        """Tests successfully calling the get Strike process details view with a model id that does not exist."""

        url = rest_util.get_url('/strikes/100/')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

    def test_successful(self):
        """Tests successfully calling the get Strike process details view."""

        url = rest_util.get_url('/strikes/%d/' % self.strike.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertTrue(isinstance(result, dict), 'result  must be a dictionary')
        self.assertEqual(result['id'], self.strike.id)
        self.assertEqual(result['name'], self.strike.name)
        self.assertIsNotNone(result['job'])
        self.assertIsNotNone(result['configuration'])

    def test_edit_simple(self):
        """Tests editing only the basic attributes of a Strike process"""

        json_data = {
            'title': 'Title EDIT',
            'description': 'Description EDIT',
        }

        url = rest_util.get_url('/strikes/%d/' % self.strike.id)
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertTrue(isinstance(result, dict), 'result  must be a dictionary')
        self.assertEqual(result['id'], self.strike.id)
        self.assertEqual(result['title'], 'Title EDIT')
        self.assertEqual(result['description'], 'Description EDIT')
        self.assertDictEqual(result['configuration'], StrikeConfiguration(self.strike.configuration).get_dict())

        strike = Strike.objects.get(pk=self.strike.id)
        self.assertEqual(strike.title, 'Title EDIT')
        self.assertEqual(strike.description, 'Description EDIT')

    def test_edit_config(self):
        """Tests editing the configuration of a Strike process"""

        config = {
            'version': '1.0',
            'mount': 'host:/my/path/EDIT',
            'transfer_suffix': '_tmp',
            'files_to_ingest': [{
                'data_types': ['test'],
                'filename_regex': '.*txt',
                'workspace_path': 'my_path',
                'workspace_name': 'raw',
            }],
        }

        json_data = {
            'configuration': config,
        }

        url = rest_util.get_url('/strikes/%d/' % self.strike.id)
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(result['id'], self.strike.id)
        self.assertEqual(result['title'], self.strike.title)
        self.assertDictEqual(result['configuration'], StrikeConfiguration(config).get_dict())

        strike = Strike.objects.get(pk=self.strike.id)
        self.assertEqual(strike.title, self.strike.title)
        self.assertDictEqual(strike.configuration, config)

    def test_edit_bad_config(self):
        """Tests attempting to edit a Strike process using an invalid configuration"""

        config = {
            'version': 'BAD',
            'mount': 'host:/my/path',
            'transfer_suffix': '_tmp',
            'files_to_ingest': [{
                'filename_regex': '.*txt',
                'workspace_path': 'my/path',
                'workspace_name': 'raw',
            }],
        }

        json_data = {
            'configuration': config,
        }

        url = rest_util.get_url('/strikes/%d/' % self.strike.id)
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)


class TestStrikesValidationView(TestCase):
    """Tests related to the Strike process validation endpoint"""

    def setUp(self):
        django.setup()

        self.workspace = storage_test_utils.create_workspace(name='raw')

    def test_successful(self):
        """Tests validating a new Strike process."""

        json_data = {
            'name': 'strike-name',
            'title': 'Strike Title',
            'description': 'Strike description',
            'configuration': {
                'version': '1.0',
                'mount': 'host:/my/path',
                'transfer_suffix': '_tmp',
                'files_to_ingest': [{
                    'filename_regex': '.*txt',
                    'workspace_path': 'my/path',
                    'workspace_name': 'raw',
                }],
            },
        }

        url = rest_util.get_url('/strikes/validation/')
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertDictEqual(results, {'warnings': []}, 'JSON result was incorrect')

    def test_missing_configuration(self):
        """Tests validating a new Strike process with missing configuration."""

        json_data = {
            'name': 'strike-name',
            'title': 'Strike Title',
            'description': 'Strike description',
        }

        url = rest_util.get_url('/strikes/validation/')
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_configuration_bad_type(self):
        """Tests validating a new Strike process with configuration that is not a dict."""

        json_data = {
            'name': 'strike-name',
            'title': 'Strike Title',
            'description': 'Strike description',
            'configuration': 123,
        }

        url = rest_util.get_url('/strikes/validation/')
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_invalid_configuration(self):
        """Tests validating a new Strike process with invalid configuration."""

        json_data = {
            'name': 'strike-name',
            'title': 'Strike Title',
            'description': 'Strike description',
            'configuration': {
                'mount': 'host:/my/path',
                'transfer_suffix': '_tmp',
                'files_to_ingest': [{
                    'filename_regex': '.*txt',
                    'workspace_path': 'my/path',
                    'workspace_name': 'BAD',
                }],
            },
        }

        url = rest_util.get_url('/strikes/validation/')
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)
