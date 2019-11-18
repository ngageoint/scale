from __future__ import unicode_literals

import copy
import datetime
import json
import os

import django
from django.test import TestCase, TransactionTestCase
from django.utils.timezone import utc
from rest_framework import status
from mock import patch

import job.test.utils as job_utils
import ingest.test.utils as ingest_test_utils
import recipe.test.utils as recipe_test_utils
import storage.test.utils as storage_test_utils
import util.rest as rest_util
from ingest.models import Scan, Strike
from ingest.strike.configuration.json.configuration_v6 import StrikeConfigurationV6
from rest_framework.test import APITestCase
from util import rest


class TestIngestsViewV6(APITestCase):

    version = 'v6'
    fixtures = ['ingest_job_types.json']

    def setUp(self):
        django.setup()

        self.ingest1 = ingest_test_utils.create_ingest(strike=ingest_test_utils.create_strike(), file_name='test1.txt',
                                                       status='QUEUED')
        self.ingest2 = ingest_test_utils.create_ingest(strike=ingest_test_utils.create_strike(), file_name='test2.txt',
                                                       status='INGESTED', data_type_tags=['type1', 'type2'])
        self.ingest3 = ingest_test_utils.create_ingest(scan=ingest_test_utils.create_scan(), file_name='test3.txt',
                                                       status='QUEUED')

        rest.login_client(self.client)

    def test_successful(self):
        """Tests successfully calling the ingests view."""

        url = '/%s/ingests/' % self.version
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 3)
        for entry in result['results']:
            expected = None
            if entry['id'] == self.ingest1.id:
                expected = self.ingest1
            elif entry['id'] == self.ingest2.id:
                expected = self.ingest2
            elif entry['id'] == self.ingest3.id:
                expected = self.ingest3
            else:
                self.fail('Found unexpected result: %s' % entry['id'])
            self.assertEqual(entry['file_name'], expected.file_name)
            self.assertEqual(entry['status'], expected.status)
            self.assertListEqual(entry['data_type_tags'], expected.data_type_tags)

    def test_status(self):
        """Tests successfully calling the ingests view filtered by status."""

        url = '/%s/ingests/?status=%s' % (self.version, self.ingest1.status)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 2)
        self.assertEqual(result['results'][0]['status'], self.ingest1.status)

    def test_strike_id(self):
        """Tests successfully calling the ingests view filtered by strike processor."""

        url = '/%s/ingests/?strike_id=%i' % (self.version, self.ingest1.strike.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['strike']['id'], self.ingest1.strike.id)

    def test_scan_id(self):
        """Tests successfully calling the ingests view filtered by scan processor."""

        url = '/%s/ingests/?scan_id=%i' % (self.version, self.ingest3.scan.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['scan']['id'], self.ingest3.scan.id)

    def test_file_name(self):
        """Tests successfully calling the ingests view filtered by file name."""

        url = '/%s/ingests/?file_name=%s' % (self.version, self.ingest1.file_name)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['file_name'], self.ingest1.file_name)

        url = '/%s/ingests/?file_name=%s' % (self.version, 'test')
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 3)
        for file in result['results']:
            self.assertIn(file['file_name'], [self.ingest1.file_name, self.ingest2.file_name, self.ingest3.file_name])

