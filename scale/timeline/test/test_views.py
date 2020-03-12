from __future__ import unicode_literals

import copy
import datetime
import django
import json

from django.utils.timezone import utc

import job.test.utils as job_test_utils
import recipe.test.utils as recipe_test_utils
import storage.test.utils as storage_test_utils

from recipe.models import RecipeType

from rest_framework import status
from rest_framework.test import APITestCase
from util import rest

class TestRecipeTypeTimelineView(APITestCase):
    api = 'v6'

    def setUp(self):
        django.setup()

        rest.login_client(self.client, is_staff=True)

        # create a couple job types
        manifest = copy.deepcopy(job_test_utils.COMPLETE_MANIFEST)
        manifest['job']['name'] = 'test-job-1'
        manifest['job']['interface']['inputs'] = {'files': [{'name': 'INPUT_FILE', 'required': True,
                                                             'mediaTypes': ['image/png'], 'partial': False}]}
        self.job_type_1 = job_test_utils.create_seed_job_type(manifest=manifest)

        manifest = copy.deepcopy(job_test_utils.COMPLETE_MANIFEST)
        manifest['job']['name'] = 'test-job-2'
        manifest['job']['interface']['inputs'] = {'files': [{'name': 'INPUT_FILE', 'required': True,
                                                             'mediaTypes': ['image/png'], 'partial': False}]}
        self.job_type_2 = job_test_utils.create_seed_job_type(manifest=manifest)

        # create recipe types
        recipe_def = {
            'version': '7',
            'input': {'files': [{'name': 'INPUT_FILE', 'media_types': ['image/png'], 'required': True,
                                 'multiple': False}],
                      'json': []},
            'nodes': {
                'node_a': {
                    'dependencies': [],
                    'input': {'INPUT_FILE': {'type': 'recipe', 'input': 'INPUT_FILE'}},
                    'node_type': {'node_type': 'job', 'job_type_name': self.job_type_1.name,
                                  'job_type_version': self.job_type_1.version,
                                  'job_type_revision': self.job_type_1.revision_num}
                }
            }
        }
        self.recipe_type_1 = recipe_test_utils.create_recipe_type_v6(definition=recipe_def)

        recipe_def = {
            'version': '7',
            'input': {'files': [{'name': 'INPUT_FILE', 'media_types': ['image/png'], 'required': True,
                                 'multiple': False}],
                      'json': []},
            'nodes': {
                'node_a': {
                    'dependencies': [],
                    'input': {'INPUT_FILE': {'type': 'recipe', 'input': 'INPUT_FILE'}},
                    'node_type': {'node_type': 'job', 'job_type_name': self.job_type_2.name,
                                  'job_type_version': self.job_type_2.version,
                                  'job_type_revision': self.job_type_2.revision_num}
                },
                'node_b': {
                    'dependencies': [],
                    'input': {'INPUT_FILE': {'type': 'recipe', 'input': 'INPUT_FILE'}},
                    'node_type': {'node_type': 'job', 'job_type_name': self.job_type_1.name,
                                  'job_type_version': self.job_type_1.version,
                                  'job_type_revision': self.job_type_1.revision_num}
                }
            }
        }
        self.recipe_type_2 = recipe_test_utils.create_recipe_type_v6(definition=recipe_def)

        # create recipes & jobs
        self.workspace = storage_test_utils.create_workspace()
        for i in range(1, 7):
            date_1 = datetime.datetime(2020, 1, i, tzinfo=utc)
            date_2 = datetime.datetime(2020, 1, i+1, tzinfo=utc)
            date_3 = datetime.datetime(2020, i, i+1, tzinfo=utc)
            file_1 = storage_test_utils.create_file(workspace=self.workspace, file_size=104857600.0,
                                                    source_started=date_1, source_ended=date_2)

            input_data = {
                'version': '1.0',
                'input_data': [{
                    'name': 'INPUT_FILE',
                    'file_id': file_1.id
                }]
            }
            # Recipe 1's jobs
            recipe_1 = recipe_test_utils.create_recipe(recipe_type=self.recipe_type_1, input=input_data)
            job_1 = job_test_utils.create_job(job_type=self.job_type_1, status='COMPLETED', started=date_1, ended=date_1)
            job_1.recipe_id = recipe_1.id
            job_1.save()
            # Recipe 2s jobs
            recipe_2 = recipe_test_utils.create_recipe(recipe_type=self.recipe_type_2, input=input_data)
            job_2 = job_test_utils.create_job(job_type=self.job_type_2, status='COMPLETED', started=date_2, ended=date_2)
            job_2.recipe_id = recipe_2.id
            job_2.save()
            job_3 = job_test_utils.create_job(job_type=self.job_type_1, status='COMPLETED', started=date_3,
                                              ended=date_3)
            job_3.recipe_id = recipe_2.id
            job_3.save()

    def test_successful(self):

        started = '2020-01-01T00:00:00Z'
        ended = '2020-02-01T00:00:00Z'

        url = '/%s/timeline/recipe-types/?started=%s&ended=%s' % (self.api, started, ended)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        results = result['results']
        self.assertEqual(len(results), 2)

        for result in results:
            the_type = None
            if result['recipe_type_id'] == self.recipe_type_1.id:
                the_type = self.recipe_type_1
            elif result['recipe_type_id'] == self.recipe_type_2.id:
                the_type = self.recipe_type_2
            self.assertEqual(result['name'], the_type.name)
            self.assertEqual(result['title'], the_type.title)
            self.assertEqual(result['revision_num'], the_type.revision_num)

    def test_range(self):

        started = '2020-01-01T00:00:00Z'
        url = '/%s/timeline/recipe-types/?started=%s' % (self.api, started)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

    def test_type_name(self):
        """Tests calling /timeline/recipe-types/ filtered by recipe type ids"""

        started = '2020-01-01T00:00:00Z'
        ended = '2020-02-01T00:00:00Z'

        url = '/%s/timeline/recipe-types/?started=%s&ended=%s&name=%s' % (self.api, started, ended,
                                                                          self.recipe_type_1.name)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        results = result['results']

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], self.recipe_type_1.name)
        self.assertEqual(results[0]['revision_num'], self.recipe_type_1.revision_num)

    def test_type_ids(self):
        """Tests calling /timeline/recipe-types/ filtered by recipe type names"""

        started = '2020-01-01T00:00:00Z'
        ended = '2020-02-01T00:00:00Z'

        url = '/%s/timeline/recipe-types/?started=%s&ended=%s&id=%s' % (self.api, started, ended,
                                                                        self.recipe_type_2.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        results = result['results']

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], self.recipe_type_2.name)
        self.assertEqual(results[0]['revision_num'], self.recipe_type_2.revision_num)

    def test_type_revisions(self):
        """Tests calling /timeline/recipe-types/ filtered by recipe type names"""

        # create recipe type
        recipe_def = {
            'version': '7',
            'input': {'files': [{'name': 'INPUT_FILE', 'media_types': ['image/png'], 'required': True,
                                 'multiple': False}],
                      'json': []},
            'nodes': {
                'node_a': {
                    'dependencies': [],
                    'input': {'INPUT_FILE': {'type': 'recipe', 'input': 'INPUT_FILE'}},
                    'node_type': {'node_type': 'job', 'job_type_name': self.job_type_1.name,
                                  'job_type_version': self.job_type_1.version,
                                  'job_type_revision': self.job_type_1.revision_num}
                }
            }
        }
        rtype = recipe_test_utils.create_recipe_type_v6(name='revision-recipe', definition=recipe_def)

        recipe_def_v2 = {
            'version': '7',
            'input': {'files': [{'name': 'INPUT_FILE', 'media_types': ['image/png'], 'required': True,
                                 'multiple': False}],
                      'json': []},
            'nodes': {
                'node_a': {
                    'dependencies': [],
                    'input': {'INPUT_FILE': {'type': 'recipe', 'input': 'INPUT_FILE'}},
                    'node_type': {'node_type': 'job', 'job_type_name': self.job_type_1.name,
                                  'job_type_version': self.job_type_1.version,
                                  'job_type_revision': self.job_type_1.revision_num}
                },
                'node_b': {
                    'dependencies': [],
                    'input': {'INPUT_FILE': {'type': 'recipe', 'input': 'INPUT_FILE'}},
                    'node_type': {'node_type': 'job', 'job_type_name': self.job_type_2.name,
                                  'job_type_version': self.job_type_2.version,
                                  'job_type_revision': self.job_type_2.revision_num}
                }

            }
        }
        recipe_test_utils.edit_recipe_type_v6(rtype, title='edited recipe', definition=recipe_def_v2)
        rtype_edit = RecipeType.objects.get(id=rtype.id)

        for i in range(1, 7):
            date_1 = datetime.datetime(2020, 1, i, tzinfo=utc)
            date_2 = datetime.datetime(2020, 1, i+1, tzinfo=utc)
            file_1 = storage_test_utils.create_file(workspace=self.workspace, file_size=104857600.0,
                                                    source_started=date_1, source_ended=date_2)
            input_data = {
                'version': '1.0',
                'input_data': [{
                    'name': 'INPUT_FILE',
                    'file_id': file_1.id
                }]
            }
            # Recipe 1's jobs
            recipe_1 = recipe_test_utils.create_recipe(recipe_type=rtype_edit, input=input_data)
            job_1 = job_test_utils.create_job(job_type=self.job_type_1, status='COMPLETED', started=date_1, ended=date_1)
            job_1.recipe_id = recipe_1.id
            job_1.save()
            job_2 = job_test_utils.create_job(job_type=self.job_type_2, status='COMPLETED', started=date_2, ended=date_2)
            job_2.recipe_id = recipe_1.id
            job_2.save()

        started = '2020-01-01T00:00:00Z'
        ended = '2020-02-01T00:00:00Z'

        url = '/%s/timeline/recipe-types/?started=%s&ended=%s&id=%s&rev=%s' % (self.api, started, ended,
                                                                               rtype_edit.id, rtype_edit.revision_num)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        results = result['results']

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], rtype_edit.name)
        self.assertEqual(results[0]['revision_num'], rtype_edit.revision_num)
        self.assertEqual(results[0]['title'], rtype_edit.title)

    def test_no_range(self):
        """Tests calling /timeline/recipe-types with no date range"""

        url = '/%s/timeline/recipe-types/' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)


