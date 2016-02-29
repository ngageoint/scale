#@PydevCodeAnalysisIgnore
from __future__ import unicode_literals

import django
import json

from django.test.testcases import TransactionTestCase

import job.test.utils as job_test_utils
import recipe.test.utils as recipe_test_utils
import storage.test.utils as storage_test_utils
import trigger.test.utils as trigger_test_utils
from recipe.models import RecipeType
from rest_framework import status


class TestRecipeTypesView(TransactionTestCase):
    '''Tests related to the recipe-types base endpoint'''

    def setUp(self):
        django.setup()

        self.workspace = storage_test_utils.create_workspace()
        self.recipe_type_1 = RecipeType.objects.create(name='Recipe 1', version='1.0',
                                                       description='Description of Recipe 1', definition='')
        self.recipe_type_2 = RecipeType.objects.create(name='Recipe 2', version='1.0',
                                                       description='Description of Recipe 2', definition='')

    def test_list_all(self):
        '''Tests getting a list of recipe types.'''
        url = '/recipe-types/'
        response = self.client.generic('GET', url)
        results = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(results['results']), 2)

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
        self.assertEqual(results['id'], recipe_type.id)
        self.assertIsNone(results['trigger_rule'])

    def test_create_trigger(self):
        '''Tests creating a new recipe type with a trigger rule.'''
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
            },
            'trigger_rule': {
                'type': 'PARSE',
                'is_active': True,
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

        recipe_type = RecipeType.objects.filter(name='recipe-type-post-test').first()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(results['id'], recipe_type.id)
        self.assertEqual(results['trigger_rule']['type'], 'PARSE')

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

    def test_create_bad_trigger_type(self):
        '''Tests creating a new recipe type with an invalid trigger type.'''
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
                'jobs': [],
            },
            'trigger_rule': {
                'type': 'BAD',
            }
        }

        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_bad_trigger_config(self):
        '''Tests creating a new recipe type with an invalid trigger rule configuration.'''
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
                'jobs': [],
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