class TestIngestDetailsViewV6(APITestCase):
    version = 'v6'
    fixtures = ['ingest_job_types.json']

    def setUp(self):
        django.setup()

        self.config = {
            "broker": {
                "type": "s3",
                "bucket_name": "my_bucket.domain.com",
                "credentials": {
                    "access_key_id": "secret",
                    "secret_access_key": "super-secret"
                },
                "host_path": "/my_bucket",
                "region_name": "us-east-1"
            }
        }

        self.workspace = storage_test_utils.create_workspace(json_config=self.config)

        self.config2 = {
            'workspace': self.workspace.name,
            'monitor': {
                'type': 's3',
                'sqs_name': 'my-sqs',
                'credentials': {
                    "access_key_id": "secret",
                    "secret_access_key": "super-secret"
                }
            },
            'files_to_ingest': [{
                'data_types': [],
                'filename_regex': '.*txt'
            }]
        }

        self.strike = ingest_test_utils.create_strike(configuration=self.config2)

        self.ingest = ingest_test_utils.create_ingest(file_name='test1.txt', status='QUEUED', workspace=self.workspace, strike=self.strike)

        rest.login_client(self.client)

    def test_id(self):
        """Tests successfully calling the ingests view by id."""

        url = '/%s/ingests/%d/' % (self.version, self.ingest.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        self.assertTrue('************' in response.content)
        self.assertFalse('super-secret' in response.content)
        result = json.loads(response.content)
        self.assertEqual(result['id'], self.ingest.id)
        self.assertEqual(result['file_name'], self.ingest.file_name)
        self.assertEqual(result['status'], self.ingest.status)

        rest.login_client(self.client, is_staff=True, username='test2')
        url = '/%s/ingests/%d/' % (self.version, self.ingest.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        self.assertTrue('secret' in response.content)
        self.assertTrue('super-secret' in response.content)

    def test_missing(self):
        """Tests calling the ingests view with an invalid id or file name."""

        url = '/%s/ingests/12345/' % self.version
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

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

        rest.login_client(self.client)

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

class TestScansViewV6(APITestCase):
    api = 'v6'

    def setUp(self):
        django.setup()

        self.scan1 = ingest_test_utils.create_scan(name='test-1', description='test A')
        self.scan2 = ingest_test_utils.create_scan(name='test-2', description='test Z')

        rest.login_client(self.client)

    def test_successful(self):
        """Tests successfully calling the get all scans view."""

        url = '/%s/scans/' % self.api
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

        url = '/%s/scans/?name=%s' % (self.api, self.scan1.name)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['name'], self.scan1.name)

        url = '/%s/scans/?name=%s' % (self.api, 'test')
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 2)
        for scan in result['results']:
            self.assertIn(scan['name'], [self.scan1.name, self.scan2.name])


    def test_sorting(self):
        """Tests custom sorting."""

        url = '/%s/scans/?order=description' % self.api
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 2)
        self.assertEqual(result['results'][0]['name'], self.scan1.name)
        self.assertEqual(result['results'][1]['name'], self.scan2.name)

    def test_reverse_sorting(self):
        """Tests custom sorting in reverse."""

        url = '/%s/scans/?order=-description' % self.api
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 2)
        self.assertEqual(result['results'][0]['name'], self.scan2.name)
        self.assertEqual(result['results'][1]['name'], self.scan1.name)

