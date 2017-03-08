from __future__ import unicode_literals

import datetime
import json

import django
import django.utils.timezone as timezone
from django.test import TestCase
from rest_framework import status

import ingest.test.utils as ingest_test_utils
import storage.test.utils as storage_test_utils
import util.rest as rest_util
from ingest.models import Strike
from ingest.strike.configuration.strike_configuration import StrikeConfiguration


class TestIngestsView(TestCase):
    fixtures = ['ingest_job_types.json']

    def setUp(self):
        django.setup()

        self.ingest1 = ingest_test_utils.create_ingest(file_name='test1.txt', status='QUEUED')
        self.ingest2 = ingest_test_utils.create_ingest(file_name='test2.txt', status='INGESTED')

    def test_successful(self):
        """Tests successfully calling the ingests view."""

        url = rest_util.get_url('/ingests/')
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

        url = rest_util.get_url('/ingests/?status=%s' % self.ingest1.status)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['status'], self.ingest1.status)

    def test_strike_id(self):
        """Tests successfully calling the ingests view filtered by strike processor."""

        url = rest_util.get_url('/ingests/?strike_id=%i' % self.ingest1.strike.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['strike']['id'], self.ingest1.strike.id)

    def test_file_name(self):
        """Tests successfully calling the ingests view filtered by file name."""

        url = rest_util.get_url('/ingests/?file_name=%s' % self.ingest1.file_name)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['file_name'], self.ingest1.file_name)


class TestIngestDetailsView(TestCase):
    fixtures = ['ingest_job_types.json']

    def setUp(self):
        django.setup()

        self.ingest = ingest_test_utils.create_ingest(file_name='test1.txt', status='QUEUED')

    def test_id(self):
        """Tests successfully calling the ingests view by id."""

        url = rest_util.get_url('/ingests/%d/' % self.ingest.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(result['id'], self.ingest.id)
        self.assertEqual(result['file_name'], self.ingest.file_name)
        self.assertEqual(result['status'], self.ingest.status)

    def test_file_name(self):
        """Tests successfully calling the ingests view by file name."""

        url = rest_util.get_url('/ingests/%s/' % self.ingest.file_name)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(result['id'], self.ingest.id)
        self.assertEqual(result['file_name'], self.ingest.file_name)
        self.assertEqual(result['status'], self.ingest.status)

    def test_missing(self):
        """Tests calling the ingests view with an invalid id or file name."""

        url = rest_util.get_url('/ingests/12345/')
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

        url = rest_util.get_url('/ingests/missing_file.txt/')
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)


class TestIngestStatusView(TestCase):
    fixtures = ['ingest_job_types.json']

    def setUp(self):
        django.setup()

        self.strike = ingest_test_utils.create_strike()
        self.ingest1 = ingest_test_utils.create_ingest(file_name='test1.txt', status='QUEUED', strike=self.strike)
        self.ingest2 = ingest_test_utils.create_ingest(file_name='test2.txt', status='INGESTED', strike=self.strike)
        self.ingest3 = ingest_test_utils.create_ingest(file_name='test3.txt', status='INGESTED', strike=self.strike)
        self.ingest4 = ingest_test_utils.create_ingest(file_name='test4.txt', status='INGESTED', strike=self.strike,
                                                       data_started=datetime.datetime(2015, 1, 1, tzinfo=timezone.utc),
                                                       ingest_ended=datetime.datetime(2015, 2, 1, tzinfo=timezone.utc))

    def test_successful(self):
        """Tests successfully calling the ingest status view."""

        url = rest_util.get_url('/ingests/status/')
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

        url = rest_util.get_url('/ingests/status/?started=2015-01-01T00:00:00Z')
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

        url = rest_util.get_url('/ingests/status/?started=2015-02-01T00:00:00Z&'
                                'ended=2015-03-01T00:00:00Z&use_ingest_time=true')
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

        url = rest_util.get_url('/ingests/status/?started=2015-01-01T00:00:00Z&ended=2015-01-01T10:00:00Z')
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

        url = rest_util.get_url('/ingests/status/')
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 3)


class TestStrikesView(TestCase):
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
