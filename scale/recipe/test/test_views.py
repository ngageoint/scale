#@PydevCodeAnalysisIgnore
import django
import json

from django.test.testcases import TransactionTestCase

import job.test.utils as job_test_utils
import recipe.test.utils as recipe_test_utils
from recipe.models import RecipeType
from rest_framework import status


class TestRecipeTypesView(TransactionTestCase):
    '''Tests related to the recipe-types base endpoint'''

    def setUp(self):
        django.setup()

        self.recipe_type_1 = RecipeType.objects.create(name=u'Recipe 1', version=u'1.0',
                                                       description=u'Description of Recipe 1', definition=u'')
        self.recipe_type_2 = RecipeType.objects.create(name=u'Recipe 2', version=u'1.0',
                                                       description=u'Description of Recipe 2', definition=u'')

    def test_list_all(self):
        '''Tests getting a list of recipe types.'''
        url = '/recipe-types/'
        response = self.client.generic('GET', url)
        results = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(results, 'get_recipe_types value is none')

    def test_create(self):
        '''Tests creating a new recipe type.'''
        url = '/recipe-types/'
        json_data = {
            'name': 'recipe-type-post-test',
            'version': '1.0.0',
            'title': 'Recipe Type Post Test',
            'description': 'This is a test.',
            'definition': {
                'version': '1.0',
                'input_data': [{
                    'name': 'input_file',
                    'type': 'file',
                    'media_types': ['image/x-hdf5-image'],
                }],
                'jobs': [],
            }
        }

        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        results = json.loads(response.content)

        recipe_type = RecipeType.objects.filter(name='recipe-type-post-test').first()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertDictEqual(results, {'id': recipe_type.id}, u'JSON result was incorrect')

    def test_create_bad_param(self):
        '''Tests creating a new recipe type with missing fields.'''
        url = '/recipe-types/'
        json_data = {
            'name': 'recipe-type-post-test',
        }

        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_bad_job(self):
        '''Tests creating a new recipe type with an invalid job relationship.'''
        url = '/recipe-types/'
        json_data = {
            'name': 'recipe-type-post-test',
            'version': '1.0.0',
            'description': 'This is a test.',
            'definition': {
                'version': '1.0',
                'input_data': [{
                    'name': 'input_file',
                    'type': 'file',
                    'media_types': ['image/x-hdf5-image'],
                }],
                'jobs': [{
                    'name': 'test',
                }],
            }
        }

        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestRecipeTypeDetailsView(TransactionTestCase):
    '''Tests related to the recipe-types details endpoint'''

    def setUp(self):
        django.setup()

        self.job_type1 = job_test_utils.create_job_type()
        self.job_type2 = job_test_utils.create_job_type()
        self.recipe_type = recipe_test_utils.create_recipe_type(name='my-type', definition={
            'version': '1.0',
            'input_data': [],
            'jobs': [{
                'name': 'Job 1',
                'job_type': {
                    'name': self.job_type1.name,
                    'version': self.job_type1.version,
                },
            }, {
                'name': 'Job 2',
                'job_type': {
                    'name': self.job_type2.name,
                    'version': self.job_type2.version,
                },
            }],
        })

    def test_not_found(self):
        '''Tests calling the recipe type details view with an id that does not exist.'''

        url = '/recipe-types/100/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_successful(self):
        '''Tests successfully calling the recipe type details view.'''

        url = '/recipe-types/%d/' % self.recipe_type.id
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = json.loads(response.content)
        self.assertTrue(isinstance(result, dict), 'result  must be a dictionary')
        self.assertEqual(result[u'id'], self.recipe_type.id)
        self.assertEqual(result[u'name'], u'my-type')
        self.assertIsNotNone(result[u'definition'])
        self.assertEqual(len(result[u'job_types']), 2)
        for entry in result[u'job_types']:
            self.assertTrue(entry[u'id'], [self.job_type1.id, self.job_type2.id])