class TestScanCreateViewV6(APITestCase):
    fixtures = ['ingest_job_types.json']
    api = 'v6'

    def setUp(self):
        django.setup()

        self.workspace = storage_test_utils.create_workspace(name='raw')

        rest.login_client(self.client, is_staff=True)

    def test_missing_configuration(self):
        """Tests calling the create Scan view with missing configuration."""

        json_data = {
            'title': 'Scan Title',
            'description': 'Scan description',
        }

        url = '/%s/scans/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_configuration_bad_type(self):
        """Tests calling the create Scan view with configuration that is not a dict."""

        json_data = {
            'title': 'Scan Title',
            'description': 'Scan description',
            'configuration': 123,
        }

        url = '/%s/scans/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_invalid_configuration(self):
        """Tests calling the create Scan view with invalid configuration."""

        json_data = {
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

        url = '/%s/scans/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_successful(self):
        """Tests calling the create Scan view successfully."""

        json_data = {
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

        url = '/%s/scans/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        scans = Scan.objects.filter(name='scan-title')

        result = json.loads(response.content)
        self.assertEqual(len(scans), 1)
        self.assertEqual(result['title'], scans[0].title)
        self.assertEqual(result['description'], scans[0].description)
        self.assertDictEqual(result['configuration'], scans[0].get_v6_configuration_json())

    def test_successful_v6(self):
        """Tests calling the create Scan view successfully."""

        definition = {
            'input': {
                'files': [{'name': 'INPUT_FILE', 'media_types': ['text/plain'], 'required': True, 'multiple': True}],
                'json': [],
            },
            'nodes': {
                'node_a': {
                    'dependencies': [],
                    'input': {
                        'input_a': {'type': 'recipe', 'input': 'INPUT_FILE'}
                    },
                    'node_type': {
                        'node_type': 'job',
                        'job_type_name': 'job-type-1',
                        'job_type_version': '1.0',
                        'job_type_revision': 1,
                    },
                },
            },
        }
        recipe_type = recipe_test_utils.create_recipe_type_v6(name='test-recipe', definition=definition)

        json_data = {
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
                'recipe': {
                    'name': recipe_type.name,
                    'revision_num': recipe_type.revision_num,
                },
            },
        }

        url = '/%s/scans/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        scans = Scan.objects.filter(name='scan-title')

        result = json.loads(response.content)
        self.assertEqual(len(scans), 1)
        self.assertEqual(result['title'], scans[0].title)
        self.assertEqual(result['description'], scans[0].description)
        self.assertDictEqual(result['configuration'], scans[0].get_v6_configuration_json())


class TestScanDetailsViewV6(APITestCase):

    api = 'v6'

    def setUp(self):
        django.setup()

        self.workspace = storage_test_utils.create_workspace(name='raw')
        self.scan = ingest_test_utils.create_scan()

        rest.login_client(self.client, is_staff=True)

    def test_not_found(self):
        """Tests successfully calling the get Scan process details view with a model id that does not exist."""

        url = '/%s/scans/100/' % self.api
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

    def test_successful(self):
        """Tests successfully calling the get Scan process details view."""

        url = '/%s/scans/%d/' % (self.api, self.scan.id)
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

        url = '/%s/scans/%d/' % (self.api, self.scan.id)
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response.content)

    def test_edit_not_found(self):
        """Tests editing non-existent Scan process"""

        json_data = {
            'title': 'Title EDIT',
            'description': 'Description EDIT',
        }

        url = '/%s/scans/100/' % self.api
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

    def test_edit_config(self):
        """Tests editing the configuration of a Scan process"""

        config = {
            'version': '1.0',
            'workspace': self.workspace.name,
            'scanner': {'type': 'dir', 'transfer_suffix': '_tmp'},
            'files_to_ingest': [{
                'data_types': ['test'],
                'filename_regex': '.*txt',
                'new_file_path': 'my_path',
                'new_workspace': self.workspace.name,
            }],
        }

        json_data = {
            'configuration': config,
        }

        url = '/%s/scans/%d/' % (self.api, self.scan.id)
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response.content)

    def test_edit_config_v6(self):
        """Tests successfully editing an existing scan"""

        definition = {
            'input': {
                'files': [{'name': 'INPUT_FILE', 'media_types': ['text/plain'], 'required': True, 'multiple': True}],
                'json': [],
            },
            'nodes': {
                'node_a': {
                    'dependencies': [],
                    'input': {
                        'input_a': {'type': 'recipe', 'input': 'INPUT_FILE'}
                    },
                    'node_type': {
                        'node_type': 'job',
                        'job_type_name': 'job-type-1',
                        'job_type_version': '1.0',
                        'job_type_revision': 1,
                    },
                },
            },
        }
        recipe_type = recipe_test_utils.create_recipe_type_v6(name='test-recipe', definition=definition)

        config = {
            'workspace': 'raw',
            'scanner': {'type': 'dir', 'transfer_suffix': '_tmp'},
            'files_to_ingest': [{
                'filename_regex': '.*txt',
                'new_file_path': 'my_path',
                'new_workspace': 'raw',
            }],
            'recipe': {
                'name': recipe_type.name,
                'revision_num': recipe_type.revision_num,
            },
        }

        json_data = {
            'configuration': config
        }
        url = '/%s/scans/%d/' % (self.api, self.scan.id)
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response.content)

    def test_edit_bad_recipe(self):
        """Tests editing a scan configuration with an invalid recipe"""

        config = {
            'workspace': 'raw',
            'scanner': {'type': 'dir', 'transfer_suffix': '_tmp'},
            'files_to_ingest': [{
                'filename_regex': '.*txt',
                'new_file_path': 'my_path',
                'new_workspace': 'raw',
            }],
            'recipe': {
                'name': 'test-recipe',
                'revision_num': '1',
            },
        }

        json_data = {
            'configuration': config
        }
        url = '/%s/scans/%d/' % (self.api, self.scan.id)
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)


    def test_edit_config_conflict(self):
        """Tests editing the configuration of a Scan process already launched"""

        json_data = {
            'configuration': {},
        }

        self.scan.job = job_utils.create_job()
        self.scan.save()
        url = '/%s/scans/%d/' % (self.api, self.scan.id)
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

        url = '/%s/scans/%d/' % (self.api, self.scan.id)
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)


