#@PydevCodeAnalysisIgnore
from __future__ import unicode_literals

import datetime
import json
import time

import django
import django.utils.timezone as timezone
from django.test import TestCase, TransactionTestCase
from rest_framework import status

import error.test.utils as error_test_utils
import job.test.utils as job_test_utils
import storage.test.utils as storage_test_utils
import trigger.test.utils as trigger_test_utils
from error.models import Error
from job.models import JobType


class TestJobsView(TestCase):

    def setUp(self):
        django.setup()

        self.job_type1 = job_test_utils.create_job_type(name='test1', version='1.0', category='test-1')
        self.job1 = job_test_utils.create_job(job_type=self.job_type1, status='RUNNING')

        self.job_type2 = job_test_utils.create_job_type(name='test2', version='1.0', category='test-2')
        self.job2 = job_test_utils.create_job(job_type=self.job_type2, status='PENDING')

    def test_successful(self):
        '''Tests successfully calling the jobs view.'''

        url = '/jobs/'
        response = self.client.generic('GET', url)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result['results']), 2)
        for entry in result['results']:
            expected = None
            if entry['id'] == self.job1.id:
                expected = self.job1
            elif entry['id'] == self.job2.id:
                expected = self.job2
            else:
                self.fail('Found unexpected result: %s' % entry['id'])
            self.assertEqual(entry['job_type']['name'], expected.job_type.name)
            self.assertEqual(entry['job_type_rev']['job_type']['id'], expected.job_type.id)

    def test_status(self):
        '''Tests successfully calling the jobs view filtered by status.'''

        url = '/jobs/?status=RUNNING'
        response = self.client.generic('GET', url)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['job_type']['id'], self.job1.job_type.id)

    def test_job_type_id(self):
        '''Tests successfully calling the jobs view filtered by job type identifier.'''

        url = '/jobs/?job_type_id=%s' % self.job1.job_type.id
        response = self.client.generic('GET', url)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['job_type']['id'], self.job1.job_type.id)

    def test_job_type_name(self):
        '''Tests successfully calling the jobs view filtered by job type name.'''

        url = '/jobs/?job_type_name=%s' % self.job1.job_type.name
        response = self.client.generic('GET', url)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['job_type']['name'], self.job1.job_type.name)

    def test_job_type_category(self):
        '''Tests successfully calling the jobs view filtered by job type category.'''

        url = '/jobs/?job_type_category=%s' % self.job1.job_type.category
        response = self.client.generic('GET', url)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['job_type']['category'], self.job1.job_type.category)

    def test_order_by(self):
        '''Tests successfully calling the jobs view with sorting.'''

        job_type1b = job_test_utils.create_job_type(name='test1', version='2.0', category='test-1')
        job_test_utils.create_job(job_type=job_type1b, status='RUNNING')

        job_type1c = job_test_utils.create_job_type(name='test1', version='3.0', category='test-1')
        job_test_utils.create_job(job_type=job_type1c, status='RUNNING')

        url = '/jobs/?order=job_type__name&order=-job_type__version'
        response = self.client.generic('GET', url)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result['results']), 4)
        self.assertEqual(result['results'][0]['job_type']['id'], job_type1c.id)
        self.assertEqual(result['results'][1]['job_type']['id'], job_type1b.id)
        self.assertEqual(result['results'][2]['job_type']['id'], self.job_type1.id)
        self.assertEqual(result['results'][3]['job_type']['id'], self.job_type2.id)