class TestRecipeTypesValidationView(TransactionTestCase):
    '''Tests related to the recipe-types validation endpoint'''

    def setUp(self):
        django.setup()

    def test_successful(self):
        '''Tests validating a new recipe type.'''
        url = '/recipe-types/validation/'
        json_data = {
            'name': 'recipe-type-post-test',
            'version': '1.0.0',
            'description': 'This is a test.',
            'definition': {
                'version': '1.0',
                'input_data': [{
                    'name': 'input_file',
                    'type': 'file',
                    'media_types': ['image/x-hdf5-image'],
                }],
                'jobs': [],
            }
        }

        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        results = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(results, {'warnings': []}, u'JSON result was incorrect')

    def test_bad_param(self):
        '''Tests validating a new recipe type with missing fields.'''
        url = '/recipe-types/validation/'
        json_data = {
            'name': 'recipe-type-post-test',
        }

        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bad_job(self):
        '''Tests creating a new recipe type with an invalid job relationship.'''
        url = '/recipe-types/validation/'
        json_data = {
            'name': 'recipe-type-post-test',
            'version': '1.0.0',
            'description': 'This is a test.',
            'definition': {
                'version': '1.0',
                'input_data': [{
                    'name': 'input_file',
                    'type': 'file',
                    'media_types': ['image/x-hdf5-image'],
                }],
                'jobs': [{
                    'name': 'test',
                }],
            }
        }

        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_warnings(self):
        '''Tests creating a new recipe type with mismatched media type warnings.'''
        interface = {
            'version': '1.0',
            'command': '/test.sh',
            'command_arguments': '${input_file1} ${input_file2}',
            'input_data': [{
                'name': 'input_file1',
                'type': 'file',
                'media_types': ['image/png'],
            }, {
                'name': 'input_file2',
                'type': 'file',
                'media_types': ['image/png'],
            }],
            'output_data': []
        }
        job_type1 = job_test_utils.create_job_type(interface=interface)
        job_type2 = job_test_utils.create_job_type()

        url = '/recipe-types/validation/'
        json_data = {
            'name': 'recipe-type-post-test',
            'version': '1.0.0',
            'description': 'This is a test.',
            'definition': {
                'version': '1.0',
                'input_data': [{
                    'name': 'input_file1',
                    'type': 'file',
                    'media_types': ['image/jpg'],
                }, {
                    'name': 'input_file2',
                    'type': 'file',
                    'media_types': ['image/jpg'],
                }],
                'jobs': [{
                    'name': job_type1.name,
                    'job_type': {
                        'name': job_type1.name,
                        'version': job_type1.version,
                    },
                    'recipe_inputs': [{
                        'job_input': 'input_file1',
                        'recipe_input': 'input_file1',
                    }, {
                        'job_input': 'input_file2',
                        'recipe_input': 'input_file2',
                    }]
                }, {
                    'name': job_type2.name,
                    'job_type': {
                        'name': job_type2.name,
                        'version': job_type2.version,
                    },
                }],
            }
        }

        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        results = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(results['warnings']), 2)
        self.assertEqual(results['warnings'][0]['id'], 'media_type')
        self.assertEqual(results['warnings'][1]['id'], 'media_type')


class TestRecipesView(TransactionTestCase):

    def setUp(self):
        django.setup()

        self.recipe_type = recipe_test_utils.create_recipe_type(name='my-type')
        self.recipe1 = recipe_test_utils.create_recipe(self.recipe_type)
        self.recipe2 = recipe_test_utils.create_recipe()

    def test_successful_all(self):
        '''Tests getting recipes'''

        url = '/recipes/'
        response = self.client.generic('GET', url)
        results = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(results['count'], 2)

    def test_successful_type_name(self):
        '''Tests getting recipes by type name'''

        url = '/recipes/?type_name=my-type'
        response = self.client.generic('GET', url)
        results = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(results['count'], 1)
        self.assertEqual(results['results'][0]['recipe_type']['name'], 'my-type')

    def test_successful_type_id(self):
        '''Tests getting recipes by type id'''

        url = '/recipes/?type_id=%s' % self.recipe_type.id
        response = self.client.generic('GET', url)
        results = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(results['count'], 1)
        self.assertEqual(results['results'][0]['recipe_type']['id'], self.recipe_type.id)

    def test_successful_details(self):
        '''Tests getting recipe details'''

        url = '/recipes/%s/' % self.recipe1.id
        response = self.client.generic('GET', url)
        results = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(results['id'], self.recipe1.id)
        self.assertEqual(results['recipe_type']['id'], self.recipe1.recipe_type.id)
        self.assertEqual(results['recipe_type_rev']['recipe_type']['id'], self.recipe1.recipe_type.id)