class TestJobTypeTimelineView(APITestCase):
    api = 'v6'

    def setUp(self):
        django.setup()

        rest.login_client(self.client, is_staff=True)

        # create a couple job types
        manifest = copy.deepcopy(job_test_utils.COMPLETE_MANIFEST)
        manifest['job']['name'] = 'test-job-1'
        manifest['job']['interface']['inputs'] = {'files': [{'name': 'INPUT_FILE', 'required': True,
                                                             'mediaTypes': ['image/png'], 'partial': False}]}
        self.job_type_1 = job_test_utils.create_seed_job_type(manifest=manifest)

        manifest = copy.deepcopy(job_test_utils.COMPLETE_MANIFEST)
        manifest['job']['name'] = 'test-job-2'
        manifest['job']['interface']['inputs'] = {'files': [{'name': 'INPUT_FILE', 'required': True,
                                                             'mediaTypes': ['image/png'], 'partial': False}]}
        self.job_type_2 = job_test_utils.create_seed_job_type(manifest=manifest)

        # create recipe types
        recipe_def = {
            'version': '7',
            'input': {'files': [{'name': 'INPUT_FILE', 'media_types': ['image/png'], 'required': True,
                                 'multiple': False}],
                      'json': []},
            'nodes': {
                'node_a': {
                    'dependencies': [],
                    'input': {'INPUT_FILE': {'type': 'recipe', 'input': 'INPUT_FILE'}},
                    'node_type': {'node_type': 'job', 'job_type_name': self.job_type_1.name,
                                  'job_type_version': self.job_type_1.version,
                                  'job_type_revision': self.job_type_1.revision_num}
                }
            }
        }
        self.recipe_type_1 = recipe_test_utils.create_recipe_type_v6(definition=recipe_def)

        recipe_def = {
            'version': '7',
            'input': {'files': [{'name': 'INPUT_FILE', 'media_types': ['image/png'], 'required': True,
                                 'multiple': False}],
                      'json': []},
            'nodes': {
                'node_a': {
                    'dependencies': [],
                    'input': {'INPUT_FILE': {'type': 'recipe', 'input': 'INPUT_FILE'}},
                    'node_type': {'node_type': 'job', 'job_type_name': self.job_type_2.name,
                                  'job_type_version': self.job_type_2.version,
                                  'job_type_revision': self.job_type_2.revision_num}
                },
                'node_b': {
                    'dependencies': [],
                    'input': {'INPUT_FILE': {'type': 'recipe', 'input': 'INPUT_FILE'}},
                    'node_type': {'node_type': 'job', 'job_type_name': self.job_type_1.name,
                                  'job_type_version': self.job_type_1.version,
                                  'job_type_revision': self.job_type_1.revision_num}
                }
            }
        }
        self.recipe_type_2 = recipe_test_utils.create_recipe_type_v6(definition=recipe_def)

        # create recipes & jobs
        self.workspace = storage_test_utils.create_workspace()
        for i in range(1, 7):
            date_1 = datetime.datetime(2020, 1, i, tzinfo=utc)
            date_2 = datetime.datetime(2020, 1, i + 1, tzinfo=utc)
            date_3 = datetime.datetime(2020, i, i + 1, tzinfo=utc)
            file_1 = storage_test_utils.create_file(workspace=self.workspace, file_size=104857600.0,
                                                    source_started=date_1, source_ended=date_2)

            input_data = {
                'version': '1.0',
                'input_data': [{
                    'name': 'INPUT_FILE',
                    'file_id': file_1.id
                }]
            }
            # Recipe 1's jobs
            recipe_1 = recipe_test_utils.create_recipe(recipe_type=self.recipe_type_1, input=input_data)
            job_1 = job_test_utils.create_job(job_type=self.job_type_1, status='COMPLETED', started=date_1,
                                              ended=date_1)
            job_1.recipe_id = recipe_1.id
            job_1.save()
            # Recipe 2s jobs
            recipe_2 = recipe_test_utils.create_recipe(recipe_type=self.recipe_type_2, input=input_data)
            job_2 = job_test_utils.create_job(job_type=self.job_type_2, status='COMPLETED', started=date_2,
                                              ended=date_2)
            job_2.recipe_id = recipe_2.id
            job_2.save()
            job_3 = job_test_utils.create_job(job_type=self.job_type_1, status='COMPLETED', started=date_3,
                                              ended=date_3)
            job_3.recipe_id = recipe_2.id
            job_3.save()

    def test_successful(self):
        started = '2020-01-01T00:00:00Z'
        ended = '2020-02-01T00:00:00Z'

        url = '/%s/timeline/job-types/?started=%s&ended=%s' % (self.api, started, ended)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        results = result['results']

        self.assertEqual(len(results), 2)
        for result in results:
            the_type = None
            if result['name'] == self.job_type_1.name:
                the_type = self.job_type_1
            elif result['name'] == self.job_type_2.name:
                the_type = self.job_type_2
            self.assertEqual(result['name'], the_type.name)
            self.assertEqual(result['title'], the_type.get_title())
            self.assertEqual(result['revision_num'], the_type.revision_num)

    def test_type_ids(self):
        """Tests calling /timeline/recipe-types/ filtered by recipe type ids"""

        started = '2020-01-01T00:00:00Z'
        ended = '2020-02-01T00:00:00Z'

        url = '/%s/timeline/job-types/?started=%s&ended=%s&job_type_name=%s' % (self.api, started, ended,
                                                                                      self.job_type_1.name)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        results = result['results']

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], self.job_type_1.name)
        self.assertEqual(results[0]['title'], self.job_type_1.get_title())
        self.assertEqual(results[0]['revision_num'], self.job_type_1.revision_num)

    def test_type_names(self):
        """Tests calling /timeline/job-types/ filtered by job type names"""

        started = '2020-01-01T00:00:00Z'
        ended = '2020-02-01T00:00:00Z'

        url = '/%s/timeline/job-types/?started=%s&ended=%s&job_type_id=%s' % (self.api, started, ended,
                                                                              self.job_type_2.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        results = result['results']

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], self.job_type_2.name)
        self.assertEqual(results[0]['title'], self.job_type_2.get_title())
        self.assertEqual(results[0]['revision_num'], self.job_type_2.revision_num)