class TestJobDetailsView(TestCase):

    def setUp(self):
        django.setup()

        self.file = storage_test_utils.create_file()
        self.job = job_test_utils.create_job(
            data={'input_data': [{'name': 'input_file', 'file_id': self.file.id}]},
        )

        # Attempt to stage related models
        self.job_exe = job_test_utils.create_job_exe(job=self.job)

        try:
            import recipe.test.utils as recipe_test_utils
            self.recipe = recipe_test_utils.create_recipe()
            self.recipe_job = recipe_test_utils.create_recipe_job(self.recipe, job=self.job)
        except:
            self.recipe = None
            self.receip_job = None

        try:
            import product.test.utils as product_test_utils
            self.product = product_test_utils.create_product(job_exe=self.job_exe)
        except:
            self.product = None

    def test_successful(self):
        '''Tests successfully calling the jobs view.'''

        url = '/jobs/%i/' % self.job.id
        response = self.client.generic('GET', url)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(result['job_type']['name'], self.job.job_type.name)
        self.assertEqual(result['job_type_rev']['job_type']['id'], self.job.job_type.id)
        self.assertEqual(len(result['input_files']), 1)
        self.assertEqual(result['input_files'][0]['id'], self.file.id)

        if self.job_exe:
            self.assertEqual(result['job_exes'][0]['command_arguments'], self.job_exe.command_arguments)
        else:
            self.assertEqual(len(result['job_exes']), 0)

        if self.recipe:
            self.assertEqual(result['recipes'][0]['recipe_type']['name'], self.recipe.recipe_type.name)
        else:
            self.assertEqual(len(result['recipes']), 0)

        if self.product:
            self.assertEqual(result['products'][0]['file_name'], self.product.file_name)
        else:
            self.assertEqual(len(result['products']), 0)

    def test_cancel_successful(self):
        '''Tests successfully cancelling a job.'''

        url = '/jobs/%i/' % self.job.id
        data = {'status': 'CANCELED'}
        response = self.client.patch(url, json.dumps(data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'CANCELED')

    def test_cancel_bad_param(self):
        '''Tests successfully cancelling a job.'''

        url = '/jobs/%i/' % self.job.id
        data = {'foo': 'bar'}
        response = self.client.patch(url, json.dumps(data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cancel_bad_value(self):
        '''Tests successfully cancelling a job.'''

        url = '/jobs/%i/' % self.job.id
        data = {'status': 'COMPLETED'}
        response = self.client.patch(url, json.dumps(data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestJobsUpdateView(TestCase):

    def setUp(self):
        django.setup()

        self.file = storage_test_utils.create_file()

        self.job_type1 = job_test_utils.create_job_type(name='test1', category='test-1')
        self.job1 = job_test_utils.create_job(
            job_type=self.job_type1, status='RUNNING',
            data={'input_data': [{'name': 'input_file', 'file_id': self.file.id}]},
        )

        self.job_type2 = job_test_utils.create_job_type(name='test2', category='test-2')
        self.job2 = job_test_utils.create_job(
            job_type=self.job_type2, status='PENDING',
            data={'input_data': [{'name': 'input_file', 'file_id': self.file.id}]},
        )

    def test_successful(self):
        '''Tests successfully calling the jobs view.'''

        url = '/jobs/updates/'
        response = self.client.generic('GET', url)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result['results']), 2)
        for entry in result['results']:
            expected = None
            if entry['id'] == self.job1.id:
                expected = self.job1
            elif entry['id'] == self.job2.id:
                expected = self.job2
            else:
                self.fail('Found unexpected result: %s' % entry['id'])
            self.assertEqual(entry['job_type']['name'], expected.job_type.name)
            self.assertEqual(len(entry['input_files']), 1)
            self.assertEqual(entry['input_files'][0]['id'], self.file.id)

    def test_status(self):
        '''Tests successfully calling the jobs view filtered by status.'''

        url = '/jobs/updates/?status=RUNNING'
        response = self.client.generic('GET', url)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['job_type']['id'], self.job1.job_type.id)

    def test_job_type_id(self):
        '''Tests successfully calling the jobs view filtered by job type identifier.'''

        url = '/jobs/updates/?job_type_id=%s' % self.job1.job_type.id
        response = self.client.generic('GET', url)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['job_type']['id'], self.job1.job_type.id)

    def test_job_type_name(self):
        '''Tests successfully calling the jobs view filtered by job type name.'''

        url = '/jobs/updates/?job_type_name=%s' % self.job1.job_type.name
        response = self.client.generic('GET', url)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['job_type']['name'], self.job1.job_type.name)

    def test_job_type_category(self):
        '''Tests successfully calling the jobs view filtered by job type category.'''

        url = '/jobs/updates/?job_type_category=%s' % self.job1.job_type.category
        response = self.client.generic('GET', url)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['job_type']['category'], self.job1.job_type.category)