class TestScansValidationViewV6(APITestCase):
    """Tests related to the Scan process validation endpoint"""
    api ='v6'

    def setUp(self):
        django.setup()

        rest.login_client(self.client)

        self.workspace = storage_test_utils.create_workspace(name='raw')

    def test_successful(self):
        """Tests validating a new Scan process."""

        json_data = {
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

        url = '/%s/scans/validation/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        valid_results_dict = {'is_valid': True, 'errors': [], 'warnings': []}
        self.assertDictEqual(results, valid_results_dict)

    def test_successful_recipe(self):
        """Tests validating a new Scan process."""

        jt1 = job_utils.create_seed_job_type()
        recipe_type_def = {'version': '6',
                           'input': {'files': [{'name': 'INPUT_FILE',
                                                'media_types': ['text/plain'],
                                                'required': True,
                                                'multiple': True}],
                                    'json': []},
                           'nodes': {'node_a': {'dependencies': [],
                                                'input': {'INPUT_FILE': {'type': 'recipe', 'input': 'INPUT_FILE'}},
                                                'node_type': {'node_type': 'job', 'job_type_name': jt1.name,
                                                              'job_type_version': jt1.version,
                                                              'job_type_revision': 1}}}}

        recipe = recipe_test_utils.create_recipe_type_v6(name='test-recipe', definition=recipe_type_def)

        json_data = {
            'title': 'Scan Title',
            'description': 'Scan description',
            'configuration': {
                'version': '1.0',
                'workspace': self.workspace.name,
                'scanner': {'type': 'dir'},
                'files_to_ingest': [{
                    'filename_regex': '.*txt'
                }],
                'recipe': {
                    'name': recipe.name,
                    'revision_num': recipe.revision_num,
                },
            },
        }

        url = '/%s/scans/validation/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        valid_results_dict = {'is_valid': True, 'errors': [], 'warnings': []}
        self.assertDictEqual(results, valid_results_dict)

    def test_missing_configuration(self):
        """Tests validating a new Scan process with missing configuration."""

        json_data = {
            'title': 'Scan Title',
            'description': 'Scan description',
        }

        url = '/%s/scans/validation/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_configuration_bad_type(self):
        """Tests validating a new Scan process with configuration that is not a dict."""

        json_data = {
            'title': 'Scan Title',
            'description': 'Scan description',
            'configuration': 123,
        }

        url = '/%s/scans/validation/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_invalid_configuration(self):
        """Tests validating a new Scan process with invalid configuration."""

        json_data = {
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

        url = '/%s/scans/validation/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertDictEqual(results, {u'errors': [{u'description': u'Unknown workspace name: BAD',
                                                    u'name': u'INVALID_SCAN_CONFIGURATION'}], u'is_valid': False, u'warnings': []})