class TestRecipeTypeDetailsView(TransactionTestCase):
    '''Tests related to the recipe-types details endpoint'''

    def setUp(self):
        django.setup()

        self.job_type1 = job_test_utils.create_job_type()
        self.job_type2 = job_test_utils.create_job_type()

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

        self.definition = {
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
        }
        self.recipe_type = recipe_test_utils.create_recipe_type(name='my-type', definition=self.definition,
                                                                trigger_rule=self.trigger_rule)

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
        self.assertEqual(result['id'], self.recipe_type.id)
        self.assertEqual(result['name'], 'my-type')
        self.assertIsNotNone(result['definition'])
        self.assertEqual(len(result['job_types']), 2)
        for entry in result['job_types']:
            self.assertTrue(entry['id'], [self.job_type1.id, self.job_type2.id])
        self.assertEqual(result['trigger_rule']['id'], self.trigger_rule.id)

    def test_edit_simple(self):
        '''Tests editing only the basic attributes of a recipe type'''

        url = '/recipe-types/%d/' % self.recipe_type.id
        json_data = {
            'title': 'Title EDIT',
            'description': 'Description EDIT',
        }
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(isinstance(result, dict), 'result  must be a dictionary')
        self.assertEqual(result['id'], self.recipe_type.id)
        self.assertEqual(result['title'], 'Title EDIT')
        self.assertEqual(result['description'], 'Description EDIT')
        self.assertEqual(result['revision_num'], 1)
        self.assertIsNotNone(result['definition'])
        self.assertEqual(len(result['job_types']), 2)
        for entry in result['job_types']:
            self.assertTrue(entry['id'], [self.job_type1.id, self.job_type2.id])
        self.assertEqual(result['trigger_rule']['id'], self.trigger_rule.id)

    def test_edit_definition(self):
        '''Tests editing the definition of a recipe type'''
        definition = self.definition.copy()
        definition['input_data'] = [{
            'name': 'input_file',
            'type': 'file',
            'media_types': ['text/plain'],
        }]

        url = '/recipe-types/%d/' % self.recipe_type.id
        json_data = {
            'definition': definition,
        }
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(result['id'], self.recipe_type.id)
        self.assertEqual(result['title'], self.recipe_type.title)
        self.assertEqual(result['revision_num'], 2)
        self.assertEqual(len(result['definition']['input_data']), 1)
        self.assertEqual(result['definition']['input_data'][0]['name'], 'input_file')
        self.assertEqual(result['trigger_rule']['id'], self.trigger_rule.id)

    def test_edit_trigger_rule(self):
        '''Tests editing the trigger rule of a recipe type'''
        trigger_config = self.trigger_config.copy()
        trigger_config['condition']['media_type'] = 'application/json'

        url = '/recipe-types/%d/' % self.recipe_type.id
        json_data = {
            'trigger_rule': {
                'type': 'PARSE',
                'configuration': trigger_config,
            }
        }
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(result['id'], self.recipe_type.id)
        self.assertEqual(result['title'], self.recipe_type.title)
        self.assertEqual(result['revision_num'], 1)
        self.assertIsNotNone(result['definition'])
        self.assertEqual(result['trigger_rule']['configuration']['condition']['media_type'], 'application/json')
        self.assertNotEqual(result['trigger_rule']['id'], self.trigger_rule.id)

    def test_edit_trigger_rule_pause(self):
        '''Tests pausing the trigger rule of a recipe type'''
        trigger_config = self.trigger_config.copy()
        trigger_config['condition']['media_type'] = 'application/json'

        url = '/recipe-types/%d/' % self.recipe_type.id
        json_data = {
            'trigger_rule': {
                'is_active': False,
            }
        }
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(result['id'], self.recipe_type.id)
        self.assertEqual(result['title'], self.recipe_type.title)
        self.assertEqual(result['revision_num'], 1)
        self.assertIsNotNone(result['definition'])
        self.assertEqual(result['trigger_rule']['is_active'], False)

    def test_edit_trigger_rule_remove(self):
        '''Tests removing the trigger rule from a recipe type'''
        url = '/recipe-types/%d/' % self.recipe_type.id
        json_data = {
            'trigger_rule': None,
        }
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(result['id'], self.recipe_type.id)
        self.assertEqual(result['title'], self.recipe_type.title)
        self.assertEqual(result['revision_num'], 1)
        self.assertIsNotNone(result['definition'])
        self.assertIsNone(result['trigger_rule'])

    def test_edit_definition_and_trigger_rule(self):
        '''Tests editing the recipe type definition and trigger rule together'''
        definition = self.definition.copy()
        definition['input_data'] = [{
            'name': 'input_file',
            'type': 'file',
            'media_types': ['text/plain'],
        }]
        trigger_config = self.trigger_config.copy()
        trigger_config['condition']['media_type'] = 'application/json'

        url = '/recipe-types/%d/' % self.recipe_type.id
        json_data = {
            'definition': definition,
            'trigger_rule': {
                'type': 'PARSE',
                'configuration': trigger_config,
            }
        }
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(result['id'], self.recipe_type.id)
        self.assertEqual(result['title'], self.recipe_type.title)
        self.assertEqual(result['revision_num'], 2)
        self.assertEqual(len(result['definition']['input_data']), 1)
        self.assertEqual(result['definition']['input_data'][0]['name'], 'input_file')
        self.assertEqual(result['trigger_rule']['configuration']['condition']['media_type'], 'application/json')
        self.assertNotEqual(result['trigger_rule']['id'], self.trigger_rule.id)

    def test_edit_bad_definition(self):
        '''Tests attempting to edit a recipe type using an invalid recipe definition'''
        definition = self.definition.copy()
        definition['version'] = 'BAD'

        url = '/recipe-types/%d/' % self.recipe_type.id
        json_data = {
            'definition': definition,
        }
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_edit_bad_trigger(self):
        '''Tests attempting to edit a recipe type using an invalid trigger rule'''
        trigger_config = self.trigger_config.copy()
        trigger_config['version'] = 'BAD'

        url = '/recipe-types/%d/' % self.recipe_type.id
        json_data = {
            'trigger_rule': {
                'type': 'PARSE',
                'configuration': trigger_config,
            }
        }
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestRecipeTypesValidationView(TransactionTestCase):
    '''Tests related to the recipe-types validation endpoint'''

    def setUp(self):
        django.setup()

        self.workspace = storage_test_utils.create_workspace()
        self.job_type = job_test_utils.create_job_type()

    def test_successful(self):
        '''Tests validating a new recipe type.'''
        url = '/recipe-types/validation/'
        json_data = {
            'name': 'recipe-type-test',
            'version': '1.0.0',
            'title': 'Recipe Type Test',
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
        self.assertDictEqual(results, {'warnings': []}, 'JSON result was incorrect')

    def test_successful_trigger(self):
        '''Tests validating a new recipe type with a trigger.'''
        url = '/recipe-types/validation/'
        json_data = {
            'name': 'recipe-type-test',
            'version': '1.0.0',
            'title': 'Recipe Type Test',
            'description': 'This is a test.',
            'definition': {
                'version': '1.0',
                'input_data': [{
                    'name': 'input_file',
                    'type': 'file',
                    'media_types': ['image/x-hdf5-image'],
                }],
                'jobs': [],
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

    def test_bad_trigger_type(self):
        '''Tests validating a new recipe type with an invalid trigger type.'''
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
            },
            'trigger_rule': {
                'type': 'BAD',
            }
        }

        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bad_trigger_config(self):
        '''Tests validating a new recipe type with an invalid trigger rule configuration.'''
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


class TestRecipesView(TransactionTestCase):

    def setUp(self):
        django.setup()

        self.job_type1 = job_test_utils.create_job_type()

        definition = {
            'version': '1.0',
            'input_data': [{
                'media_types': [
                    'image/x-hdf5-image',
                ],
                'type': 'file',
                'name': 'input_file',
            }],
            'jobs': [{
                'job_type': {
                    'name': self.job_type1.name,
                    'version': self.job_type1.version,
                },
                'name': 'kml',
                'recipe_inputs': [{
                    'job_input': 'input_file',
                    'recipe_input': 'input_file',
                }],
            }],
        }

        self.recipe_type = recipe_test_utils.create_recipe_type(name='my-type', definition=definition)
        self.recipe1 = recipe_test_utils.create_recipe(self.recipe_type)
        self.recipe_job1 = recipe_test_utils.create_recipe_job(recipe=self.recipe1)

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
        self.assertDictEqual(results['jobs'][0]['job']['job_type_rev']['interface'], self.job_type1.interface)