class TestJobTypesView(TestCase):

    def setUp(self):
        django.setup()

        self.workspace = storage_test_utils.create_workspace()
        self.error = error_test_utils.create_error()
        self.job_type1 = job_test_utils.create_job_type(priority=2, mem=1.0)
        self.job_type2 = job_test_utils.create_job_type(priority=1, mem=2.0)

    def test_successful(self):
        '''Tests successfully calling the get all job types view.'''

        url = '/job-types/'
        response = self.client.get(url)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result['results']), 2)
        for entry in result['results']:
            expected = None
            if entry['id'] == self.job_type1.id:
                expected = self.job_type1
            elif entry['id'] == self.job_type2.id:
                expected = self.job_type2
            else:
                self.fail('Found unexpected result: %s' % entry['id'])
            self.assertEqual(entry['name'], expected.name)
            self.assertEqual(entry['version'], expected.version)

    def test_name(self):
        '''Tests successfully calling the jobs view filtered by job type name.'''

        url = '/job-types/?name=%s' % self.job_type1.name
        response = self.client.generic('GET', url)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['name'], self.job_type1.name)

    def test_category(self):
        '''Tests successfully calling the jobs view filtered by job type category.'''

        url = '/job-types/?category=%s' % self.job_type1.category
        response = self.client.generic('GET', url)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['category'], self.job_type1.category)

    def test_sorting(self):
        '''Tests custom sorting.'''

        url = '/job-types/?order=priority'
        response = self.client.get(url)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result['results']), 2)
        self.assertEqual(result['results'][0]['name'], self.job_type2.name)
        self.assertEqual(result['results'][0]['version'], self.job_type2.version)

    def test_reverse_sorting(self):
        '''Tests custom sorting in reverse.'''

        url = '/job-types/?order=-mem_required'
        response = self.client.get(url)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result['results']), 2)
        self.assertEqual(result['results'][0]['name'], self.job_type2.name)
        self.assertEqual(result['results'][0]['version'], self.job_type2.version)

    def test_create(self):
        '''Tests creating a new job type.'''
        url = '/job-types/'
        json_data = {
            'name': 'job-type-post-test',
            'version': '1.0.0',
            'title': 'Job Type Post Test',
            'description': 'This is a test.',
            'priority': '1',
            'interface': {
                'version': '1.0',
                'command': 'test_cmd',
                'command_arguments': 'test_arg',
                'input_data': [],
                'output_data': [],
                'shared_resources': [],
            },
            'error_mapping': {
                'version': '1.0',
                'exit_codes': {
                    '1': self.error.name,
                },
            },
        }

        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        results = json.loads(response.content)

        job_type = JobType.objects.filter(name='job-type-post-test').first()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(results['id'], job_type.id)
        self.assertEqual(results['priority'], 1)
        self.assertIsNotNone(results['error_mapping'])
        self.assertEqual(results['error_mapping']['exit_codes']['1'], self.error.name)
        self.assertIsNone(results['trigger_rule'])

    def test_create_trigger(self):
        '''Tests creating a new job type with a trigger rule.'''
        url = '/job-types/'
        json_data = {
            'name': 'job-type-post-test',
            'version': '1.0.0',
            'title': 'Job Type Post Test',
            'description': 'This is a test.',
            'interface': {
                'version': '1.0',
                'command': 'test_cmd',
                'command_arguments': 'test_arg',
                'input_data': [{
                    'media_types': ['image/png'],
                    'type': 'file',
                    'name': 'input_file',
                }],
                'output_data': [],
                'shared_resources': [],
            },
            'trigger_rule': {
                'type': 'PARSE',
                'is_active': True,
                'configuration': {
                    'version': '1.0',
                    'condition': {
                        'media_type': 'image/png',
                        'data_types': [],
                    },
                    'data': {
                        'input_data_name': 'input_file',
                        'workspace_name': self.workspace.name,
                    }
                }
            }
        }

        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        results = json.loads(response.content)

        job_type = JobType.objects.filter(name='job-type-post-test').first()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(results['id'], job_type.id)
        self.assertIsNotNone(results['interface'])
        self.assertDictEqual(results['error_mapping']['exit_codes'], {})
        self.assertEqual(results['trigger_rule']['type'], 'PARSE')

    def test_create_missing_param(self):
        '''Tests creating a job type with missing fields.'''
        url = '/job-types/'
        json_data = {
            'name': 'job-type-post-test',
        }

        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_bad_param(self):
        '''Tests creating a job type with invalid type fields.'''
        url = '/job-types/'
        json_data = {
            'name': 'job-type-post-test',
            'version': '1.0.0',
            'title': 'Job Type Post Test',
            'description': 'This is a test.',
            'priority': 'BAD',
            'interface': {
                'version': '1.0',
                'command': 'test_cmd',
                'command_arguments': 'test_arg',
                'input_data': [],
                'output_data': [],
                'shared_resources': [],
            },
        }

        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_bad_error(self):
        '''Tests creating a new job type with an invalid error relationship.'''
        url = '/job-types/'
        json_data = {
            'name': 'job-type-post-test',
            'version': '1.0.0',
            'description': 'This is a test.',
            'interface': {
                'version': '1.0',
                'command': 'test_cmd',
                'command_arguments': 'test_arg',
                'input_data': [],
                'output_data': [],
                'shared_resources': [],
            },
            'error_mapping': {
                'version': '1.0',
                'exit_codes': {
                    '1': 'BAD',
                },
            },
        }

        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_bad_trigger_type(self):
        '''Tests creating a new job type with an invalid trigger type.'''
        url = '/job-types/'
        json_data = {
            'name': 'job-type-post-test',
            'version': '1.0.0',
            'description': 'This is a test.',
            'interface': {
                'version': '1.0',
                'command': 'test_cmd',
                'command_arguments': 'test_arg',
                'input_data': [],
                'output_data': [],
                'shared_resources': [],
            },
            'trigger_rule': {
                'type': 'BAD',
            }
        }

        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_bad_trigger_config(self):
        '''Tests creating a new job type with an invalid trigger rule configuration.'''
        url = '/job-types/'
        json_data = {
            'name': 'job-type-post-test',
            'version': '1.0.0',
            'description': 'This is a test.',
            'interface': {
                'version': '1.0',
                'command': 'test_cmd',
                'command_arguments': 'test_arg',
                'input_data': [],
                'output_data': [],
                'shared_resources': [],
            },
            'trigger_rule': {
                'type': 'PARSE',
                'configuration': {
                    'BAD': '1.0',
                }
            }
        }

        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestJobTypeDetailsView(TestCase):

    def setUp(self):
        django.setup()

        self.interface = {
            'version': '1.0',
            'command': 'test_cmd',
            'command_arguments': 'test_arg',
            'input_data': [],
            'output_data': [],
            'shared_resources': [],
        }

        self.error = error_test_utils.create_error(category='ALGORITHM')
        self.error_mapping = {
            'version': '1.0',
            'exit_codes': {
                '1': self.error.name,
            }
        }

        self.workspace = storage_test_utils.create_workspace()
        self.trigger_config = {
            'version': '1.0',
            'condition': {
                'media_type': 'text/plain',
            },
            'data': {
                'input_data_name': 'input_file',
                'workspace_name': self.workspace.name,
            }
        }
        self.trigger_rule = trigger_test_utils.create_trigger_rule(trigger_type='PARSE', is_active=True,
                                                                   configuration=self.trigger_config)

        self.job_type = job_test_utils.create_job_type(interface=self.interface, error_mapping=self.error_mapping,
                                                       trigger_rule=self.trigger_rule)
        self.error1 = error_test_utils.create_error()
        self.error2 = error_test_utils.create_error()

    def test_not_found(self):
        '''Tests successfully calling the get job type details view with a job id that does not exist.'''

        url = '/job-types/100/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_successful(self):
        '''Tests successfully calling the get job type details view.'''

        url = '/job-types/%d/' % self.job_type.id
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = json.loads(response.content)
        self.assertTrue(isinstance(result, dict), 'result  must be a dictionary')
        self.assertEqual(result['id'], self.job_type.id)
        self.assertEqual(result['name'], self.job_type.name)
        self.assertEqual(result['version'], self.job_type.version)

        self.assertIsNotNone(result['interface'])
        self.assertIsNotNone(result['error_mapping'])
        self.assertIsNotNone(result['trigger_rule'])
        self.assertEqual(len(result['errors']), 1)

        self.assertEqual(len(result['job_counts_6h']), 0)
        self.assertEqual(len(result['job_counts_12h']), 0)
        self.assertEqual(len(result['job_counts_24h']), 0)

    def test_edit_simple(self):
        '''Tests editing only the basic attributes of a job type'''

        url = '/job-types/%d/' % self.job_type.id
        json_data = {
            'title': 'Title EDIT',
            'description': 'Description EDIT',
        }
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(isinstance(result, dict), 'result  must be a dictionary')
        self.assertEqual(result['id'], self.job_type.id)
        self.assertEqual(result['title'], 'Title EDIT')
        self.assertEqual(result['description'], 'Description EDIT')
        self.assertEqual(result['revision_num'], 1)
        self.assertDictEqual(result['interface'], self.interface)
        self.assertDictEqual(result['error_mapping'], self.error_mapping)
        self.assertEqual(result['trigger_rule']['id'], self.trigger_rule.id)

    def test_edit_interface(self):
        '''Tests editing the interface of a job type'''
        interface = self.interface.copy()
        interface['command'] = 'test_cmd_edit'

        url = '/job-types/%d/' % self.job_type.id
        json_data = {
            'interface': interface,
        }
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(result['id'], self.job_type.id)
        self.assertEqual(result['title'], self.job_type.title)
        self.assertEqual(result['revision_num'], 2)
        self.assertEqual(result['interface']['command'], 'test_cmd_edit')
        self.assertEqual(result['trigger_rule']['id'], self.trigger_rule.id)

    def test_edit_error_mapping(self):
        '''Tests editing the error mapping of a job type'''
        error = error_test_utils.create_error(category='DATA')
        error_mapping = self.error_mapping.copy()
        error_mapping['exit_codes']['10'] = error.name

        url = '/job-types/%d/' % self.job_type.id
        json_data = {
            'error_mapping': error_mapping,
        }
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(result['id'], self.job_type.id)
        self.assertEqual(result['title'], self.job_type.title)
        self.assertEqual(result['revision_num'], 1)
        self.assertEqual(result['error_mapping']['exit_codes']['10'], error.name)
        self.assertEqual(result['trigger_rule']['id'], self.trigger_rule.id)

    def test_edit_trigger_rule(self):
        '''Tests editing the trigger rule of a job type'''
        trigger_config = self.trigger_config.copy()
        trigger_config['condition']['media_type'] = 'application/json'

        url = '/job-types/%d/' % self.job_type.id
        json_data = {
            'trigger_rule': {
                'type': 'PARSE',
                'configuration': trigger_config,
            }
        }
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(result['id'], self.job_type.id)
        self.assertEqual(result['title'], self.job_type.title)
        self.assertEqual(result['revision_num'], 1)
        self.assertIsNotNone(result['interface'])
        self.assertEqual(result['trigger_rule']['configuration']['condition']['media_type'], 'application/json')
        self.assertNotEqual(result['trigger_rule']['id'], self.trigger_rule.id)

    def test_edit_trigger_rule_pause(self):
        '''Tests pausing the trigger rule of a job type'''
        trigger_config = self.trigger_config.copy()
        trigger_config['condition']['media_type'] = 'application/json'

        url = '/job-types/%d/' % self.job_type.id
        json_data = {
            'trigger_rule': {
                'is_active': False,
            }
        }
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(result['id'], self.job_type.id)
        self.assertEqual(result['title'], self.job_type.title)
        self.assertEqual(result['revision_num'], 1)
        self.assertIsNotNone(result['interface'])
        self.assertEqual(result['trigger_rule']['is_active'], False)

    def test_edit_trigger_rule_remove(self):
        '''Tests removing the trigger rule from a job type'''
        url = '/job-types/%d/' % self.job_type.id
        json_data = {
            'trigger_rule': None,
        }
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(result['id'], self.job_type.id)
        self.assertEqual(result['title'], self.job_type.title)
        self.assertEqual(result['revision_num'], 1)
        self.assertIsNotNone(result['interface'])
        self.assertIsNone(result['trigger_rule'])

    def test_edit_interface_and_trigger_rule(self):
        '''Tests editing the job type interface and trigger rule together'''
        interface = self.interface.copy()
        interface['command'] = 'test_cmd_edit'
        trigger_config = self.trigger_config.copy()
        trigger_config['condition']['media_type'] = 'application/json'

        url = '/job-types/%d/' % self.job_type.id
        json_data = {
            'interface': interface,
            'trigger_rule': {
                'type': 'PARSE',
                'configuration': trigger_config,
            }
        }
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(result['id'], self.job_type.id)
        self.assertEqual(result['title'], self.job_type.title)
        self.assertEqual(result['revision_num'], 2)
        self.assertEqual(result['interface']['command'], 'test_cmd_edit')
        self.assertEqual(result['trigger_rule']['configuration']['condition']['media_type'], 'application/json')
        self.assertNotEqual(result['trigger_rule']['id'], self.trigger_rule.id)

    def test_edit_bad_interface(self):
        '''Tests attempting to edit a job type using an invalid job interface'''
        interface = self.interface.copy()
        interface['version'] = 'BAD'

        url = '/job-types/%d/' % self.job_type.id
        json_data = {
            'interface': interface,
        }
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_edit_bad_error_mapping(self):
        '''Tests attempting to edit a job type using an invalid error mapping'''
        error_mapping = self.error_mapping.copy()
        error_mapping['version'] = 'BAD'

        url = '/job-types/%d/' % self.job_type.id
        json_data = {
            'error_mapping': error_mapping,
        }
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_edit_bad_trigger(self):
        '''Tests attempting to edit a job type using an invalid trigger rule'''
        trigger_config = self.trigger_config.copy()
        trigger_config['version'] = 'BAD'

        url = '/job-types/%d/' % self.job_type.id
        json_data = {
            'trigger_rule': {
                'type': 'PARSE',
                'configuration': trigger_config,
            }
        }
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestJobTypesValidationView(TransactionTestCase):
    '''Tests related to the job-types validation endpoint'''

    def setUp(self):
        django.setup()

        self.workspace = storage_test_utils.create_workspace()
        self.error = error_test_utils.create_error(category='ALGORITHM')

    def test_successful(self):
        '''Tests validating a new job type.'''
        url = '/job-types/validation/'
        json_data = {
            'name': 'job-type-test',
            'version': '1.0.0',
            'title': 'Job Type Test',
            'description': 'This is a test.',
            'interface': {
                'version': '1.0',
                'command': 'test_cmd',
                'command_arguments': 'test_arg',
                'input_data': [],
                'output_data': [],
                'shared_resources': [],
            },
            'error_mapping': {
                'version': '1.0',
                'exit_codes': {
                    '1': self.error.name,
                },
            },
        }

        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        results = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(results, {'warnings': []}, 'JSON result was incorrect')

    def test_successful_trigger(self):
        '''Tests validating a new job type with a trigger.'''
        url = '/job-types/validation/'
        json_data = {
            'name': 'job-type-test',
            'version': '1.0.0',
            'title': 'Job Type Test',
            'description': 'This is a test.',
            'interface': {
                'version': '1.0',
                'command': 'test_cmd',
                'command_arguments': 'test_arg',
                'input_data': [],
                'output_data': [],
                'shared_resources': [],
            },
            'trigger_rule': {
                'type': 'PARSE',
                'configuration': {
                    'version': '1.0',
                    'condition': {
                        'media_type': 'image/x-hdf5-image',
                        'data_types': [],
                    },
                    'data': {
                        'input_data_name': 'input_file',
                        'workspace_name': self.workspace.name,
                    }
                }
            }
        }

        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        results = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(results, {'warnings': []}, 'JSON result was incorrect')

    def test_bad_param(self):
        '''Tests validating a new job type with missing fields.'''
        url = '/job-types/validation/'
        json_data = {
            'name': 'job-type-post-test',
        }

        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bad_error(self):
        '''Tests validating a new job type with an invalid error relationship.'''
        url = '/job-types/validation/'
        json_data = {
            'name': 'job-type-post-test',
            'version': '1.0.0',
            'description': 'This is a test.',
            'error_mapping': {
                'version': '1.0',
                'exit_codes': {
                    '1': 'BAD',
                },
            },
        }

        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_warnings(self):
        '''Tests validating a new job type with mismatched media type warnings.'''
        url = '/job-types/validation/'
        json_data = {
            'name': 'job-type-post-test',
            'version': '1.0.0',
            'description': 'This is a test.',
            'interface': {
                'version': '1.0',
                'command': '/test.sh',
                'command_arguments': '${input_file}',
                'input_data': [{
                    'name': 'input_file',
                    'type': 'file',
                    'media_types': ['image/png'],
                }],
                'output_data': [],
            },
            'trigger_rule': {
                'type': 'PARSE',
                'configuration': {
                    'version': '1.0',
                    'condition': {
                        'media_type': 'text/plain',
                        'data_types': [],
                    },
                    'data': {
                        'input_data_name': 'input_file',
                        'workspace_name': self.workspace.name,
                    }
                }
            }
        }

        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        results = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(results['warnings']), 1)
        self.assertEqual(results['warnings'][0]['id'], 'media_type')

    def test_bad_trigger_type(self):
        '''Tests validating a new job type with an invalid trigger type.'''
        url = '/job-types/validation/'
        json_data = {
            'name': 'job-type-post-test',
            'version': '1.0.0',
            'description': 'This is a test.',
            'interface': {
                'version': '1.0',
                'command': 'test_cmd',
                'command_arguments': 'test_arg',
                'input_data': [],
                'output_data': [],
                'shared_resources': [],
            },
            'trigger_rule': {
                'type': 'BAD',
            }
        }

        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bad_trigger_config(self):
        '''Tests validating a new job type with an invalid trigger rule configuration.'''
        url = '/job-types/validation/'
        json_data = {
            'name': 'job-type-post-test',
            'version': '1.0.0',
            'description': 'This is a test.',
            'interface': {
                'version': '1.0',
                'command': 'test_cmd',
                'command_arguments': 'test_arg',
                'input_data': [],
                'output_data': [],
                'shared_resources': [],
            },
            'trigger_rule': {
                'type': 'PARSE',
                'configuration': {
                    'BAD': '1.0',
                }
            }
        }

        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestJobTypesStatusView(TestCase):

    def setUp(self):
        django.setup()

        self.job_type = job_test_utils.create_job_type()

    def test_successful(self):
        '''Tests successfully calling the status view.'''
        job = job_test_utils.create_job(job_type=self.job_type, status='COMPLETED')

        url = '/job-types/status/'
        response = self.client.generic('GET', url)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['job_type']['name'], job.job_type.name)
        self.assertEqual(len(result['results'][0]['job_counts']), 1)
        self.assertEqual(result['results'][0]['job_counts'][0]['status'], 'COMPLETED')
        self.assertEqual(result['results'][0]['job_counts'][0]['count'], 1)

    def test_running(self):
        '''Tests getting running jobs regardless of time filters.'''
        old_timestamp = datetime.datetime(2015, 1, 1, tzinfo=timezone.utc)
        job_test_utils.create_job(job_type=self.job_type, status='COMPLETED', last_status_change=old_timestamp)
        job_test_utils.create_job(job_type=self.job_type, status='RUNNING', last_status_change=old_timestamp)

        new_timestamp = datetime.datetime(2015, 1, 10, tzinfo=timezone.utc)
        job_test_utils.create_job(job_type=self.job_type, status='COMPLETED', last_status_change=new_timestamp)
        job_test_utils.create_job(job_type=self.job_type, status='RUNNING', last_status_change=new_timestamp)

        url = '/job-types/status/?started=2015-01-05T00:00:00Z'
        response = self.client.generic('GET', url)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(len(result['results'][0]['job_counts']), 2)

        for entry in result['results'][0]['job_counts']:
            if entry['status'] == 'COMPLETED':
                self.assertEqual(entry['count'], 1)
            elif entry['status'] == 'RUNNING':
                self.assertEqual(entry['count'], 2)
            else:
                self.fail('Found unexpected job type count status: %s' % entry['status'])


