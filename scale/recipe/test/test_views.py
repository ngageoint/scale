from __future__ import unicode_literals

import datetime
import django
import json

from django.test.testcases import TestCase, TransactionTestCase
from django.utils.timezone import utc

import batch.test.utils as batch_test_utils
import job.test.utils as job_test_utils
import recipe.test.utils as recipe_test_utils
import storage.test.utils as storage_test_utils
import trigger.test.utils as trigger_test_utils
import util.rest as rest_util
from recipe.handlers.graph import RecipeGraph
from recipe.handlers.graph_delta import RecipeGraphDelta
from recipe.models import RecipeNode, RecipeType
from rest_framework import status


class TestRecipeTypesViewV5(TransactionTestCase):
    """Tests related to the recipe-types base endpoint"""
    
    api = 'v5'

    def setUp(self):
        django.setup()

        self.workspace = storage_test_utils.create_workspace()
        self.recipe_type_1 = recipe_test_utils.create_recipe_type()
        self.recipe_type_2 = recipe_test_utils.create_recipe_type()

    def test_list_all(self):
        """Tests getting a list of recipe types."""
        url = '/%s/recipe-types/' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertEqual(len(results['results']), 2)

    def test_create(self):
        """Tests creating a new recipe type."""
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

        url = '/%s/recipe-types/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        recipe_type = RecipeType.objects.filter(name='recipe-type-post-test').first()

        results = json.loads(response.content)
        self.assertEqual(results['id'], recipe_type.id)
        self.assertIsNone(results['trigger_rule'])

    def test_create_trigger(self):
        """Tests creating a new recipe type with a trigger rule."""
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

        url = '/%s/recipe-types/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        recipe_type = RecipeType.objects.filter(name='recipe-type-post-test').first()

        results = json.loads(response.content)
        self.assertEqual(results['id'], recipe_type.id)
        self.assertEqual(results['trigger_rule']['type'], 'PARSE')

    def test_create_bad_param(self):
        """Tests creating a new recipe type with missing fields."""
        json_data = {
            'name': 'recipe-type-post-test',
        }

        url = '/%s/recipe-types/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_create_bad_job(self):
        """Tests creating a new recipe type with an invalid job relationship."""
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

        url = '/%s/recipe-types/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_create_bad_trigger_type(self):
        """Tests creating a new recipe type with an invalid trigger type."""
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

        url = '/%s/recipe-types/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_create_bad_trigger_config(self):
        """Tests creating a new recipe type with an invalid trigger rule configuration."""
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

        url = '/%s/recipe-types/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)


class TestRecipeTypesViewV6(TransactionTestCase):
    """Tests related to the recipe-types base endpoint"""
    
    api = 'v6'

    def setUp(self):
        django.setup()

        self.workspace = storage_test_utils.create_workspace()
        self.recipe_type_1 = recipe_test_utils.create_recipe_type()
        self.recipe_type_2 = recipe_test_utils.create_recipe_type()

    def test_list_all(self):
        """Tests getting a list of recipe types."""
        url = '/%s/recipe-types/' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertEqual(len(results['results']), 2)

    def test_create(self):
        """Tests creating a new recipe type."""
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

        url = '/%s/recipe-types/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        recipe_type = RecipeType.objects.filter(name='recipe-type-post-test').first()

        results = json.loads(response.content)
        self.assertEqual(results['id'], recipe_type.id)
        self.assertIsNone(results['trigger_rule'])

    def test_create_trigger(self):
        """Tests creating a new recipe type with a trigger rule."""
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

        url = '/%s/recipe-types/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        recipe_type = RecipeType.objects.filter(name='recipe-type-post-test').first()

        results = json.loads(response.content)
        self.assertEqual(results['id'], recipe_type.id)
        self.assertEqual(results['trigger_rule']['type'], 'PARSE')

    def test_create_bad_param(self):
        """Tests creating a new recipe type with missing fields."""
        json_data = {
            'name': 'recipe-type-post-test',
        }

        url = '/%s/recipe-types/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_create_bad_job(self):
        """Tests creating a new recipe type with an invalid job relationship."""
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

        url = '/%s/recipe-types/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_create_bad_trigger_type(self):
        """Tests creating a new recipe type with an invalid trigger type."""
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

        url = '/%s/recipe-types/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_create_bad_trigger_config(self):
        """Tests creating a new recipe type with an invalid trigger rule configuration."""
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

        url = '/%s/recipe-types/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)