class TestScansProcessViewV6(APITestCase):
    fixtures = ['ingest_job_types.json']
    api = 'v6'

    def setUp(self):
        django.setup()

        self.workspace = storage_test_utils.create_workspace(name='raw')
        self.scan = ingest_test_utils.create_scan()

        rest.login_client(self.client, is_staff=True)

    def test_not_found(self):
        """Tests a Scan process launch where the id of Scan is missing."""

        url = '/%s/scans/100/process/' % self.api
        response = self.client.generic('POST', url, json.dumps({ 'ingest': False }), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

    @patch('ingest.models.CommandMessageManager')
    def test_dry_run_process(self, mock_msg_mgr):
        """Tests successfully calling the Scan process view for a dry run Scan."""

        url = '/%s/scans/%d/process/' % (self.api, self.scan.id)
        response = self.client.generic('POST', url, json.dumps({ 'ingest': False }), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        result = json.loads(response.content)
        self.assertTrue(isinstance(result, dict), 'result  must be a dictionary')
        self.assertIsNotNone(result['dry_run_job'])

    @patch('ingest.models.CommandMessageManager')
    def test_ingest_process(self, mock_msg_mgr):
        """Tests successfully calling the Scan process view for an ingest Scan."""

        url = '/%s/scans/%d/process/' % (self.api, self.scan.id)
        response = self.client.generic('POST', url, json.dumps({ 'ingest': True }), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        result = json.loads(response.content)
        self.assertTrue(isinstance(result, dict), 'result  must be a dictionary')
        self.assertIsNotNone(result['job'])

    def test_dry_run_process_conflict(self):
        """Tests error response when calling the Scan process view for a dry run Scan when already processed."""

        self.scan.job = job_utils.create_job()
        self.scan.save()

        url = '/%s/scans/%d/process/' % (self.api, self.scan.id)
        response = self.client.generic('POST', url, json.dumps({ 'ingest': False }), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT, response.content)

    def test_ingest_process_conflict(self):
        """Tests error response when calling the Scan process view for an ingest Scan when already processed."""

        self.scan.job = job_utils.create_job()
        self.scan.save()

        url = '/%s/scans/%d/process/' % (self.api, self.scan.id)
        response = self.client.generic('POST', url, json.dumps({ 'ingest': True }), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT, response.content)

    @patch('ingest.models.CommandMessageManager')
    def test_dry_run_process_reprocess(self, mock_msg_mgr):
        """Tests successfully calling the Scan process view for a 2nd dry run Scan."""

        self.scan.dry_run_job = job_utils.create_job()
        old_job_id = self.scan.dry_run_job.id

        url = '/%s/scans/%d/process/' % (self.api, self.scan.id)
        response = self.client.generic('POST', url, json.dumps({ 'ingest': False }), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        result = json.loads(response.content)
        self.assertTrue(isinstance(result, dict), 'result  must be a dictionary')
        self.assertIsNotNone(result['dry_run_job'])
        self.assertNotEqual(result['dry_run_job']['id'], old_job_id)

    @patch('ingest.models.CommandMessageManager')
    def test_ingest_after_dry_run(self, mock_msg_mgr):
        """Tests successfully calling the Scan process view for an ingest Scan. following dry run"""

        self.scan.dry_run_job = job_utils.create_job()

        url = '/%s/scans/%d/process/' % (self.api, self.scan.id)
        response = self.client.generic('POST', url, json.dumps({ 'ingest': True }), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        result = json.loads(response.content)
        self.assertTrue(isinstance(result, dict), 'result  must be a dictionary')
        self.assertIsNotNone(result['job'])

    @patch('ingest.models.CommandMessageManager')
    @patch('ingest.models.create_cancel_jobs_messages')
    def test_cancel_scan_job(self, msg_create, mock_msg_mgr):
        """Tests successfully calling the Scan process view for an ingest Scan. following dry run"""

        self.scan.job = job_utils.create_job()
        self.scan.save()
        self.ingest = ingest_test_utils.create_ingest(scan=self.scan, file_name='test3.txt',
                                                       status='QUEUED')

        url = '/%s/scans/cancel/%d/' % (self.api, self.scan.id)
        response = self.client.generic('POST', url, json.dumps({ 'ingest': True }), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED, response.content)
        
        result = json.loads(response.data)

        msg_create.assert_called()
        mock_msg_mgr.assert_called()

        self.assertEqual(len(result), 2)

    @patch('ingest.models.CommandMessageManager')
    @patch('ingest.models.create_cancel_jobs_messages')
    def test_cancel_scan_job_nothing_to_cancel(self, msg_create, mock_msg_mgr):
        """Tests no cancel messages generated when jobs are not in a cancelable state"""

        self.scan.job = job_utils.create_job()
        self.scan.job.status = "COMPLETED"
        self.scan.job.save()
        self.scan.save()
        self.ingest = ingest_test_utils.create_ingest(scan=self.scan, file_name='test3.txt',
                                                       status='QUEUED')
        self.ingest.job.status = "CANCELED"
        self.ingest.job.save()

        url = '/%s/scans/cancel/%d/' % (self.api, self.scan.id)
        response = self.client.generic('POST', url, json.dumps({ 'ingest': True }), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED, response.content)
        
        result = json.loads(response.data)

        msg_create.assert_not_called()
        mock_msg_mgr.assert_not_called()

        self.assertEqual(len(result), 0)

    @patch('ingest.models.CommandMessageManager')
    @patch('ingest.models.create_cancel_jobs_messages')
    def test_cancel_scan_broken_ingest_job(self, msg_create, mock_msg_mgr):
        """Tests no cancel messages generated when jobs are not in a cancelable state"""

        self.scan.job = job_utils.create_job()
        self.scan.save()
        self.ingest = ingest_test_utils.create_ingest(scan=self.scan, file_name='test3.txt',
                                                       status='QUEUED')
        self.ingest.job = None
        self.ingest.save()

        url = '/%s/scans/cancel/%d/' % (self.api, self.scan.id)
        response = self.client.generic('POST', url, json.dumps({ 'ingest': True }), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED, response.content)
        
        result = json.loads(response.data)

        msg_create.assert_called()
        mock_msg_mgr.assert_called()

        self.assertEqual(len(result), 1)

class TestStrikesViewV6(APITestCase):

    version = 'v6'
    fixtures = ['ingest_job_types.json']

    def setUp(self):
        django.setup()

        self.strike1 = ingest_test_utils.create_strike(name='test-1', description='test A')
        self.strike2 = ingest_test_utils.create_strike(name='test-2', description='test Z')

        rest.login_client(self.client)

    def test_successful(self):
        """Tests successfully calling the get all strikes view."""

        url = '/%s/strikes/' % self.version
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

        url = '/%s/strikes/?name=%s' % (self.version, self.strike1.name)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['name'], self.strike1.name)

    def test_sorting(self):
        """Tests custom sorting."""

        url = '/%s/strikes/?order=description' % self.version
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 2)
        self.assertEqual(result['results'][0]['name'], self.strike1.name)
        self.assertEqual(result['results'][1]['name'], self.strike2.name)

    def test_reverse_sorting(self):
        """Tests custom sorting in reverse."""

        url = '/%s/strikes/?order=-description' % self.version
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 2)
        self.assertEqual(result['results'][0]['name'], self.strike2.name)
        self.assertEqual(result['results'][1]['name'], self.strike1.name)

class TestStrikeCreateViewV6(APITestCase):

    version = 'v6'
    fixtures = ['ingest_job_types.json']

    def setUp(self):
        django.setup()

        self.workspace = storage_test_utils.create_workspace(name='raw')
        self.new_workspace = storage_test_utils.create_workspace(name='new')

        rest.login_client(self.client, is_staff=True)

    def test_missing_configuration(self):
        """Tests calling the create Strike view with missing configuration."""

        json_data = {
            'name': 'strike-name',
            'title': 'Strike Title',
            'description': 'Strike description',
        }

        url = '/%s/strikes/' % self.version
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_configuration_bad_type(self):
        """Tests calling the create Strike view with configuration that is not a dict."""

        json_data = {
            'title': 'Strike Title',
            'description': 'Strike description',
            'configuration': 123,
        }

        url = '/%s/strikes/' % self.version
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_invalid_configuration(self):
        """Tests calling the create Strike view with invalid configuration."""

        json_data = {
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

        url = '/%s/strikes/' % self.version
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    @patch('ingest.models.CommandMessageManager')
    def test_successful(self, mock_msg_mgr):
        """Tests calling the create Strike view successfully."""

        recipe_type = recipe_test_utils.create_recipe_type_v6()

        json_data = {
            'title': 'Strike Title',
            'description': 'Strike description',
            'configuration': {
                'version': '6',
                'workspace': self.workspace.name,
                'monitor': {
                    'type': 'dir-watcher',
                    'transfer_suffix': '_tmp',
                },
                'files_to_ingest': [{
                    'filename_regex': '.*txt',
                    'data_types': ['one', 'two'],
                    'new_file_path': os.path.join('my', 'path'),
                    'new_workspace': self.new_workspace.name,
                }],
                'recipe': {
                    'name': recipe_type.name,
                    'revision_num': recipe_type.revision_num,
                },
            },
        }

        url = '/%s/strikes/' % self.version
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        strikes = Strike.objects.filter(name='strike-title')

        result = json.loads(response.content)
        self.assertEqual(len(strikes), 1)
        self.assertEqual(result['title'], strikes[0].title)
        self.assertEqual(result['description'], strikes[0].description)
        self.assertDictEqual(result['configuration'], strikes[0].get_v6_configuration_json())

    @patch('ingest.models.CommandMessageManager')
    def test_successful_v6(self, mock_msg_mgr):
        """Tests creating strike with recipe configuration"""

        definition = {
            'input': {
                'files': [{'name': 'INPUT_FILE', 'media_types': ['text/plain'], 'required': True, 'multiple': True}],
                'json': [],
            },
            'nodes': {
                'node_a': {
                    'dependencies': [],
                    'input': {
                        'input_a': {'type': 'recipe', 'input': 'INPUT_FILE'}
                    },
                    'node_type': {
                        'node_type': 'job',
                        'job_type_name': 'job-type-1',
                        'job_type_version': '1.0',
                        'job_type_revision': 1,
                    },
                },
            },
        }
        recipe_type = recipe_test_utils.create_recipe_type_v6(name='test-recipe', definition=definition)

        json_data = {
            'title': 'Strike Title',
            'description': 'Strike description',
            'configuration': {
                'version': '6',
                'workspace': self.workspace.name,
                'monitor': {
                    'type': 'dir-watcher',
                    'transfer_suffix': '_tmp',
                },
                'files_to_ingest': [{
                    'filename_regex': '.*txt',
                    'data_types': ['one', 'two'],
                    'new_file_path': os.path.join('my', 'path'),
                    'new_workspace': self.new_workspace.name,
                }],
                'recipe': {
                    'name': recipe_type.name,
                    'revision_num': recipe_type.revision_num,
                },
            },
        }

        url = '/%s/strikes/' % self.version
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        strikes = Strike.objects.filter(name='strike-title')
        result = json.loads(response.content)
        self.assertEqual(len(strikes), 1)
        self.assertEqual(result['title'], strikes[0].title)
        self.assertEqual(result['description'], strikes[0].description)
        self.assertDictEqual(result['configuration'], strikes[0].get_v6_configuration_json())

class TestStrikeDetailsViewV6(APITestCase):

    version = 'v6'
    fixtures = ['ingest_job_types.json']

    def setUp(self):
        django.setup()

        self.workspace = storage_test_utils.create_workspace(name='raw')

        self.strike = ingest_test_utils.create_strike()

        self.config = {
            "broker": {
                "type": "s3",
                "bucket_name": "my_bucket.domain.com",
                "credentials": {
                    "access_key_id": "secret",
                    "secret_access_key": "super-secret"
                },
                "host_path": "/my_bucket",
                "region_name": "us-east-1"
            }
        }

        self.workspace2 = storage_test_utils.create_workspace(name='raw2', json_config=self.config)

        self.config2 = {
            'workspace': self.workspace2.name,
            'monitor': {
                'type': 's3',
                'sqs_name': 'my-sqs',
                'credentials': {
                    "access_key_id": "secret",
                    "secret_access_key": "super-secret"
                }
            },
            'files_to_ingest': [{
                'data_types': [],
                'filename_regex': '.*txt'
            }]
        }
        self.secret_config = copy.deepcopy(self.config2)
        self.secret_config['monitor']['credentials']['access_key_id'] = '************'
        self.secret_config['monitor']['credentials']['secret_access_key'] = '************'
        self.strike2 = ingest_test_utils.create_strike(configuration=self.config2)

        rest.login_client(self.client, is_staff=True)

    def test_not_found(self):
        """Tests successfully calling the get Strike process details view with a model id that does not exist."""

        url = '/%s/strikes/100/' % self.version
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

    def test_successful(self):
        """Tests successfully calling the get Strike process details view."""

        url = '/%s/strikes/%d/' % (self.version, self.strike.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertTrue(isinstance(result, dict), 'result  must be a dictionary')
        self.assertEqual(result['id'], self.strike.id)
        self.assertEqual(result['name'], self.strike.name)
        self.assertIsNotNone(result['job'])
        self.maxDiff = None
        del self.strike.configuration['version']
        self.assertDictEqual(result['configuration'], self.strike.configuration)

        url = '/%s/strikes/%d/' % (self.version, self.strike2.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        result = json.loads(response.content)
        self.assertDictEqual(result['configuration'], self.config2)


        rest.login_client(self.client, is_staff=False, username='test2')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        result = json.loads(response.content)
        self.assertTrue(isinstance(result, dict), 'result  must be a dictionary')
        self.assertEqual(result['id'], self.strike2.id)
        self.assertEqual(result['name'], self.strike2.name)
        self.assertIsNotNone(result['job'])
        self.assertDictEqual(result['configuration'], self.secret_config)

    def test_edit_simple(self):
        """Tests editing only the basic attributes of a Strike process"""

        json_data = {
            'title': 'Title EDIT',
            'description': 'Description EDIT',
        }

        url = '/%s/strikes/%d/' % (self.version, self.strike.id)
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response.content)

    @patch('ingest.views.CommandMessageManager')
    @patch('ingest.views.create_requeue_jobs_messages')
    def test_edit_config(self, mock_msg_mgr, mock_create):
        """Tests editing the configuration of a Strike process"""

        recipe_type = recipe_test_utils.create_recipe_type_v6()
        config = {
            'workspace': self.workspace.name,
            'monitor': {
                'type': 'dir-watcher',
                'transfer_suffix': '_tmp',
            },
            'files_to_ingest': [{
                'filename_regex': '.*txt',
                'data_types': ['test'],
                'new_file_path': os.path.join('my', 'path', 'EDIT'),
                'new_workspace': self.workspace.name,
            }],
            'recipe': {
                'name': recipe_type.name,
                'revision_num': recipe_type.revision_num,
            },
        }

        json_data = {
            'configuration': config,
        }

        url = '/%s/strikes/%d/' % (self.version, self.strike.id)
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response.content)
        mock_msg_mgr.assert_called_once()
        mock_create.assert_called_once()

    @patch('ingest.views.CommandMessageManager')
    @patch('ingest.views.create_requeue_jobs_messages')
    def test_edit_config_v6(self, mock_msg_mgr, mock_create):
        """Tests attempting to edit a Strike process adding a recipe configuration"""
        new_workspace = storage_test_utils.create_workspace(name='prods')

        definition = {
            'input': {
                'files': [{'name': 'INPUT_FILE', 'media_types': ['text/plain'], 'required': True, 'multiple': True}],
                'json': [],
            },
            'nodes': {
                'node_a': {
                    'dependencies': [],
                    'input': {
                        'input_a': {'type': 'recipe', 'input': 'INPUT_FILE'}
                    },
                    'node_type': {
                        'node_type': 'job',
                        'job_type_name': 'job-type-1',
                        'job_type_version': '1.0',
                        'job_type_revision': 1,
                    },
                },
            },
        }
        recipe_type = recipe_test_utils.create_recipe_type_v6(name='test-recipe', definition=definition)

        config = {
            'workspace': self.workspace.name,
            'monitor': {
                'type': 'dir-watcher',
                'transfer_suffix': '_tmp',
            },
            'files_to_ingest': [{
                'filename_regex': '.*txt',
                'data_types': ['one', 'two'],
                'new_file_path': os.path.join('my', 'path'),
                'new_workspace': new_workspace.name,
            }],
            'recipe': {
                'name': recipe_type.name,
                'revision_num': recipe_type.revision_num,
            },
        }

        json_data = {
            'configuration': config
        }

        url = '/%s/strikes/%d/' % (self.version, self.strike.id)
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response.content)

        strike = Strike.objects.get(pk=self.strike.id)
        self.assertDictEqual(strike.get_v6_configuration_json(), config)
        mock_msg_mgr.assert_called_once()
        mock_create.assert_called_once()

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

        url = '/%s/strikes/%d/' % (self.version, self.strike.id)
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_edit_invalid_recipe(self):
        """Tests attempting to edit a Strike process with a nonexistant recipe"""
        config = {
            'workspace': self.workspace.name,
            'monitor': {
                'type': 'dir-watcher',
                'transfer_suffix': '_tmp',
            },
            'files_to_ingest': [{
                'filename_regex': '.*txt',
                'data_types': ['one', 'two'],
                'new_file_path': os.path.join('my', 'path'),
                'new_workspace': self.workspace.name,
            }],
            'recipe': {
                'name': 'test-recipe',
                'revision_num': '1',
            },
        }

        json_data = {
            'configuration': config
        }

        url = '/%s/strikes/%d/' % (self.version, self.strike.id)
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

class TestStrikesValidationViewV6(APITestCase):
    """Tests related to the Strike process validation endpoint"""

    version = 'v6'

    def setUp(self):
        django.setup()

        rest.login_client(self.client)

        self.workspace = storage_test_utils.create_workspace(name='raw')

    def test_successful(self):
        """Tests validating a new Strike process."""
        recipe_type = recipe_test_utils.create_recipe_type_v6()

        json_data = {
            'name': 'strike-name',
            'title': 'Strike Title',
            'description': 'Strike description',
            'configuration': {
                'version': '6',
                'workspace': self.workspace.name,
                'monitor': {
                    'type': 'dir-watcher',
                    'transfer_suffix': '_tmp',
                },
                'files_to_ingest': [{
                    'filename_regex': '.*txt',
                    'data_types': ['one', 'two'],
                    'new_file_path': os.path.join('my', 'path'),
                    'new_workspace': self.workspace.name,
                }],
                'recipe': {
                    'name': recipe_type.name,
                    'revision_num': recipe_type.revision_num,
                },
            },
        }

        url = '/%s/strikes/validation/' % self.version
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        valid_results_dict = {'is_valid': True, 'errors': [], 'warnings': []}
        self.assertDictEqual(results, valid_results_dict)

    def test_successful_recipe(self):
        """Tests validating a new Scan process."""

        jt1 = job_utils.create_seed_job_type()
        recipe_type_def = {'version': '6',
                           'input': {'files': [{'name': 'INPUT_FILE',
                                                'media_types': ['text/plain'],
                                                'required': True,
                                                'multiple': True}],
                                    'json': []},
                           'nodes': {'node_a': {'dependencies': [],
                                                'input': {'INPUT_FILE': {'type': 'recipe', 'input': 'INPUT_FILE'}},
                                                'node_type': {'node_type': 'job', 'job_type_name': jt1.name,
                                                              'job_type_version': jt1.version,
                                                              'job_type_revision': 1}}}}

        recipe = recipe_test_utils.create_recipe_type_v6(name='test-recipe', definition=recipe_type_def)

        json_data = {
            'name': 'strike-name',
            'title': 'Strike Title',
            'description': 'Strike description',
            'configuration': {
                'version': '6',
                'workspace': self.workspace.name,
                'monitor': {
                    'type': 'dir-watcher',
                    'transfer_suffix': '_tmp',
                },
                'files_to_ingest': [{
                    'filename_regex': '.*txt',
                    'data_types': ['one', 'two'],
                    'new_file_path': os.path.join('my', 'path'),
                    'new_workspace': self.workspace.name,
                }],
                'recipe': {
                    'name': recipe.name,
                    'revision_num': recipe.revision_num
                },
            },
        }

        url = '/%s/strikes/validation/' % self.version
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        valid_results_dict = {'is_valid': True, 'errors': [], 'warnings': []}
        self.assertDictEqual(results, valid_results_dict)

    def test_missing_configuration(self):
        """Tests validating a new Strike process with missing configuration."""

        json_data = {
            'name': 'strike-name',
            'title': 'Strike Title',
            'description': 'Strike description',
        }

        url = '/%s/strikes/validation/' % self.version
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

        url = '/%s/strikes/validation/' % self.version
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
                'recipe': {
                    'name': 'name',
                },
            },
        }

        url = '/%s/strikes/validation/' % self.version
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertEqual(results['errors'][0]['name'], u'INVALID_STRIKE_CONFIGURATION')
        self.assertEqual(results['is_valid'], False)