class TestJobTypesRunningView(TestCase):

    def setUp(self):
        django.setup()

        self.job = job_test_utils.create_job(status='RUNNING')

    def test_successful(self):
        '''Tests successfully calling the running status view.'''

        url = '/job-types/running/'
        response = self.client.generic('GET', url)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['job_type']['name'], self.job.job_type.name)
        self.assertEqual(result['results'][0]['count'], 1)


class TestJobTypesSystemFailuresView(TestCase):

    def setUp(self):
        django.setup()

        self.error = Error(name='Test Error', description='test')
        self.error.save()
        self.job = job_test_utils.create_job(status='FAILED', error=self.error)

    def test_successful(self):
        '''Tests successfully calling the system failures view.'''

        url = '/job-types/system-failures/'
        response = self.client.generic('GET', url)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['job_type']['name'], self.job.job_type.name)
        self.assertEqual(result['results'][0]['error']['name'], self.error.name)
        self.assertEqual(result['results'][0]['count'], 1)


class TestJobsWithExecutionView(TransactionTestCase):
    '''An integration test of the Jobs with latest execution view'''

    def setUp(self):
        django.setup()

        self.job_type_1 = job_test_utils.create_job_type()
        self.job_type_2 = job_test_utils.create_job_type()

        self.job_1a = job_test_utils.create_job(job_type=self.job_type_1, status='COMPLETED')
        job_test_utils.create_job_exe(job=self.job_1a, status='FAILED',
                                      created=timezone.now() - datetime.timedelta(hours=3))
        time.sleep(.01)
        job_test_utils.create_job_exe(job=self.job_1a, status='FAILED',
                                      created=timezone.now() - datetime.timedelta(hours=2))
        time.sleep(.01)
        job_test_utils.create_job_exe(job=self.job_1a, status='COMPLETED',
                                      created=timezone.now() - datetime.timedelta(hours=1),
                                      last_modified=timezone.now() - datetime.timedelta(hours=1))
        time.sleep(.01)
        self.last_run_1a = job_test_utils.create_job_exe(job=self.job_1a, status='RUNNING')

        self.job_1b = job_test_utils.create_job(job_type=self.job_type_1, status='FAILED')
        time.sleep(.01)
        self.last_run_1b = job_test_utils.create_job_exe(job=self.job_1b, status='FAILED')

        self.job_2a = job_test_utils.create_job(job_type=self.job_type_2, status='RUNNING')
        time.sleep(.01)
        job_test_utils.create_job_exe(job=self.job_2a, status='FAILED',
                                      created=timezone.now() - datetime.timedelta(hours=3),
                                      last_modified=timezone.now() - datetime.timedelta(hours=2))
        time.sleep(.01)
        job_test_utils.create_job_exe(job=self.job_2a, status='FAILED',
                                      created=timezone.now() - datetime.timedelta(hours=2),
                                      last_modified=timezone.now() - datetime.timedelta(hours=1))
        time.sleep(.01)
        job_test_utils.create_job_exe(job=self.job_2a, status='COMPLETED',
                                      created=timezone.now() - datetime.timedelta(hours=1))
        time.sleep(.01)
        self.last_run_2a = job_test_utils.create_job_exe(job=self.job_2a, status='RUNNING')

        self.job_2b = job_test_utils.create_job(job_type=self.job_type_2, status='COMPLETED')
        time.sleep(.01)
        self.last_run_2b = job_test_utils.create_job_exe(job=self.job_2b, status='COMPLETED')

    def test_get_latest_job_exes(self):
        '''Tests calling the jobs information service without a filter'''

        job_map = {
            self.job_1a.id: (self.job_1a, self.job_type_1, self.last_run_1a),
            self.job_1b.id: (self.job_1b, self.job_type_1, self.last_run_1b),
            self.job_2a.id: (self.job_2a, self.job_type_2, self.last_run_2a),
            self.job_2b.id: (self.job_2b, self.job_type_2, self.last_run_2b),
        }

        url = '/jobs/executions/'
        response = self.client.generic('GET', url)
        results = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(results['count'], 4)
        self.assertEqual(results['next'], None)
        self.assertEqual(results['previous'], None)

        job_ids = set()
        for job_entry in results['results']:
            self.assertFalse(job_entry['id'] in job_ids)
            job_ids.add(job_entry['id'])

            self.assertTrue(job_entry['id'] in job_map)
            expected_job, expected_type, expected_last_run = job_map[job_entry['id']]
            result_type_dict = job_entry['job_type']
            result_last_run_dict = job_entry['latest_job_exe']

            # Test a few values from the response
            self.assertEqual(expected_job.status, job_entry['status'])
            self.assertEqual(expected_job.priority, job_entry['priority'])
            self.assertEqual(expected_type.id, result_type_dict['id'])
            self.assertEqual(expected_type.name, result_type_dict['name'])
            self.assertEqual(expected_last_run.id, result_last_run_dict['id'])
            self.assertEqual(expected_last_run.job_exit_code, result_last_run_dict['job_exit_code'])

    def test_with_status_filter(self):
        url = '/jobs/executions/?status=COMPLETED'
        response = self.client.generic('GET', url)
        results = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(results['count'], 2)

        for job_entry in results['results']:
            self.assertTrue(job_entry['id'] in (self.job_1a.id, self.job_2b.id))

    def test_with_job_type_id_filter(self):
        url = '/jobs/executions/?job_type_id=%s' % self.job_type_1.id
        response = self.client.generic('GET', url)
        results = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(results['count'], 2)

        for job_entry in results['results']:
            self.assertTrue(job_entry['id'] in (self.job_1a.id, self.job_1b.id))

    def test_with_job_type_name_filter(self):
        url = '/jobs/executions/?job_type_name=%s' % self.job_type_2.name
        response = self.client.generic('GET', url)
        results = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(results['count'], 2)

        for job_entry in results['results']:
            self.assertTrue(job_entry['id'] in (self.job_2a.id, self.job_2b.id))

    def test_with_job_type_category_filter(self):
        url = '/jobs/executions/?job_type_category=%s' % self.job_type_2.category
        response = self.client.generic('GET', url)
        results = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(results['count'], 2)

        for job_entry in results['results']:
            self.assertTrue(job_entry['id'] in (self.job_2a.id, self.job_2b.id))