class TestRecipeTypeDetailsViewV5(TransactionTestCase):
    """Tests related to the recipe-types details endpoint"""
    
    api = 'v5'

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
        """Tests calling the recipe type details view with an id that does not exist."""

        url = '/%s/recipe-types/2345908/' % self.api
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

    def test_successful(self):
        """Tests successfully calling the recipe type details view."""

        url = '/%s/recipe-types/%d/' % (self.api, self.recipe_type.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

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
        """Tests editing only the basic attributes of a recipe type"""

        json_data = {
            'title': 'Title EDIT',
            'description': 'Description EDIT',
        }

        url = '/%s/recipe-types/%d/' % (self.api, self.recipe_type.id)
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
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
        """Tests editing the definition of a recipe type"""
        definition = self.definition.copy()
        definition['input_data'] = [{
            'name': 'input_file',
            'type': 'file',
            'media_types': ['text/plain'],
        }]

        json_data = {
            'definition': definition,
        }

        url = '/%s/recipe-types/%d/' % (self.api, self.recipe_type.id)
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(result['id'], self.recipe_type.id)
        self.assertEqual(result['title'], self.recipe_type.title)
        self.assertEqual(result['revision_num'], 2)
        self.assertEqual(len(result['definition']['input_data']), 1)
        self.assertEqual(result['definition']['input_data'][0]['name'], 'input_file')
        self.assertEqual(result['trigger_rule']['id'], self.trigger_rule.id)

    def test_edit_trigger_rule(self):
        """Tests editing the trigger rule of a recipe type"""
        trigger_config = self.trigger_config.copy()
        trigger_config['condition']['media_type'] = 'application/json'

        json_data = {
            'trigger_rule': {
                'type': 'PARSE',
                'configuration': trigger_config,
            }
        }

        url = '/%s/recipe-types/%d/' % (self.api, self.recipe_type.id)
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(result['id'], self.recipe_type.id)
        self.assertEqual(result['title'], self.recipe_type.title)
        self.assertEqual(result['revision_num'], 1)
        self.assertIsNotNone(result['definition'])
        self.assertEqual(result['trigger_rule']['configuration']['condition']['media_type'], 'application/json')
        self.assertNotEqual(result['trigger_rule']['id'], self.trigger_rule.id)

    def test_edit_trigger_rule_pause(self):
        """Tests pausing the trigger rule of a recipe type"""
        trigger_config = self.trigger_config.copy()
        trigger_config['condition']['media_type'] = 'application/json'

        json_data = {
            'trigger_rule': {
                'is_active': False,
            }
        }

        url = '/%s/recipe-types/%d/' % (self.api, self.recipe_type.id)
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(result['id'], self.recipe_type.id)
        self.assertEqual(result['title'], self.recipe_type.title)
        self.assertEqual(result['revision_num'], 1)
        self.assertIsNotNone(result['definition'])
        self.assertEqual(result['trigger_rule']['is_active'], False)

    def test_edit_trigger_rule_remove(self):
        """Tests removing the trigger rule from a recipe type"""
        json_data = {
            'trigger_rule': None,
        }

        url = '/%s/recipe-types/%d/' % (self.api, self.recipe_type.id)
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(result['id'], self.recipe_type.id)
        self.assertEqual(result['title'], self.recipe_type.title)
        self.assertEqual(result['revision_num'], 1)
        self.assertIsNotNone(result['definition'])
        self.assertIsNone(result['trigger_rule'])

    def test_edit_definition_and_trigger_rule(self):
        """Tests editing the recipe type definition and trigger rule together"""
        definition = self.definition.copy()
        definition['input_data'] = [{
            'name': 'input_file',
            'type': 'file',
            'media_types': ['text/plain'],
        }]
        trigger_config = self.trigger_config.copy()
        trigger_config['condition']['media_type'] = 'application/json'

        json_data = {
            'definition': definition,
            'trigger_rule': {
                'type': 'PARSE',
                'configuration': trigger_config,
            }
        }

        url = '/%s/recipe-types/%d/' % (self.api, self.recipe_type.id)
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(result['id'], self.recipe_type.id)
        self.assertEqual(result['title'], self.recipe_type.title)
        self.assertEqual(result['revision_num'], 2)
        self.assertEqual(len(result['definition']['input_data']), 1)
        self.assertEqual(result['definition']['input_data'][0]['name'], 'input_file')
        self.assertEqual(result['trigger_rule']['configuration']['condition']['media_type'], 'application/json')
        self.assertNotEqual(result['trigger_rule']['id'], self.trigger_rule.id)

    def test_edit_bad_definition(self):
        """Tests attempting to edit a recipe type using an invalid recipe definition"""
        definition = self.definition.copy()
        definition['version'] = 'BAD'

        json_data = {
            'definition': definition,
        }

        url = '/%s/recipe-types/%d/' % (self.api, self.recipe_type.id)
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_edit_bad_trigger(self):
        """Tests attempting to edit a recipe type using an invalid trigger rule"""
        trigger_config = self.trigger_config.copy()
        trigger_config['version'] = 'BAD'

        json_data = {
            'trigger_rule': {
                'type': 'PARSE',
                'configuration': trigger_config,
            }
        }

        url = '/%s/recipe-types/%d/' % (self.api, self.recipe_type.id)
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)


class TestRecipeTypeDetailsViewV6(TransactionTestCase):
    """Tests related to the recipe-types details endpoint"""
    
    api = 'v6'

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
        """Tests calling the recipe type details view with an id that does not exist."""

        url = '/%s/recipe-types/1235134/' % self.api
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

    def test_successful(self):
        """Tests successfully calling the recipe type details view."""

        url = '/%s/recipe-types/%d/' % (self.api, self.recipe_type.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

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
        """Tests editing only the basic attributes of a recipe type"""

        json_data = {
            'title': 'Title EDIT',
            'description': 'Description EDIT',
        }

        url = '/%s/recipe-types/%d/' % (self.api, self.recipe_type.id)
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
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
        """Tests editing the definition of a recipe type"""
        definition = self.definition.copy()
        definition['input_data'] = [{
            'name': 'input_file',
            'type': 'file',
            'media_types': ['text/plain'],
        }]

        json_data = {
            'definition': definition,
        }

        url = '/%s/recipe-types/%d/' % (self.api, self.recipe_type.id)
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(result['id'], self.recipe_type.id)
        self.assertEqual(result['title'], self.recipe_type.title)
        self.assertEqual(result['revision_num'], 2)
        self.assertEqual(len(result['definition']['input_data']), 1)
        self.assertEqual(result['definition']['input_data'][0]['name'], 'input_file')
        self.assertEqual(result['trigger_rule']['id'], self.trigger_rule.id)

    def test_edit_trigger_rule(self):
        """Tests editing the trigger rule of a recipe type"""
        trigger_config = self.trigger_config.copy()
        trigger_config['condition']['media_type'] = 'application/json'

        json_data = {
            'trigger_rule': {
                'type': 'PARSE',
                'configuration': trigger_config,
            }
        }

        url = '/%s/recipe-types/%d/' % (self.api, self.recipe_type.id)
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(result['id'], self.recipe_type.id)
        self.assertEqual(result['title'], self.recipe_type.title)
        self.assertEqual(result['revision_num'], 1)
        self.assertIsNotNone(result['definition'])
        self.assertEqual(result['trigger_rule']['configuration']['condition']['media_type'], 'application/json')
        self.assertNotEqual(result['trigger_rule']['id'], self.trigger_rule.id)

    def test_edit_trigger_rule_pause(self):
        """Tests pausing the trigger rule of a recipe type"""
        trigger_config = self.trigger_config.copy()
        trigger_config['condition']['media_type'] = 'application/json'

        json_data = {
            'trigger_rule': {
                'is_active': False,
            }
        }

        url = '/%s/recipe-types/%d/' % (self.api, self.recipe_type.id)
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(result['id'], self.recipe_type.id)
        self.assertEqual(result['title'], self.recipe_type.title)
        self.assertEqual(result['revision_num'], 1)
        self.assertIsNotNone(result['definition'])
        self.assertEqual(result['trigger_rule']['is_active'], False)

    def test_edit_trigger_rule_remove(self):
        """Tests removing the trigger rule from a recipe type"""
        json_data = {
            'trigger_rule': None,
        }

        url = '/%s/recipe-types/%d/' % (self.api, self.recipe_type.id)
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(result['id'], self.recipe_type.id)
        self.assertEqual(result['title'], self.recipe_type.title)
        self.assertEqual(result['revision_num'], 1)
        self.assertIsNotNone(result['definition'])
        self.assertIsNone(result['trigger_rule'])

    def test_edit_definition_and_trigger_rule(self):
        """Tests editing the recipe type definition and trigger rule together"""
        definition = self.definition.copy()
        definition['input_data'] = [{
            'name': 'input_file',
            'type': 'file',
            'media_types': ['text/plain'],
        }]
        trigger_config = self.trigger_config.copy()
        trigger_config['condition']['media_type'] = 'application/json'

        json_data = {
            'definition': definition,
            'trigger_rule': {
                'type': 'PARSE',
                'configuration': trigger_config,
            }
        }

        url = '/%s/recipe-types/%d/' % (self.api, self.recipe_type.id)
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(result['id'], self.recipe_type.id)
        self.assertEqual(result['title'], self.recipe_type.title)
        self.assertEqual(result['revision_num'], 2)
        self.assertEqual(len(result['definition']['input_data']), 1)
        self.assertEqual(result['definition']['input_data'][0]['name'], 'input_file')
        self.assertEqual(result['trigger_rule']['configuration']['condition']['media_type'], 'application/json')
        self.assertNotEqual(result['trigger_rule']['id'], self.trigger_rule.id)

    def test_edit_bad_definition(self):
        """Tests attempting to edit a recipe type using an invalid recipe definition"""
        definition = self.definition.copy()
        definition['version'] = 'BAD'

        json_data = {
            'definition': definition,
        }

        url = '/%s/recipe-types/%d/' % (self.api, self.recipe_type.id)
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_edit_bad_trigger(self):
        """Tests attempting to edit a recipe type using an invalid trigger rule"""
        trigger_config = self.trigger_config.copy()
        trigger_config['version'] = 'BAD'

        json_data = {
            'trigger_rule': {
                'type': 'PARSE',
                'configuration': trigger_config,
            }
        }

        url = '/%s/recipe-types/%d/' % (self.api, self.recipe_type.id)
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)


