#@PydevCodeAnalysisIgnore
from __future__ import unicode_literals

import datetime
import json

import django
import django.utils.timezone as timezone
from django.test import TestCase
from rest_framework import status

import ingest.test.utils as ingest_test_utils
import storage.test.utils as storage_test_utils
from ingest.models import Strike


class TestIngestsView(TestCase):

    fixtures = ['ingest_job_types.json']

    def setUp(self):
        django.setup()

        self.ingest1 = ingest_test_utils.create_ingest(file_name='test1.txt', status='QUEUED')
        self.ingest2 = ingest_test_utils.create_ingest(file_name='test2.txt', status='INGESTED')

    def test_successful(self):
        '''Tests successfully calling the ingests view.'''

        url = '/ingests/'
        response = self.client.generic('GET', url)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
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
        '''Tests successfully calling the ingests view.'''

        url = '/ingests/?status=%s' % self.ingest1.status
        response = self.client.generic('GET', url)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['status'], self.ingest1.status)


class TestIngestDetailsView(TestCase):

    fixtures = ['ingest_job_types.json']

    def setUp(self):
        django.setup()

        self.ingest = ingest_test_utils.create_ingest(file_name='test1.txt', status='QUEUED')

    def test_not_found(self):
        '''Tests calling the ingest details view with an id that does not exist.'''

        url = '/ingests/100/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_successful(self):
        '''Tests successfully calling the ingest details view.'''

        url = '/ingests/%d/' % self.ingest.id
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = json.loads(response.content)
        self.assertTrue(isinstance(result, dict), 'result  must be a dictionary')
        self.assertEqual(result['id'], self.ingest.id)
        self.assertEqual(result['file_name'], 'test1.txt')
        self.assertEqual(result['status'], 'QUEUED')


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
        '''Tests successfully calling the ingest status view.'''

        url = '/ingests/status/'
        response = self.client.generic('GET', url)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result['results']), 1)

        entry = result['results'][0]
        self.assertEqual(entry['strike']['id'], self.strike.id)
        self.assertIsNotNone(entry['most_recent'])
        self.assertEqual(entry['files'], 2)
        self.assertEqual(entry['size'], self.ingest2.file_size + self.ingest3.file_size)

    def test_time_range(self):
        '''Tests successfully calling the ingest status view with a time range filter.'''

        url = '/ingests/status/?started=2015-01-01T00:00:00Z'
        response = self.client.generic('GET', url)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result['results']), 1)

        entry = result['results'][0]
        self.assertEqual(entry['strike']['id'], self.strike.id)
        self.assertIsNotNone(entry['most_recent'])
        self.assertEqual(entry['files'], 3)
        self.assertEqual(entry['size'], self.ingest2.file_size + self.ingest3.file_size + self.ingest4.file_size)

    def test_use_ingest_time(self):
        '''Tests successfully calling the ingest status view grouped by ingest time instead of data time.'''

        url = '/ingests/status/?started=2015-02-01T00:00:00Z&ended=2015-03-01T00:00:00Z&use_ingest_time=true'
        response = self.client.generic('GET', url)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result['results']), 1)

        entry = result['results'][0]
        self.assertEqual(entry['strike']['id'], self.strike.id)
        self.assertEqual(entry['most_recent'], '2015-02-01T00:00:00Z')
        self.assertEqual(entry['files'], 1)
        self.assertEqual(entry['size'], self.ingest3.file_size)

    def test_fill_empty_slots(self):
        '''Tests successfully calling the ingest status view with place holder zero values when no data exists.'''

        url = '/ingests/status/?started=2015-01-01T00:00:00Z&ended=2015-01-01T10:00:00Z'
        response = self.client.generic('GET', url)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result['results']), 1)

        entry = result['results'][0]
        self.assertEqual(entry['strike']['id'], self.strike.id)
        self.assertIsNotNone(entry['most_recent'])
        self.assertEqual(entry['files'], 1)
        self.assertEqual(entry['size'], self.ingest3.file_size)
        self.assertEqual(len(entry['values']), 24)

    def test_multiple_strikes(self):
        '''Tests successfully calling the ingest status view with multiple strike process groupings.'''
        ingest_test_utils.create_strike()
        strike3 = ingest_test_utils.create_strike()
        ingest_test_utils.create_ingest(file_name='test3.txt', status='INGESTED', strike=strike3)

        url = '/ingests/status/'
        response = self.client.generic('GET', url)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result['results']), 3)


class TestCreateStrikeView(TestCase):

    fixtures = ['ingest_job_types.json']

    def setUp(self):
        django.setup()

        self.workspace = storage_test_utils.create_workspace()

    def test_missing_configuration(self):
        '''Tests calling the create Strike view with missing configuration.'''

        url = '/strike/create/'
        json_data = {
            'name': 'strike-name',
            'title': 'Strike Title',
            'description': 'Strike description',
        }
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_configuration_bad_type(self):
        '''Tests calling the create Strike view with configuration that is not a dict.'''

        url = '/strike/create/'
        json_data = {
            'name': 'strike-name',
            'title': 'Strike Title',
            'description': 'Strike description',
            'configuration': 123,
        }
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_configuration(self):
        '''Tests calling the create Strike view with invalid configuration.'''

        url = '/strike/create/'
        json_data = {
            'name': 'strike-name',
            'title': 'Strike Title',
            'description': 'Strike description',
            'configuration': {
                'mount': 123,
            }
        }
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_successful(self):
        '''Tests calling the create Strike view successfully.'''

        url = '/strike/create/'
        json_data = {
            'name': 'strike-name',
            'title': 'Strike Title',
            'description': 'Strike description',
            'configuration': {
                'mount': 'host:/my/path',
                'transfer_suffix': '_tmp',
                'files_to_ingest': [{
                    'filename_regex': '.*',
                    'workspace_path': 'my/path',
                    'workspace_name': self.workspace.name,
                }]
            }
        }
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        strike = Strike.objects.all().first()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = json.loads(response.content)
        self.assertDictEqual(result, {'strike_id': strike.id}, 'JSON result was incorrect')