class TestJobExecutionsView(TransactionTestCase):

    def setUp(self):
        django.setup()

        self.job_type_1 = job_test_utils.create_job_type()
        self.job_type_2 = job_test_utils.create_job_type()

        self.job_1 = job_test_utils.create_job(job_type=self.job_type_1, status='COMPLETED')
        self.job_exe_1a = job_test_utils.create_job_exe(job=self.job_1, status='FAILED',
                                                            created=timezone.now() - datetime.timedelta(hours=3))
        self.job_exe_1b = job_test_utils.create_job_exe(job=self.job_1, status='FAILED',
                                                            created=timezone.now() - datetime.timedelta(hours=2))
        self.job_exe_1c = job_test_utils.create_job_exe(job=self.job_1, status='FAILED',
                                                            created=timezone.now() - datetime.timedelta(hours=1),
                                                            last_modified=timezone.now() - datetime.timedelta(hours=1))
        self.last_exe_1 = job_test_utils.create_job_exe(job=self.job_1, status='RUNNING')

        self.job_2 = job_test_utils.create_job(job_type=self.job_type_1, status='FAILED')
        self.last_exe_2 = job_test_utils.create_job_exe(job=self.job_2, status='FAILED')

        job_3 = job_test_utils.create_job(job_type=self.job_type_2, status='RUNNING')
        job_test_utils.create_job_exe(job=job_3, status='FAILED', created=timezone.now() - datetime.timedelta(hours=3),
                                          last_modified=timezone.now() - datetime.timedelta(hours=2))
        job_test_utils.create_job_exe(job=job_3, status='FAILED', created=timezone.now() - datetime.timedelta(hours=2),
                                          last_modified=timezone.now() - datetime.timedelta(hours=1))
        job_test_utils.create_job_exe(job=job_3, status='COMPLETED',
                                      created=timezone.now() - datetime.timedelta(hours=1))
        job_test_utils.create_job_exe(job=job_3, status='RUNNING')

        job_4 = job_test_utils.create_job(job_type=self.job_type_2, status='COMPLETED')
        job_test_utils.create_job_exe(job=job_4, status='COMPLETED')

    def test_get_job_executions(self):
        '''This test checks to make sure there are 10 job executions.'''
        url = '/job-executions/'
        response = self.client.generic('GET', url)
        results = json.loads(response.content)

        job_exe_count = results['count']

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(job_exe_count, 10)

    def test_get_job_executions_running_status(self):
        '''This test checks to make sure there are 2 job executions running.'''
        url = '/job-executions/?status=RUNNING'
        response = self.client.generic('GET', url)
        results = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(results['count'], 2)

    def test_get_job_executions_for_job_id(self):
        url = '/job-executions/?job_type_id=%s' % self.job_type_1.id
        response = self.client.generic('GET', url)
        results = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(results['count'], 5)

        job_1_exe_list = (self.job_exe_1a.id, self.job_exe_1b.id, self.job_exe_1c.id, self.last_exe_1.id,
                          self.last_exe_2.id)
        for job_execution_entry in results['results']:
            job_exe_id = job_execution_entry['id']
            self.assertTrue(job_exe_id in job_1_exe_list)

    def test_get_job_executions_for_job_name(self):
        url = '/job-executions/?job_type_name=%s' % self.job_type_1.name
        response = self.client.generic('GET', url)
        results = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(results['count'], 5)

        job_1_exe_list = (self.job_exe_1a.id, self.job_exe_1b.id, self.job_exe_1c.id, self.last_exe_1.id,
                          self.last_exe_2.id)
        for job_execution_entry in results['results']:
            job_exe_id = job_execution_entry['id']
            self.assertTrue(job_exe_id in job_1_exe_list)

    def test_get_job_executions_for_job_category(self):
        url = '/job-executions/?job_type_category=%s' % self.job_type_1.category
        response = self.client.generic('GET', url)
        results = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(results['count'], 5)

        job_1_exe_list = (self.job_exe_1a.id, self.job_exe_1b.id, self.job_exe_1c.id, self.last_exe_1.id,
                          self.last_exe_2.id)
        for job_execution_entry in results['results']:
            job_exe_id = job_execution_entry['id']
            self.assertTrue(job_exe_id in job_1_exe_list)

    def test_no_tz(self):
        start_date_time = timezone.now() - datetime.timedelta(hours=1)
        end_date_time = timezone.now()
        url = '/job-executions/?started={0}&ended={1}'.format(start_date_time.isoformat(), end_date_time.isoformat())
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_job_execution_for_job_exe_id(self):
        url = '/job-executions/%d/' % self.job_exe_1a.id
        response = self.client.generic('GET', url)
        results = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(results['id'], self.job_exe_1a.id)

    def test_get_job_execution_bad_id(self):
        url = '/job-executions/9999999/'
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_job_execution_logs_success(self):
        url = '/job-executions/%d/logs/' % self.job_exe_1b.id
        response = self.client.generic('GET', url)
        results = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(results['id'], self.job_exe_1b.id)
        self.assertEqual(results['status'], self.job_exe_1b.status)
        self.assertEqual(results['stdout'], self.job_exe_1b.stdout)
        self.assertEqual(results['stderr'], self.job_exe_1b.stderr)

    def test_get_job_execution_logs_bad_id(self):
        url = '/job-executions/999999/logs/'
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