class TestRecipeTypesValidationViewV5(TransactionTestCase):
    """Tests related to the recipe-types validation endpoint"""
    
    api = 'v5'

    def setUp(self):
        django.setup()

        self.workspace = storage_test_utils.create_workspace()
        self.job_type = job_test_utils.create_job_type()

    def test_successful(self):
        """Tests validating a new recipe type."""
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

        url = '/%s/recipe-types/validation/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertDictEqual(results, {'warnings': []}, 'JSON result was incorrect')

    def test_successful_trigger(self):
        """Tests validating a new recipe type with a trigger."""
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

        url = '/%s/recipe-types/validation/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertDictEqual(results, {'warnings': []}, 'JSON result was incorrect')

    def test_bad_param(self):
        """Tests validating a new recipe type with missing fields."""
        json_data = {
            'name': 'recipe-type-post-test',
        }

        url = '/%s/recipe-types/validation/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_bad_job(self):
        """Tests creating a new recipe type with an invalid job relationship."""
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

        url = '/%s/recipe-types/validation/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_warnings(self):
        """Tests creating a new recipe type with mismatched media type warnings."""
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

        url = '/%s/recipe-types/validation/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertEqual(len(results['warnings']), 2)
        self.assertEqual(results['warnings'][0]['id'], 'media_type')
        self.assertEqual(results['warnings'][1]['id'], 'media_type')

    def test_bad_trigger_type(self):
        """Tests validating a new recipe type with an invalid trigger type."""
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

        url = '/%s/recipe-types/validation/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_bad_trigger_config(self):
        """Tests validating a new recipe type with an invalid trigger rule configuration."""
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

        url = '/%s/recipe-types/validation/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)


class TestRecipeTypesValidationViewV6(TransactionTestCase):
    """Tests related to the recipe-types validation endpoint"""
    
    api = 'v6'

    def setUp(self):
        django.setup()

        self.workspace = storage_test_utils.create_workspace()
        self.job_type = job_test_utils.create_job_type()

    def test_successful(self):
        """Tests validating a new recipe type."""
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

        url = '/%s/recipe-types/validation/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertDictEqual(results, {'warnings': []}, 'JSON result was incorrect')

    def test_successful_trigger(self):
        """Tests validating a new recipe type with a trigger."""
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

        url = '/%s/recipe-types/validation/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertDictEqual(results, {'warnings': []}, 'JSON result was incorrect')

    def test_bad_param(self):
        """Tests validating a new recipe type with missing fields."""
        json_data = {
            'name': 'recipe-type-post-test',
        }

        url = '/%s/recipe-types/validation/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_bad_job(self):
        """Tests creating a new recipe type with an invalid job relationship."""
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

        url = '/%s/recipe-types/validation/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_warnings(self):
        """Tests creating a new recipe type with mismatched media type warnings."""
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

        url = '/%s/recipe-types/validation/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertEqual(len(results['warnings']), 2)
        self.assertEqual(results['warnings'][0]['id'], 'media_type')
        self.assertEqual(results['warnings'][1]['id'], 'media_type')

    def test_bad_trigger_type(self):
        """Tests validating a new recipe type with an invalid trigger type."""
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

        url = '/%s/recipe-types/validation/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_bad_trigger_config(self):
        """Tests validating a new recipe type with an invalid trigger rule configuration."""
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

        url = '/%s/recipe-types/validation/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)


class TestRecipesViewV5(TransactionTestCase):
    
    api = 'v5'

    def setUp(self):
        django.setup()

        self.job_type1 = job_test_utils.create_job_type(name='scale-batch-creator')

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

        workspace1 = storage_test_utils.create_workspace()
        file1 = storage_test_utils.create_file(workspace=workspace1)

        data = {
            'version': '1.0',
            'input_data': [{
                'name': 'input_file',
                'file_id': file1.id,
            }],
            'workspace_id': workspace1.id,
        }

        self.recipe_type = recipe_test_utils.create_recipe_type(name='my-type', definition=definition)
        recipe_handler = recipe_test_utils.create_recipe_handler(recipe_type=self.recipe_type, data=data)
        self.recipe1 = recipe_handler.recipe
        self.recipe1_jobs = recipe_handler.recipe_jobs

        self.recipe2 = recipe_test_utils.create_recipe()
        self.recipe3 = recipe_test_utils.create_recipe(is_superseded=True)

    def test_successful_all(self):
        """Tests getting recipes"""

        url = '/%s/recipes/' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertEqual(results['count'], 2)

    def test_successful_batch(self):
        """Tests getting recipes by batch id"""

        batch = batch_test_utils.create_batch()
        self.recipe1.batch_id = batch.id
        self.recipe1.save()

        url = '/%s/recipes/?batch_id=%d' % (self.api, batch.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertEqual(results['count'], 1)
        self.assertEqual(results['results'][0]['recipe_type']['id'], self.recipe_type.id)

    def test_successful_type_name(self):
        """Tests getting recipes by type name"""

        url = '/%s/recipes/?type_name=my-type' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertEqual(results['count'], 1)
        self.assertEqual(results['results'][0]['recipe_type']['name'], 'my-type')

    def test_successful_type_id(self):
        """Tests getting recipes by type id"""

        url = '/%s/recipes/?type_id=%s' % (self.api, self.recipe_type.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertEqual(results['count'], 1)
        self.assertEqual(results['results'][0]['recipe_type']['id'], self.recipe_type.id)

    def test_successful_superseded(self):
        """Tests getting superseded recipes"""

        url = '/%s/recipes/?include_superseded=true' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertEqual(results['count'], 3)

    def test_successful_details(self):
        """Tests getting recipe details"""

        url = '/%s/recipes/%s/' % (self.api, self.recipe1.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertEqual(results['id'], self.recipe1.id)
        self.assertEqual(results['recipe_type']['id'], self.recipe1.recipe_type.id)
        self.assertEqual(results['recipe_type_rev']['recipe_type']['id'], self.recipe1.recipe_type.id)
        self.assertDictEqual(results['jobs'][0]['job']['job_type_rev']['interface'], self.job_type1.manifest)

    def test_superseded(self):
        """Tests successfully calling the recipe details view for superseded recipes."""

        graph1 = RecipeGraph()
        graph1.add_job('kml', self.job_type1.name, self.job_type1.version)
        graph2 = RecipeGraph()
        graph2.add_job('kml', self.job_type1.name, self.job_type1.version)
        delta = RecipeGraphDelta(graph1, graph2)

        superseded_jobs = {recipe_job.node_name: recipe_job.job for recipe_job in self.recipe1_jobs}
        new_recipe = recipe_test_utils.create_recipe_handler(
            recipe_type=self.recipe_type, superseded_recipe=self.recipe1, delta=delta, superseded_jobs=superseded_jobs
        ).recipe

        # Make sure the original recipe was updated
        url = '/%s/recipes/%i/' % (self.api, self.recipe1.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertTrue(result['is_superseded'])
        self.assertIsNone(result['root_superseded_recipe'])
        self.assertIsNotNone(result['superseded_by_recipe'])
        self.assertEqual(result['superseded_by_recipe']['id'], new_recipe.id)
        self.assertIsNotNone(result['superseded'])
        self.assertEqual(len(result['jobs']), 1)
        for recipe_job in result['jobs']:
            self.assertTrue(recipe_job['is_original'])

        # Make sure the new recipe has the expected relations
        url = '/%s/recipes/%i/' % (self.api, new_recipe.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertFalse(result['is_superseded'])
        self.assertIsNotNone(result['root_superseded_recipe'])
        self.assertEqual(result['root_superseded_recipe']['id'], self.recipe1.id)
        self.assertIsNotNone(result['superseded_recipe'])
        self.assertEqual(result['superseded_recipe']['id'], self.recipe1.id)
        self.assertIsNone(result['superseded'])
        self.assertEqual(len(result['jobs']), 1)
        for recipe_job in result['jobs']:
            self.assertFalse(recipe_job['is_original'])


class TestRecipesViewV6(TransactionTestCase):
    
    api = 'v6'

    def setUp(self):
        django.setup()

        self.job_type1 = job_test_utils.create_job_type(name='scale-batch-creator')

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

        workspace1 = storage_test_utils.create_workspace()
        file1 = storage_test_utils.create_file(workspace=workspace1)

        data = {
            'version': '1.0',
            'input_data': [{
                'name': 'input_file',
                'file_id': file1.id,
            }],
            'workspace_id': workspace1.id,
        }

        self.recipe_type = recipe_test_utils.create_recipe_type(name='my-type', definition=definition)
        recipe_handler = recipe_test_utils.create_recipe_handler(recipe_type=self.recipe_type, data=data)
        self.recipe1 = recipe_handler.recipe
        self.recipe1_jobs = recipe_handler.recipe_jobs

        self.recipe2 = recipe_test_utils.create_recipe()
        self.recipe3 = recipe_test_utils.create_recipe(is_superseded=True)

    def test_successful_all(self):
        """Tests getting recipes"""

        url = '/%s/recipes/' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertEqual(results['count'], 2)

    def test_successful_batch(self):
        """Tests getting recipes by batch id"""

        batch = batch_test_utils.create_batch()
        self.recipe1.batch_id = batch.id
        self.recipe1.save()

        url = '/%s/recipes/?batch_id=%d' % (self.api, batch.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertEqual(results['count'], 1)
        self.assertEqual(results['results'][0]['recipe_type']['id'], self.recipe_type.id)

    def test_successful_type_name(self):
        """Tests getting recipes by type name"""

        url = '/%s/recipes/?type_name=my-type' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertEqual(results['count'], 1)
        self.assertEqual(results['results'][0]['recipe_type']['name'], 'my-type')

    def test_successful_type_id(self):
        """Tests getting recipes by type id"""

        url = '/%s/recipes/?type_id=%s' % (self.api, self.recipe_type.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertEqual(results['count'], 1)
        self.assertEqual(results['results'][0]['recipe_type']['id'], self.recipe_type.id)

    def test_successful_superseded(self):
        """Tests getting superseded recipes"""

        url = '/%s/recipes/?include_superseded=true' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertEqual(results['count'], 3)

    def test_successful_details(self):
        """Tests getting recipe details"""

        url = '/%s/recipes/%s/' % (self.api, self.recipe1.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertEqual(results['id'], self.recipe1.id)
        self.assertEqual(results['recipe_type']['id'], self.recipe1.recipe_type.id)
        self.assertEqual(results['recipe_type_rev']['recipe_type']['id'], self.recipe1.recipe_type.id)
        self.assertEqual(results['jobs'][0]['job']['job_type_rev']['revision_num'], self.job_type1.revision_num)

    def test_superseded(self):
        """Tests successfully calling the recipe details view for superseded recipes."""

        graph1 = RecipeGraph()
        graph1.add_job('kml', self.job_type1.name, self.job_type1.version)
        graph2 = RecipeGraph()
        graph2.add_job('kml', self.job_type1.name, self.job_type1.version)
        delta = RecipeGraphDelta(graph1, graph2)

        superseded_jobs = {recipe_job.node_name: recipe_job.job for recipe_job in self.recipe1_jobs}
        new_recipe = recipe_test_utils.create_recipe_handler(
            recipe_type=self.recipe_type, superseded_recipe=self.recipe1, delta=delta, superseded_jobs=superseded_jobs
        ).recipe

        # Make sure the original recipe was updated
        url = '/%s/recipes/%i/' % (self.api, self.recipe1.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertTrue(result['is_superseded'])
        self.assertIsNone(result['root_superseded_recipe'])
        self.assertIsNotNone(result['superseded_by_recipe'])
        self.assertEqual(result['superseded_by_recipe']['id'], new_recipe.id)
        self.assertIsNotNone(result['superseded'])
        self.assertEqual(len(result['jobs']), 1)
        for recipe_job in result['jobs']:
            self.assertTrue(recipe_job['is_original'])

        # Make sure the new recipe has the expected relations
        url = '/%s/recipes/%i/' % (self.api, new_recipe.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertFalse(result['is_superseded'])
        self.assertIsNotNone(result['root_superseded_recipe'])
        self.assertEqual(result['root_superseded_recipe']['id'], self.recipe1.id)
        self.assertIsNotNone(result['superseded_recipe'])
        self.assertEqual(result['superseded_recipe']['id'], self.recipe1.id)
        self.assertIsNone(result['superseded'])
        self.assertEqual(len(result['jobs']), 1)
        for recipe_job in result['jobs']:
            self.assertFalse(recipe_job['is_original'])
            



class TestRecipesPostViewV6(TransactionTestCase):
    
    api = 'v6'

    def setUp(self):
        django.setup()

        self.job_type1 = job_test_utils.create_job_type(name='scale-batch-creator')

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

        workspace1 = storage_test_utils.create_workspace()
        file1 = storage_test_utils.create_file(workspace=workspace1)

        data = {
            'version': '1.0',
            'input_data': [{
                'name': 'input_file',
                'file_id': file1.id,
            }],
            'workspace_id': workspace1.id,
        }

        self.recipe_type = recipe_test_utils.create_recipe_type(name='my-type', definition=definition)
        recipe_handler = recipe_test_utils.create_recipe_handler(recipe_type=self.recipe_type, data=data)
        self.recipe1 = recipe_handler.recipe
        self.recipe1_jobs = recipe_handler.recipe_jobs

        self.recipe2 = recipe_test_utils.create_recipe()
        self.recipe3 = recipe_test_utils.create_recipe(is_superseded=True)

    def test_successful(self):

        
        json_data = { 
            "input" : {},
            "recipe_type_id" : self.recipe_type.pk
        }

        url = '/%s/recipes/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        #Response should be new v6 job detail response

            
class TestRecipeDetailsViewV6(TransactionTestCase):
    
    api = 'v6'

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

        workspace1 = storage_test_utils.create_workspace()
        file1 = storage_test_utils.create_file(workspace=workspace1)

        data = {
            'version': '1.0',
            'input_data': [{
                'name': 'input_file',
                'file_id': file1.id,
            }],
            'workspace_id': workspace1.id,
        }

        self.recipe_type = recipe_test_utils.create_recipe_type(name='my-type', definition=definition)
        recipe_handler = recipe_test_utils.create_recipe_handler(recipe_type=self.recipe_type, data=data)
        self.recipe1 = recipe_handler.recipe
        self.recipe1_jobs = recipe_handler.recipe_jobs

    def test_successful(self):
        """Tests getting recipe details"""

        url = '/%s/recipes/%i/' % (self.api, self.recipe1.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(result['id'], self.recipe1.id)
        self.assertEqual(result['recipe_type']['id'], self.recipe1.recipe_type.id)
        self.assertEqual(result['recipe_type_rev']['recipe_type']['id'], self.recipe1.recipe_type.id)
        self.assertEqual(result['jobs'][0]['job']['job_type_rev']['revision_num'], self.job_type1.revision_num)
        self.assertDictEqual(result['input'], self.recipe1.input)
        self.assertTrue('inputs' not in result)
        self.assertTrue('definiton' not in result['recipe_type'])

    def test_superseded(self):
        """Tests successfully calling the recipe details view for superseded recipes."""

        graph1 = RecipeGraph()
        graph1.add_job('kml', self.job_type1.name, self.job_type1.version)
        graph2 = RecipeGraph()
        graph2.add_job('kml', self.job_type1.name, self.job_type1.version)
        delta = RecipeGraphDelta(graph1, graph2)

        superseded_jobs = {recipe_job.node_name: recipe_job.job for recipe_job in self.recipe1_jobs}
        new_recipe = recipe_test_utils.create_recipe_handler(
            recipe_type=self.recipe_type, superseded_recipe=self.recipe1, delta=delta, superseded_jobs=superseded_jobs
        ).recipe

        url = '/%s/recipes/%i/' % (self.api,  self.recipe1.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertTrue(result['is_superseded'])
        self.assertIsNone(result['root_superseded_recipe'])
        self.assertIsNotNone(result['superseded_by_recipe'])
        self.assertEqual(result['superseded_by_recipe']['id'], new_recipe.id)
        self.assertIsNotNone(result['superseded'])
        self.assertEqual(len(result['jobs']), 1)
        for recipe_job in result['jobs']:
            self.assertTrue(recipe_job['is_original'])

        url = '/%s/recipes/%i/' % (self.api,  new_recipe.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertFalse(result['is_superseded'])
        self.assertIsNotNone(result['root_superseded_recipe'])
        self.assertEqual(result['root_superseded_recipe']['id'], self.recipe1.id)
        self.assertIsNotNone(result['superseded_recipe'])
        self.assertEqual(result['superseded_recipe']['id'], self.recipe1.id)
        self.assertIsNone(result['superseded'])
        self.assertEqual(len(result['jobs']), 1)
        for recipe_job in result['jobs']:
            self.assertFalse(recipe_job['is_original'])

    
# TODO: remove this class when REST API v5 is removed
class OldTestRecipeDetailsView(TransactionTestCase):
    
    api = 'v5'

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

        workspace1 = storage_test_utils.create_workspace()
        file1 = storage_test_utils.create_file(workspace=workspace1)

        data = {
            'version': '1.0',
            'input_data': [{
                'name': 'input_file',
                'file_id': file1.id,
            }],
            'workspace_id': workspace1.id,
        }

        self.recipe_type = recipe_test_utils.create_recipe_type(name='my-type', definition=definition)
        recipe_handler = recipe_test_utils.create_recipe_handler(recipe_type=self.recipe_type, data=data)
        self.recipe1 = recipe_handler.recipe
        self.recipe1_jobs = recipe_handler.recipe_jobs

    def test_successful(self):
        """Tests getting recipe details"""

        url = '/%s/recipes/%i/' % (self.api, self.recipe1.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(result['id'], self.recipe1.id)
        self.assertEqual(result['recipe_type']['id'], self.recipe1.recipe_type.id)
        self.assertEqual(result['recipe_type_rev']['recipe_type']['id'], self.recipe1.recipe_type.id)
        self.assertDictEqual(result['jobs'][0]['job']['job_type_rev']['interface'], self.job_type1.manifest)

        self.assertEqual(len(result['inputs']), 1)
        for data_input in result['inputs']:
            self.assertIsNotNone(data_input['value'])

    def test_superseded(self):
        """Tests successfully calling the recipe details view for superseded recipes."""

        graph1 = RecipeGraph()
        graph1.add_job('kml', self.job_type1.name, self.job_type1.version)
        graph2 = RecipeGraph()
        graph2.add_job('kml', self.job_type1.name, self.job_type1.version)
        delta = RecipeGraphDelta(graph1, graph2)

        superseded_jobs = {recipe_job.node_name: recipe_job.job for recipe_job in self.recipe1_jobs}
        new_recipe = recipe_test_utils.create_recipe_handler(
            recipe_type=self.recipe_type, superseded_recipe=self.recipe1, delta=delta, superseded_jobs=superseded_jobs
        ).recipe

        # Make sure the original recipe was updated
        url = '/%s/recipes/%i/' % (self.api, self.recipe1.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertTrue(result['is_superseded'])
        self.assertIsNone(result['root_superseded_recipe'])
        self.assertIsNotNone(result['superseded_by_recipe'])
        self.assertEqual(result['superseded_by_recipe']['id'], new_recipe.id)
        self.assertIsNotNone(result['superseded'])
        self.assertEqual(len(result['jobs']), 1)
        for recipe_job in result['jobs']:
            self.assertTrue(recipe_job['is_original'])

        # Make sure the new recipe has the expected relations
        url = '/%s/recipes/%i/' % (self.api, new_recipe.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertFalse(result['is_superseded'])
        self.assertIsNotNone(result['root_superseded_recipe'])
        self.assertEqual(result['root_superseded_recipe']['id'], self.recipe1.id)
        self.assertIsNotNone(result['superseded_recipe'])
        self.assertEqual(result['superseded_recipe']['id'], self.recipe1.id)
        self.assertIsNone(result['superseded'])
        self.assertEqual(len(result['jobs']), 1)
        for recipe_job in result['jobs']:
            self.assertFalse(recipe_job['is_original'])


class TestRecipeReprocessViewV5(TransactionTestCase):
    
    api = 'v5'

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

        workspace1 = storage_test_utils.create_workspace()
        file1 = storage_test_utils.create_file(workspace=workspace1)

        data = {
            'version': '1.0',
            'input_data': [{
                'name': 'input_file',
                'file_id': file1.id,
            }],
            'workspace_id': workspace1.id,
        }

        self.recipe_type = recipe_test_utils.create_recipe_type(name='my-type', definition=definition)
        recipe_handler = recipe_test_utils.create_recipe_handler(recipe_type=self.recipe_type, data=data)
        self.recipe1 = recipe_handler.recipe
        self.recipe1_jobs = recipe_handler.recipe_jobs

    def test_all_jobs(self):
        """Tests reprocessing all jobs in an existing recipe"""

        json_data = {
            'all_jobs': True,
        }

        url = '/%s/recipes/%i/reprocess/' % (self.api, self.recipe1.id)
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        results = json.loads(response.content)
        self.assertNotEqual(results['id'], self.recipe1.id)
        self.assertEqual(results['recipe_type']['id'], self.recipe1.recipe_type.id)

    def test_job(self):
        """Tests reprocessing one job in an existing recipe"""

        json_data = {
            'job_names': ['kml'],
        }

        url = '/%s/recipes/%i/reprocess/' % (self.api, self.recipe1.id)
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        results = json.loads(response.content)
        self.assertNotEqual(results['id'], self.recipe1.id)
        self.assertEqual(results['recipe_type']['id'], self.recipe1.recipe_type.id)

    def test_priority(self):
        """Tests reprocessing all jobs in an existing recipe with a priority override"""

        json_data = {
            'all_jobs': True,
            'priority': 1111,
        }

        url = '/%s/recipes/%i/reprocess/' % (self.api, self.recipe1.id)
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        results = json.loads(response.content)
        self.assertNotEqual(results['id'], self.recipe1.id)
        self.assertEqual(results['recipe_type']['id'], self.recipe1.recipe_type.id)

        recipe_job_1 = RecipeNode.objects.get(recipe_id=results['id'], node_name='kml')
        self.assertEqual(recipe_job_1.job.priority, 1111)

    def test_no_changes(self):
        """Tests reprocessing a recipe that has not changed without specifying any jobs throws an error."""

        json_data = {}

        url = '/%s/recipes/%i/reprocess/' % (self.api, self.recipe1.id)
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_superseded(self):
        """Tests reprocessing a recipe that is already superseded throws an error."""

        self.recipe1.is_superseded = True
        self.recipe1.save()

        json_data = {
            'all_jobs': True,
        }

        url = '/%s/recipes/%i/reprocess/' % (self.api, self.recipe1.id)
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)


class TestRecipeReprocessViewV6(TransactionTestCase):
    
    api = 'v6'

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

        workspace1 = storage_test_utils.create_workspace()
        file1 = storage_test_utils.create_file(workspace=workspace1)

        data = {
            'version': '1.0',
            'input_data': [{
                'name': 'input_file',
                'file_id': file1.id,
            }],
            'workspace_id': workspace1.id,
        }

        self.recipe_type = recipe_test_utils.create_recipe_type(name='my-type', definition=definition)
        recipe_handler = recipe_test_utils.create_recipe_handler(recipe_type=self.recipe_type, data=data)
        self.recipe1 = recipe_handler.recipe
        self.recipe1_jobs = recipe_handler.recipe_jobs

    def test_all_jobs(self):
        """Tests reprocessing all jobs in an existing recipe"""

        json_data = {
            'all_jobs': True,
        }

        url = '/%s/recipes/%i/reprocess/' % (self.api, self.recipe1.id)
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        results = json.loads(response.content)
        self.assertNotEqual(results['id'], self.recipe1.id)
        self.assertEqual(results['recipe_type']['id'], self.recipe1.recipe_type.id)

    def test_job(self):
        """Tests reprocessing one job in an existing recipe"""

        json_data = {
            'job_names': ['kml'],
        }

        url = '/%s/recipes/%i/reprocess/' % (self.api, self.recipe1.id)
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        results = json.loads(response.content)
        self.assertNotEqual(results['id'], self.recipe1.id)
        self.assertEqual(results['recipe_type']['id'], self.recipe1.recipe_type.id)

    def test_priority(self):
        """Tests reprocessing all jobs in an existing recipe with a priority override"""

        json_data = {
            'all_jobs': True,
            'priority': 1111,
        }

        url = '/%s/recipes/%i/reprocess/' % (self.api, self.recipe1.id)
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        results = json.loads(response.content)
        self.assertNotEqual(results['id'], self.recipe1.id)
        self.assertEqual(results['recipe_type']['id'], self.recipe1.recipe_type.id)

        recipe_job_1 = RecipeNode.objects.get(recipe_id=results['id'], node_name='kml')
        self.assertEqual(recipe_job_1.job.priority, 1111)

    def test_no_changes(self):
        """Tests reprocessing a recipe that has not changed without specifying any jobs throws an error."""

        json_data = {}

        url = '/%s/recipes/%i/reprocess/' % (self.api, self.recipe1.id)
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_superseded(self):
        """Tests reprocessing a recipe that is already superseded throws an error."""

        self.recipe1.is_superseded = True
        self.recipe1.save()

        json_data = {
            'all_jobs': True,
        }

        url = '/%s/recipes/%i/reprocess/' % (self.api, self.recipe1.id)
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)


class TestRecipeInputFilesViewV5(TestCase):
    
    api = 'v5'

    def setUp(self):

        # Create legacy test files
        self.f1_file_name = 'legacy_foo.bar'
        self.f1_last_modified = datetime.datetime(2016, 1, 2, tzinfo=utc)
        self.f1_source_started = datetime.datetime(2016, 1, 1, tzinfo=utc)
        self.f1_source_ended = datetime.datetime(2016, 1, 2, tzinfo=utc)
        self.file1 = storage_test_utils.create_file(file_name=self.f1_file_name, source_started=self.f1_source_started,
                                                    source_ended=self.f1_source_ended,
                                                    last_modified=self.f1_last_modified)

        self.f2_file_name = 'legacy_qaz.bar'
        self.f2_recipe_input = 'legacy_input_1'
        self.f2_last_modified = datetime.datetime(2016, 1, 3, tzinfo=utc)
        self.f2_source_started = datetime.datetime(2016, 1, 2, tzinfo=utc)
        self.f2_source_ended = datetime.datetime(2016, 1, 3, tzinfo=utc)
        self.file2 = storage_test_utils.create_file(file_name=self.f2_file_name, source_started=self.f2_source_started,
                                                    source_ended=self.f2_source_ended,
                                                    last_modified=self.f2_last_modified)

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

        workspace1 = storage_test_utils.create_workspace()

        data = {
            'version': '1.0',
            'input_data': [{
                'name': 'input_file',
                'file_id': self.file1.id,
            }, {
                'name': self.f2_recipe_input,
                'file_id': self.file2.id,
            }],
            'workspace_id': workspace1.id,
        }

        self.recipe_type = recipe_test_utils.create_recipe_type(name='my-type', definition=definition)
        recipe_handler = recipe_test_utils.create_recipe_handler(recipe_type=self.recipe_type, data=data)
        self.legacy_recipe = recipe_handler.recipe
        self.recipe = recipe_test_utils.create_recipe()

        # Create RecipeInputFile entry files
        self.f3_file_name = 'foo.bar'
        self.f3_last_modified = datetime.datetime(2016, 1, 11, tzinfo=utc)
        self.f3_source_started = datetime.datetime(2016, 1, 10, tzinfo=utc)
        self.f3_source_ended = datetime.datetime(2016, 1, 11, tzinfo=utc)
        self.file3 = recipe_test_utils.create_input_file(file_name=self.f3_file_name,
                                                         source_started=self.f3_source_started,
                                                         source_ended=self.f3_source_ended, recipe=self.recipe,
                                                         last_modified=self.f3_last_modified)

        self.f4_file_name = 'qaz.bar'
        self.f4_recipe_input = 'input_1'
        self.f4_last_modified = datetime.datetime(2016, 1, 12, tzinfo=utc)
        self.f4_source_started = datetime.datetime(2016, 1, 11, tzinfo=utc)
        self.f4_source_ended = datetime.datetime(2016, 1, 12, tzinfo=utc)
        self.file4 = recipe_test_utils.create_input_file(file_name=self.f4_file_name,
                                                         source_started=self.f4_source_started,
                                                         source_ended=self.f4_source_ended, recipe=self.recipe,
                                                         last_modified=self.f4_last_modified,
                                                         recipe_input=self.f4_recipe_input)

    def test_successful_file(self):
        """Tests successfully calling the recipe input files view"""

        url = '/%s/recipes/%i/input_files/' % (self.api, self.recipe.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        results = result['results']
        self.assertEqual(len(results), 2)
        for result in results:
            self.assertTrue(result['id'] in [self.file3.id, self.file4.id])

    def test_legacy_successful_file(self):
        """Tests successfully calling the recipe input files view for legacy files with recipe_data"""

        url = '/%s/recipes/%i/input_files/' % (self.api, self.legacy_recipe.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        results = result['results']
        self.assertEqual(len(results), 2)
        for result in results:
            self.assertTrue(result['id'] in [self.file1.id, self.file2.id])

    def test_filter_recipe_input(self):
        """Tests successfully calling the recipe inputs files view with recipe_input string filtering"""

        url = '/%s/recipes/%i/input_files/?recipe_input=%s' % (self.api, self.recipe.id, self.f4_recipe_input)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        results = result['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], self.file4.id)

    def test_legacy_filter_recipe_input(self):
        """Tests successfully calling the recipe inputs files view for legacy files with recipe_input string filtering"""

        url = '/%s/recipes/%i/input_files/?recipe_input=%s' % (self.api, self.legacy_recipe.id,
                                                                              self.f2_recipe_input)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        results = result['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], self.file2.id)

    def test_file_name_successful(self):
        """Tests successfully calling the get files by name view"""

        url = '/%s/recipes/%i/input_files/?file_name=%s' % (self.api, self.recipe.id, self.f3_file_name)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        result = results['results']
        self.assertEqual(len(result), 1)

        self.assertEqual(self.f3_file_name, result[0]['file_name'])
        self.assertEqual('2016-01-10T00:00:00Z', result[0]['source_started'])
        self.assertEqual(self.file3.id, result[0]['id'])

    def test_bad_file_name(self):
        """Tests unsuccessfully calling the get files by name view"""

        url = '/%s/recipes/%i/input_files/?file_name=%s' % (self.api, self.recipe.id, 'not_a.file')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        result = results['results']
        self.assertEqual(len(result), 0)

    def test_time_successful(self):
        """Tests unsuccessfully calling the get files by name view"""

        url = '/%s/recipes/%i/input_files/?started=%s&ended=%s&time_field=%s' % (self.api, self.recipe.id,
                                                                                                '2016-01-10T00:00:00Z',
                                                                                                '2016-01-13T00:00:00Z',
                                                                                                'source')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        results = result['results']
        self.assertEqual(len(results), 2)
        for result in results:
            self.assertTrue(result['id'] in [self.file3.id, self.file4.id])


class TestRecipeInputFilesViewV6(TestCase):
    
    api = 'v6'

    def setUp(self):

        # Create legacy test files
        self.f1_file_name = 'legacy_foo.bar'
        self.f1_last_modified = datetime.datetime(2016, 1, 2, tzinfo=utc)
        self.f1_source_started = datetime.datetime(2016, 1, 1, tzinfo=utc)
        self.f1_source_ended = datetime.datetime(2016, 1, 2, tzinfo=utc)
        self.file1 = storage_test_utils.create_file(file_name=self.f1_file_name, source_started=self.f1_source_started,
                                                    source_ended=self.f1_source_ended,
                                                    last_modified=self.f1_last_modified)

        self.f2_file_name = 'legacy_qaz.bar'
        self.f2_recipe_input = 'legacy_input_1'
        self.f2_last_modified = datetime.datetime(2016, 1, 3, tzinfo=utc)
        self.f2_source_started = datetime.datetime(2016, 1, 2, tzinfo=utc)
        self.f2_source_ended = datetime.datetime(2016, 1, 3, tzinfo=utc)
        self.file2 = storage_test_utils.create_file(file_name=self.f2_file_name, source_started=self.f2_source_started,
                                                    source_ended=self.f2_source_ended,
                                                    last_modified=self.f2_last_modified)

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

        workspace1 = storage_test_utils.create_workspace()

        data = {
            'version': '1.0',
            'input_data': [{
                'name': 'input_file',
                'file_id': self.file1.id,
            }, {
                'name': self.f2_recipe_input,
                'file_id': self.file2.id,
            }],
            'workspace_id': workspace1.id,
        }

        self.recipe_type = recipe_test_utils.create_recipe_type(name='my-type', definition=definition)
        recipe_handler = recipe_test_utils.create_recipe_handler(recipe_type=self.recipe_type, data=data)
        self.legacy_recipe = recipe_handler.recipe
        self.recipe = recipe_test_utils.create_recipe()

        # Create RecipeInputFile entry files
        self.f3_file_name = 'foo.bar'
        self.f3_last_modified = datetime.datetime(2016, 1, 11, tzinfo=utc)
        self.f3_source_started = datetime.datetime(2016, 1, 10, tzinfo=utc)
        self.f3_source_ended = datetime.datetime(2016, 1, 11, tzinfo=utc)
        self.file3 = recipe_test_utils.create_input_file(file_name=self.f3_file_name,
                                                         source_started=self.f3_source_started,
                                                         source_ended=self.f3_source_ended, recipe=self.recipe,
                                                         last_modified=self.f3_last_modified)

        self.f4_file_name = 'qaz.bar'
        self.f4_recipe_input = 'input_1'
        self.f4_last_modified = datetime.datetime(2016, 1, 12, tzinfo=utc)
        self.f4_source_started = datetime.datetime(2016, 1, 11, tzinfo=utc)
        self.f4_source_ended = datetime.datetime(2016, 1, 12, tzinfo=utc)
        self.file4 = recipe_test_utils.create_input_file(file_name=self.f4_file_name,
                                                         source_started=self.f4_source_started,
                                                         source_ended=self.f4_source_ended, recipe=self.recipe,
                                                         last_modified=self.f4_last_modified,
                                                         recipe_input=self.f4_recipe_input)

    def test_successful_file(self):
        """Tests successfully calling the recipe input files view"""

        url = '/%s/recipes/%i/input_files/' % (self.api, self.recipe.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        results = result['results']
        self.assertEqual(len(results), 2)
        for result in results:
            self.assertTrue(result['id'] in [self.file3.id, self.file4.id])

    def test_legacy_successful_file(self):
        """Tests successfully calling the recipe input files view for legacy files with recipe_data"""

        url = '/%s/recipes/%i/input_files/' % (self.api, self.legacy_recipe.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        results = result['results']
        self.assertEqual(len(results), 2)
        for result in results:
            self.assertTrue(result['id'] in [self.file1.id, self.file2.id])

    def test_filter_recipe_input(self):
        """Tests successfully calling the recipe inputs files view with recipe_input string filtering"""

        url = '/%s/recipes/%i/input_files/?recipe_input=%s' % (self.api, self.recipe.id, self.f4_recipe_input)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        results = result['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], self.file4.id)

    def test_legacy_filter_recipe_input(self):
        """Tests successfully calling the recipe inputs files view for legacy files with recipe_input string filtering"""

        url = '/%s/recipes/%i/input_files/?recipe_input=%s' % (self.api, self.legacy_recipe.id,
                                                                              self.f2_recipe_input)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        results = result['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], self.file2.id)

    def test_file_name_successful(self):
        """Tests successfully calling the get files by name view"""

        url = '/%s/recipes/%i/input_files/?file_name=%s' % (self.api, self.recipe.id, self.f3_file_name)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        result = results['results']
        self.assertEqual(len(result), 1)

        self.assertEqual(self.f3_file_name, result[0]['file_name'])
        self.assertEqual('2016-01-10T00:00:00Z', result[0]['source_started'])
        self.assertEqual(self.file3.id, result[0]['id'])

    def test_bad_file_name(self):
        """Tests unsuccessfully calling the get files by name view"""

        url = '/%s/recipes/%i/input_files/?file_name=%s' % (self.api, self.recipe.id, 'not_a.file')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        result = results['results']
        self.assertEqual(len(result), 0)

    def test_time_successful(self):
        """Tests unsuccessfully calling the get files by name view"""

        url = '/%s/recipes/%i/input_files/?started=%s&ended=%s&time_field=%s' % (self.api, self.recipe.id,
                                                                                                '2016-01-10T00:00:00Z',
                                                                                                '2016-01-13T00:00:00Z',
                                                                                                'source')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        results = result['results']
        self.assertEqual(len(results), 2)
        for result in results:
            self.assertTrue(result['id'] in [self.file3.id, self.file4.id])
