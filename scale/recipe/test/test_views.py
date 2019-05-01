from __future__ import unicode_literals

import copy
import datetime
import django
import json

from django.db import transaction
import django.utils.timezone as timezone
from django.utils.timezone import utc
from mock import patch

import batch.test.utils as batch_test_utils
import job.test.utils as job_test_utils
import recipe.test.utils as recipe_test_utils
import storage.test.utils as storage_test_utils
import source.test.utils as source_test_utils
from job.models import JobType
from recipe.models import Recipe, RecipeType, RecipeTypeJobLink, RecipeTypeSubLink
from recipe.definition.json.definition_v6 import RecipeDefinitionV6
from rest_framework import status
from rest_framework.test import APITestCase, APITransactionTestCase
from util import rest


class MockCommandMessageManager():

    def send_messages(self, commands):
        new_commands = []
        while True:
            for command in commands:
                command.execute()
                new_commands.extend(command.new_messages)
            commands = new_commands
            if not new_commands:
                break
            new_commands = []


class TestRecipeTypesViewV6(APITransactionTestCase):
    """Tests related to the get recipe-types base endpoint"""

    api = 'v6'

    def setUp(self):
        django.setup()

        rest.login_client(self.client, is_staff=True)

        self.job_type1 = job_test_utils.create_seed_job_type(manifest=job_test_utils.MINIMUM_MANIFEST)
        self.job_type2 = job_test_utils.create_seed_job_type()

        self.sub_definition = copy.deepcopy(recipe_test_utils.SUB_RECIPE_DEFINITION)
        self.sub_definition['nodes']['node_a']['node_type']['job_type_name'] = self.job_type1.name
        self.sub_definition['nodes']['node_a']['node_type']['job_type_version'] = self.job_type1.version
        self.sub_definition['nodes']['node_a']['node_type']['job_type_revision'] = self.job_type1.revision_num

        self.recipe_type1 = recipe_test_utils.create_recipe_type_v6(definition=self.sub_definition,
                                                                    description="A sub recipe",
                                                                    is_active=False,
                                                                    is_system=False)

        self.main_definition = copy.deepcopy(recipe_test_utils.RECIPE_DEFINITION)
        self.main_definition['nodes']['node_a']['node_type']['job_type_name'] = self.job_type2.name
        self.main_definition['nodes']['node_a']['node_type']['job_type_version'] = self.job_type2.version
        self.main_definition['nodes']['node_a']['node_type']['job_type_revision'] = self.job_type2.revision_num
        self.main_definition['nodes']['node_b']['node_type']['job_type_name'] = self.job_type2.name
        self.main_definition['nodes']['node_b']['node_type']['job_type_version'] = self.job_type2.version
        self.main_definition['nodes']['node_b']['node_type']['job_type_revision'] = self.job_type2.revision_num
        self.main_definition['nodes']['node_c']['node_type']['recipe_type_name'] = self.recipe_type1.name
        self.main_definition['nodes']['node_c']['node_type']['recipe_type_revision'] = self.recipe_type1.revision_num

        self.recipe_type2 = recipe_test_utils.create_recipe_type_v6(definition=self.main_definition,
                                                                    title="My main recipe",
                                                                    is_active=True,
                                                                    is_system=True)

    def test_list_all(self):
        """Tests getting a list of recipe types."""

        url = '/%s/recipe-types/' % self.api
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertEqual(len(results['results']), 2)

        self.assertIn('deprecated', results['results'][0])

    def test_keyword(self):
        """Tests successfully calling the recipe types view filtered by keyword."""

        url = '/%s/recipe-types/?keyword=%s' % (self.api, self.recipe_type1.name)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['name'], self.recipe_type1.name)

        url = '/%s/recipe-types/?keyword=%s' % (self.api, 'recipe')
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 2)

        url = '/%s/recipe-types/?keyword=%s' % (self.api, 'klj;lkj;sdi')
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 0)

        url = '/%s/recipe-types/?keyword=%s' % (self.api, 'sub')
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['name'], self.recipe_type1.name)

        url = '/%s/recipe-types/?keyword=%s' % (self.api, 'main')
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['name'], self.recipe_type2.name)

        url = '/%s/recipe-types/?keyword=%s&keyword=%s' % (self.api, 'main', 'sub')
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 2)

    def test_is_active(self):
        """Tests successfully calling the recipetypes view filtered by inactive state."""

        url = '/%s/recipe-types/?is_active=false' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['name'], self.recipe_type1.name)

        url = '/%s/recipe-types/?is_active=true' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['name'], self.recipe_type2.name)

    def test_is_system(self):
        """Tests successfully calling the recipe types view filtered by system status."""

        url = '/%s/recipe-types/?is_system=false' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['name'], self.recipe_type1.name)

        url = '/%s/recipe-types/?is_system=true' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['name'], self.recipe_type2.name)


class TestCreateRecipeTypeViewV6(APITransactionTestCase):
    """Tests related to the post recipe-types base endpoint"""

    api = 'v6'

    def setUp(self):
        django.setup()

        rest.login_client(self.client, is_staff=True)

        self.job_type1 = job_test_utils.create_seed_job_type(manifest=job_test_utils.MINIMUM_MANIFEST)
        self.job_type2 = job_test_utils.create_seed_job_type()

        self.sub_definition = copy.deepcopy(recipe_test_utils.SUB_RECIPE_DEFINITION)
        self.sub_definition['nodes']['node_a']['node_type']['job_type_name'] = self.job_type1.name
        self.sub_definition['nodes']['node_a']['node_type']['job_type_version'] = self.job_type1.version
        self.sub_definition['nodes']['node_a']['node_type']['job_type_revision'] = self.job_type1.revision_num

        self.recipe_type1 = recipe_test_utils.create_recipe_type_v6(definition=self.sub_definition,
                                                                    description="A sub recipe",
                                                                    is_active=False,
                                                                    is_system=False)

    def test_create(self):
        """Tests creating a new recipe type."""

        main_definition = copy.deepcopy(recipe_test_utils.RECIPE_DEFINITION)
        main_definition['nodes']['node_a']['node_type']['job_type_name'] = self.job_type2.name
        main_definition['nodes']['node_a']['node_type']['job_type_version'] = self.job_type2.version
        main_definition['nodes']['node_a']['node_type']['job_type_revision'] = self.job_type2.revision_num
        main_definition['nodes']['node_b']['node_type']['job_type_name'] = self.job_type2.name
        main_definition['nodes']['node_b']['node_type']['job_type_version'] = self.job_type2.version
        main_definition['nodes']['node_b']['node_type']['job_type_revision'] = self.job_type2.revision_num
        main_definition['nodes']['node_c']['node_type']['recipe_type_name'] = self.recipe_type1.name
        main_definition['nodes']['node_c']['node_type']['recipe_type_revision'] = self.recipe_type1.revision_num

        json_data = {
            'title': 'Recipe Type Post Test',
            'description': 'This is a test.',
            'definition': main_definition
        }

        url = '/%s/recipe-types/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        recipe_type = RecipeType.objects.filter(name='recipe-type-post-test').first()

        results = json.loads(response.content)
        self.assertEqual(results['id'], recipe_type.id)

        jobs = RecipeTypeJobLink.objects.get_job_type_ids([recipe_type.id])
        self.assertEqual(len(jobs), 1)

        back_links = RecipeTypeJobLink.objects.get_recipe_type_ids(jobs)
        self.assertEqual(len(back_links), 1)
        self.assertEqual(back_links[0], recipe_type.id)

        subs = RecipeTypeSubLink.objects.get_sub_recipe_type_ids([recipe_type.id])
        self.assertEqual(len(subs), 1)

        back_links = RecipeTypeSubLink.objects.get_recipe_type_ids(subs)
        self.assertEqual(len(back_links), 1)
        self.assertEqual(back_links[0], recipe_type.id)

    def test_create_bad_param(self):
        """Tests creating a new recipe type with missing fields."""

        json_data = {
            'name': 'recipe-type-post-test',
        }

        url = '/%s/recipe-types/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_create_bad_job_type(self):
        """Tests creating a new recipe type with job type that doesn't exist."""

        sub_definition = copy.deepcopy(recipe_test_utils.SUB_RECIPE_DEFINITION)

        json_data = {
            'title': 'Recipe Type Post Test',
            'description': 'This is a test.',
            'definition': sub_definition
        }


        url = '/%s/recipe-types/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

class TestRecipeTypeDetailsViewV6(APITransactionTestCase):
    """Tests related to the recipe-types details endpoint"""

    api = 'v6'

    def setUp(self):
        django.setup()

        rest.login_client(self.client, is_staff=True)

        self.job_type1 = job_test_utils.create_seed_job_type(manifest=job_test_utils.MINIMUM_MANIFEST)
        self.job_type2 = job_test_utils.create_seed_job_type()
        manifest=copy.deepcopy(job_test_utils.MINIMUM_MANIFEST)
        manifest['job']['name'] = 'minimum-two'
        self.job_type3 = job_test_utils.create_seed_job_type(manifest=manifest)

        self.workspace = storage_test_utils.create_workspace()

        self.sub_definition = copy.deepcopy(recipe_test_utils.SUB_RECIPE_DEFINITION)
        self.sub_definition['nodes']['node_a']['node_type']['job_type_name'] = self.job_type1.name
        self.sub_definition['nodes']['node_a']['node_type']['job_type_version'] = self.job_type1.version
        self.sub_definition['nodes']['node_a']['node_type']['job_type_revision'] = self.job_type1.revision_num

        self.recipe_type1 = recipe_test_utils.create_recipe_type_v6(definition=self.sub_definition)

        self.main_definition = copy.deepcopy(recipe_test_utils.RECIPE_DEFINITION)
        self.main_definition['nodes']['node_a']['node_type']['job_type_name'] = self.job_type2.name
        self.main_definition['nodes']['node_a']['node_type']['job_type_version'] = self.job_type2.version
        self.main_definition['nodes']['node_a']['node_type']['job_type_revision'] = self.job_type2.revision_num
        self.main_definition['nodes']['node_b']['node_type']['job_type_name'] = self.job_type2.name
        self.main_definition['nodes']['node_b']['node_type']['job_type_version'] = self.job_type2.version
        self.main_definition['nodes']['node_b']['node_type']['job_type_revision'] = self.job_type2.revision_num
        self.main_definition['nodes']['node_c']['node_type']['recipe_type_name'] = self.recipe_type1.name
        self.main_definition['nodes']['node_c']['node_type']['recipe_type_revision'] = self.recipe_type1.revision_num

        self.recipe_type2 = recipe_test_utils.create_recipe_type_v6(name='test.period', definition=self.main_definition)

    def test_not_found(self):
        """Tests calling the recipe type details view with a name that does not exist."""

        url = '/%s/recipe-types/unknown/' % self.api
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

    def test_successful(self):
        """Tests successfully calling the recipe type details view."""

        url = '/%s/recipe-types/%s/' % (self.api, self.recipe_type2.name)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertTrue(isinstance(result, dict), 'result must be a dictionary')
        self.assertEqual(result['id'], self.recipe_type2.id)
        self.assertEqual(result['name'], self.recipe_type2.name)
        self.assertIsNotNone(result['definition'])
        self.assertEqual(len(result['job_types']), 1)
        for entry in result['job_types']:
            self.assertTrue(entry['id'], [self.job_type2.id])

        self.assertEqual(len(result['sub_recipe_types']), 1)
        for entry in result['sub_recipe_types']:
            self.assertTrue(entry['id'], [self.recipe_type1.id])

        self.assertIn('deprecated', result)

        versionless = copy.deepcopy(self.main_definition)
        del versionless['version']
        self.assertDictEqual(result['definition'], versionless)

    def test_edit_simple(self):
        """Tests editing only the basic attributes of a recipe type"""

        json_data = {
            'title': 'Title EDIT',
            'description': 'Description EDIT',
        }

        url = '/%s/recipe-types/%s/' % (self.api, self.recipe_type1.name)
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response.content)

    def test_edit_definition(self):
        """Tests editing the definition of a recipe type"""
        definition = self.sub_definition.copy()
        definition['input']['json'] = [{'name': 'bar', 'type': 'string', 'required': False}]

        json_data = {
            'definition': definition,
        }

        url = '/%s/recipe-types/%s/' % (self.api, self.recipe_type1.name)
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response.content)

        recipe_type = RecipeType.objects.get(pk=self.recipe_type1.id)
        self.assertEqual(recipe_type.revision_num, 2)
        result_def = recipe_type.get_v6_definition_json()
        self.assertEqual(result_def['input']['json'][0]['name'], 'bar')

    @patch('recipe.models.CommandMessageManager')
    @patch('recipe.messages.update_recipe_definition.create_sub_update_recipe_definition_message')
    def test_edit_definition_and_update(self, mock_create, mock_msg_mgr):
        """Tests editing the definition of a recipe type and updating recipes"""
        definition = self.sub_definition.copy()
        definition['input']['json'] = [{'name': 'bar', 'type': 'string', 'required': False}]
        definition['nodes']['node_a']['node_type']['job_type_name'] = self.job_type3.name
        definition['nodes']['node_a']['node_type']['job_type_version'] = self.job_type3.version

        json_data = {
            'definition': definition,
            'auto_update': True
        }

        url = '/%s/recipe-types/%s/' % (self.api, self.recipe_type1.name)
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response.content)

        recipe_type = RecipeType.objects.get(pk=self.recipe_type1.id)
        self.assertEqual(recipe_type.revision_num, 2)
        result_def = recipe_type.get_v6_definition_json()
        self.assertEqual(result_def['input']['json'][0]['name'], 'bar')

        # Check that create_sub_update_recipe_definition_message message was created and sent
        recipe_type = RecipeType.objects.get(pk=self.recipe_type1.id)
        mock_create.assert_called_with(self.recipe_type2.id, recipe_type.id)

        jobs = RecipeTypeJobLink.objects.get_job_type_ids([recipe_type.id])
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0], self.job_type3.id)

        back_links = RecipeTypeJobLink.objects.get_recipe_type_ids(jobs)
        self.assertEqual(len(back_links), 1)
        self.assertEqual(back_links[0], recipe_type.id)

    def test_edit_bad_definition(self):
        """Tests attempting to edit a recipe type using an invalid recipe definition"""
        definition = self.sub_definition.copy()
        definition['version'] = 'BAD'

        json_data = {
            'definition': definition,
        }

        url = '/%s/recipe-types/%s/' % (self.api, self.recipe_type1.name)
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)


class TestRecipeTypeRevisionsViewV6(APITransactionTestCase):
    """Tests related to the recipe-types base endpoint"""

    api = 'v6'

    def setUp(self):
        django.setup()

        rest.login_client(self.client, is_staff=True)

        self.job_type1 = job_test_utils.create_seed_job_type(manifest=job_test_utils.MINIMUM_MANIFEST)
        self.job_type2 = job_test_utils.create_seed_job_type()

        self.sub_definition = copy.deepcopy(recipe_test_utils.SUB_RECIPE_DEFINITION)
        self.sub_definition['nodes']['node_a']['node_type']['job_type_name'] = self.job_type1.name
        self.sub_definition['nodes']['node_a']['node_type']['job_type_version'] = self.job_type1.version
        self.sub_definition['nodes']['node_a']['node_type']['job_type_revision'] = self.job_type1.revision_num

        self.recipe_type1 = recipe_test_utils.create_recipe_type_v6(definition=self.sub_definition)

        self.main_definition = copy.deepcopy(recipe_test_utils.RECIPE_DEFINITION)
        self.main_definition['nodes']['node_a']['node_type']['job_type_name'] = self.job_type2.name
        self.main_definition['nodes']['node_a']['node_type']['job_type_version'] = self.job_type2.version
        self.main_definition['nodes']['node_a']['node_type']['job_type_revision'] = self.job_type2.revision_num
        self.main_definition['nodes']['node_b']['node_type']['job_type_name'] = self.job_type2.name
        self.main_definition['nodes']['node_b']['node_type']['job_type_version'] = self.job_type2.version
        self.main_definition['nodes']['node_b']['node_type']['job_type_revision'] = self.job_type2.revision_num
        self.main_definition['nodes']['node_c']['node_type']['recipe_type_name'] = self.recipe_type1.name
        self.main_definition['nodes']['node_c']['node_type']['recipe_type_revision'] = self.recipe_type1.revision_num

        self.recipe_type2 = recipe_test_utils.create_recipe_type_v6(definition=self.main_definition)

    def test_list_all(self):
        """Tests getting a list of recipe types."""

        url = '/%s/recipe-types/%s/revisions/' % (self.api, self.recipe_type1.name)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertTrue(isinstance(results, dict))
        self.assertEqual(len(results['results']), 1)

        self.assertEqual(results['results'][0]['recipe_type']['id'], self.recipe_type1.id)
        self.assertEqual(results['results'][0]['recipe_type']['name'], self.recipe_type1.name)
        self.assertEqual(results['results'][0]['revision_num'], self.recipe_type1.revision_num)


class TestRecipeTypeRevisionDetailsViewV6(APITransactionTestCase):
    """Tests related to the recipe-types details endpoint"""

    api = 'v6'

    def setUp(self):
        django.setup()

        rest.login_client(self.client, is_staff=True)

        self.job_type1 = job_test_utils.create_seed_job_type(manifest=job_test_utils.MINIMUM_MANIFEST)
        self.job_type2 = job_test_utils.create_seed_job_type()

        self.workspace = storage_test_utils.create_workspace()

        self.sub_definition = copy.deepcopy(recipe_test_utils.SUB_RECIPE_DEFINITION)
        self.sub_definition['nodes']['node_a']['node_type']['job_type_name'] = self.job_type1.name
        self.sub_definition['nodes']['node_a']['node_type']['job_type_version'] = self.job_type1.version
        self.sub_definition['nodes']['node_a']['node_type']['job_type_revision'] = self.job_type1.revision_num

        self.recipe_type1 = recipe_test_utils.create_recipe_type_v6(definition=self.sub_definition)

        self.main_definition = copy.deepcopy(recipe_test_utils.RECIPE_DEFINITION)
        self.main_definition['nodes']['node_a']['node_type']['job_type_name'] = self.job_type2.name
        self.main_definition['nodes']['node_a']['node_type']['job_type_version'] = self.job_type2.version
        self.main_definition['nodes']['node_a']['node_type']['job_type_revision'] = self.job_type2.revision_num
        self.main_definition['nodes']['node_b']['node_type']['job_type_name'] = self.job_type2.name
        self.main_definition['nodes']['node_b']['node_type']['job_type_version'] = self.job_type2.version
        self.main_definition['nodes']['node_b']['node_type']['job_type_revision'] = self.job_type2.revision_num
        self.main_definition['nodes']['node_c']['node_type']['recipe_type_name'] = self.recipe_type1.name
        self.main_definition['nodes']['node_c']['node_type']['recipe_type_revision'] = self.recipe_type1.revision_num

        self.recipe_type2 = recipe_test_utils.create_recipe_type_v6(definition=self.main_definition)

    def test_not_found(self):
        """Tests calling the recipe type revision details view with a revision that does not exist."""

        url = '/%s/recipe-types/%s/revisions/9999/' % (self.api, self.recipe_type1.name)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

    def test_successful(self):
        """Tests successfully calling the recipe type details view."""

        url = '/%s/recipe-types/%s/revisions/%d/' % (self.api, self.recipe_type2.name, self.recipe_type2.revision_num)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertTrue(isinstance(result, dict), 'result must be a dictionary')
        self.assertEqual(result['recipe_type']['id'], self.recipe_type2.id)
        self.assertEqual(result['recipe_type']['name'], self.recipe_type2.name)
        self.assertNotIn('definition', result['recipe_type'])
        self.assertIsNotNone(result['definition'])


class TestRecipeTypesValidationViewV6(APITransactionTestCase):
    """Tests related to the recipe-types validation endpoint"""

    api = 'v6'

    def setUp(self):
        django.setup()

        rest.login_client(self.client)

        self.job_type1 = job_test_utils.create_seed_job_type(manifest=job_test_utils.MINIMUM_MANIFEST)
        self.job_type2 = job_test_utils.create_seed_job_type()
        manifest=copy.deepcopy(job_test_utils.MINIMUM_MANIFEST)
        manifest['job']['name'] = 'minimum-two'
        self.job_type3 = job_test_utils.create_seed_job_type(manifest=manifest)

        self.sub_definition = copy.deepcopy(recipe_test_utils.SUB_RECIPE_DEFINITION)
        self.sub_definition['nodes']['node_a']['node_type']['job_type_name'] = self.job_type1.name
        self.sub_definition['nodes']['node_a']['node_type']['job_type_version'] = self.job_type1.version
        self.sub_definition['nodes']['node_a']['node_type']['job_type_revision'] = self.job_type1.revision_num

        self.recipe_type1 = recipe_test_utils.create_recipe_type_v6(definition=self.sub_definition,
                                                                    name='sub-recipe',
                                                                    title='Sub Recipe',
                                                                    description="A sub recipe",
                                                                    is_active=False,
                                                                    is_system=False)

    def test_successful_new(self):
        """Tests validating a new recipe type."""
        main_definition = copy.deepcopy(recipe_test_utils.RECIPE_DEFINITION)
        main_definition['nodes']['node_a']['node_type']['job_type_name'] = self.job_type2.name
        main_definition['nodes']['node_a']['node_type']['job_type_version'] = self.job_type2.version
        main_definition['nodes']['node_a']['node_type']['job_type_revision'] = self.job_type2.revision_num
        main_definition['nodes']['node_b']['node_type']['job_type_name'] = self.job_type2.name
        main_definition['nodes']['node_b']['node_type']['job_type_version'] = self.job_type2.version
        main_definition['nodes']['node_b']['node_type']['job_type_revision'] = self.job_type2.revision_num
        main_definition['nodes']['node_c']['node_type']['recipe_type_name'] = self.recipe_type1.name
        main_definition['nodes']['node_c']['node_type']['recipe_type_revision'] = self.recipe_type1.revision_num

        json_data = {
            'definition': main_definition
        }

        url = '/%s/recipe-types/validation/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertTrue(results['is_valid'])
        self.assertDictEqual(results, {u'errors': [], u'is_valid': True, u'warnings': [], u'diff': {}})


    def test_successful_update(self):
        """Tests validating an updated recipe type."""
        sub_definition = copy.deepcopy(recipe_test_utils.SUB_RECIPE_DEFINITION)
        sub_definition['nodes']['node_a']['node_type']['job_type_name'] = self.job_type3.name
        sub_definition['nodes']['node_a']['node_type']['job_type_version'] = self.job_type3.version
        sub_definition['nodes']['node_a']['node_type']['job_type_revision'] = self.job_type3.revision_num

        json_data = {
            'name': 'sub-recipe',
            'definition': sub_definition
        }

        url = '/%s/recipe-types/validation/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertTrue(results['is_valid'])
        diff = { u'can_be_reprocessed': True, u'reasons': [],
                 u'nodes': {u'node_a': { u'status': u'CHANGED', u'reprocess_new_node': True, u'force_reprocess': False, u'dependencies': [],
                            u'node_type': { u'job_type_version': u'1.0.0', u'node_type': u'job', u'job_type_name': u'minimum-two',
                                            u'job_type_revision': 1, u'prev_job_type_name': u'my-minimum-job'},
                            u'changes': [{u'name': u'JOB_TYPE_CHANGE', u'description': u'Job type changed from my-minimum-job to minimum-two'}]}}}
        self.assertDictEqual(results, {u'errors': [], u'is_valid': True, u'warnings': [], u'diff': diff})

    def test_bad_param(self):
        """Tests validating a new recipe type with missing fields."""
        json_data = {
            'title': 'Recipe Type Post Test',
        }

        url = '/%s/recipe-types/validation/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_bad_job_type(self):
        """Tests creating a new recipe type with a job type that doesn't exist."""
        sub_definition = copy.deepcopy(recipe_test_utils.SUB_RECIPE_DEFINITION)

        json_data = {
            'definition': sub_definition
        }

        url = '/%s/recipe-types/validation/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertFalse(results['is_valid'])
        errors = [{ u'name': u'JOB_TYPE_DOES_NOT_EXIST',
                    u'description': u'Recipe definition contains a job type that does not exist: ' +
                    'JobType matching query does not exist.'}]
        self.assertDictEqual(results, {u'errors': errors, u'is_valid': False, u'warnings': [], u'diff': {}})

    def test_reprocess_warning(self):
        """Tests validating an updated recipe type with an unable to reprocess warning."""
        new_definition = {'version': '6',
                             'input': {'files': [{'name': 'INPUT_IMAGE', 'media_types': ['image/png'], 'required': True,
                                                  'multiple': False}]},
                             'nodes': {'node_a': {'dependencies': [],
                                                  'input': {'INPUT_IMAGE': {'type': 'recipe', 'input': 'INPUT_IMAGE'}},
                                                  'node_type': {'node_type': 'job', 'job_type_name': self.job_type2.name,
                                                                'job_type_version': self.job_type2.version,
                                                                'job_type_revision': self.job_type2.revision_num}}}}

        json_data = {
            'name': 'sub-recipe',
            'definition': new_definition
        }

        url = '/%s/recipe-types/validation/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertFalse(results['is_valid'])
        diff = {u'can_be_reprocessed': False,
                u'reasons': [{u'name': u'INPUT_CHANGE', u'description': u"Input interface has changed: Parameter 'INPUT_IMAGE' is required"}],
                u'nodes': { u'node_a': { u'status': u'CHANGED', u'reprocess_new_node': False, u'force_reprocess': False, u'dependencies': [],
                                         u'node_type': { u'job_type_revision': self.job_type2.revision_num, u'job_type_name': self.job_type2.name,
                                                         u'job_type_version': self.job_type2.version, u'node_type': u'job', u'prev_job_type_version': u'1.0.0',
                                                         u'prev_job_type_name': u'my-minimum-job' },
                                         u'changes': [{ u'name': u'JOB_TYPE_CHANGE', u'description': u'Job type changed from my-minimum-job to %s' % self.job_type2.name},
                                                      { u'name': u'JOB_TYPE_VERSION_CHANGE', u'description': u'Job type version changed from 1.0.0 to %s' % self.job_type2.version},
                                                      { u'name': u'INPUT_NEW', u'description': u'New input INPUT_IMAGE added'}]}}}

        warnings = [{u'name': u'REPROCESS_WARNING', u'description': u"This recipe cannot be reprocessed after updating."}]
        self.maxDiff = None
        self.assertDictEqual(results, {u'errors': [], u'is_valid': False, u'warnings': warnings, u'diff': diff})

    def test_recipe_not_found_warning(self):
        """Tests validating a recipe definition against a recipe-type that doesn't exist"""
        new_definition = {'version': '6',
                          'input': {'files': [{'name': 'INPUT_IMAGE', 'media_types': ['image/png'], 'required': True,
                                               'multiple': False}]},
                          'nodes': {'node_a': {'dependencies': [],
                                               'input': {'INPUT_IMAGE': {'type': 'recipe', 'input': 'INPUT_IMAGE'}},
                                               'node_type': {'node_type': 'job', 'job_type_name': self.job_type2.name,
                                                             'job_type_version': self.job_type2.version,
                                                             'job_type_revision': self.job_type2.revision_num}}}}

        json_data = {
            'name': 'not-a-name',
            'definition': new_definition
        }

        url = '/%s/recipe-types/validation/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertTrue(results['is_valid'])
        warnings = [{u'name': u'RECIPE_TYPE_NOT_FOUND', u'description': u"Unable to find an existing recipe type with name: not-a-name"}]
        self.assertDictEqual(results, {u'errors': [], u'is_valid': True, u'warnings': warnings, u'diff': {}})


    def test_mismatched_warning(self):
        """Tests validating a new recipe type."""
        main_definition = copy.deepcopy(recipe_test_utils.RECIPE_DEFINITION)
        main_definition['input']['files'][0]['media_types'] = ['image/tiff']
        main_definition['nodes']['node_a']['node_type']['job_type_name'] = self.job_type2.name
        main_definition['nodes']['node_a']['node_type']['job_type_version'] = self.job_type2.version
        main_definition['nodes']['node_a']['node_type']['job_type_revision'] = self.job_type2.revision_num
        main_definition['nodes']['node_b']['node_type']['job_type_name'] = self.job_type2.name
        main_definition['nodes']['node_b']['node_type']['job_type_version'] = self.job_type2.version
        main_definition['nodes']['node_b']['node_type']['job_type_revision'] = self.job_type2.revision_num
        main_definition['nodes']['node_c']['node_type']['recipe_type_name'] = self.recipe_type1.name
        main_definition['nodes']['node_c']['node_type']['recipe_type_revision'] = self.recipe_type1.revision_num

        json_data = {
            'definition': main_definition
        }

        url = '/%s/recipe-types/validation/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertTrue(results['is_valid'])
        warnings = [{u'name': u'MISMATCHED_MEDIA_TYPES', u'description': u"Parameter 'INPUT_IMAGE' might not accept [image/tiff]"}]
        self.assertDictEqual(results, {u'errors': [], u'is_valid': True, u'warnings': warnings, u'diff': {}})


class TestRecipesViewV6(APITransactionTestCase):

    api = 'v6'

    def setUp(self):
        django.setup()

        rest.login_client(self.client, is_staff=True)

        self.date_1 = datetime.datetime(2016, 1, 1, tzinfo=utc)
        self.date_2 = datetime.datetime(2016, 1, 2, tzinfo=utc)
        self.date_3 = datetime.datetime(2016, 1, 2, tzinfo=utc)
        self.date_4 = datetime.datetime(2016, 1, 3, tzinfo=utc)
        self.s_class = 'A'
        self.s_sensor = '1'
        self.collection = '12345'
        self.task = 'abcd'
        self.s_class2 = 'B'
        self.s_sensor2 = '2'
        self.collection2 = '123456'
        self.task2 = 'abcde'

        manifest = copy.deepcopy(job_test_utils.COMPLETE_MANIFEST)
        manifest['job']['name'] = 'scale-batch-creator'

        self.job_type1 = job_test_utils.create_seed_job_type(manifest=manifest)
        self.jt2 = job_test_utils.create_seed_job_type(manifest=job_test_utils.MINIMUM_MANIFEST)

        def_v6_dict_sub = {'version': '6',
                       'input': { 'files': [],
                                  'json': []},
                       'nodes': {'node_a': {'dependencies': [],
                                            'input': {},
                                            'node_type': {'node_type': 'job', 'job_type_name': self.jt2.name,
                                                          'job_type_version': self.jt2.version, 'job_type_revision': self.jt2.revision_num}}}}

        self.sub = recipe_test_utils.create_recipe_type_v6(definition=def_v6_dict_sub)

        def_v6_dict = {'version': '6',
                       'input': {'files': [{'name': 'INPUT_FILE', 'media_types': ['image/tiff'], 'required': True,
                                            'multiple': True}],
                                 'json': [{'name': 'INPUT_JSON', 'type': 'string', 'required': True}]},
                       'nodes': {'node_a': {'dependencies': [],
                                            'input': {'INPUT_FILE': {'type': 'recipe', 'input': 'INPUT_FILE'},
                                                      'INPUT_JSON': {'type': 'recipe', 'input': 'INPUT_JSON'}},
                                            'node_type': {'node_type': 'job', 'job_type_name': self.job_type1.name,
                                                          'job_type_version': self.job_type1.version, 'job_type_revision': 1}},
                                 'node_b': {'dependencies': [],
                                            'input': {},
                                            'node_type': {'node_type': 'recipe', 'recipe_type_name': self.sub.name,
                                                          'recipe_type_revision': self.sub.revision_num}}

                       }

        }

        self.workspace = storage_test_utils.create_workspace()
        self.file1 = storage_test_utils.create_file(workspace=self.workspace, file_size=104857600.0,
                                               source_started=self.date_1, source_ended=self.date_2,
                                               source_sensor_class=self.s_class, source_sensor=self.s_sensor,
                                               source_collection=self.collection, source_task=self.task)

        self.file2 = storage_test_utils.create_file(workspace=self.workspace, file_size=104857600.0,
                                               source_started=self.date_3, source_ended=self.date_4,
                                               source_sensor_class=self.s_class2, source_sensor=self.s_sensor2,
                                               source_collection=self.collection2, source_task=self.task2)

        self.data = {'version': '6', 'files': {'INPUT_FILE': [self.file1.id]},
                'json': {'INPUT_JSON': 'hello'}}

        self.data2 = {'version': '6', 'files': {'INPUT_FILE': [self.file2.id]},
                'json': {'INPUT_JSON': 'hello2'}}

        self.recipe_type = recipe_test_utils.create_recipe_type_v6(name='my-type', definition=def_v6_dict)
        self.recipe1 = recipe_test_utils.create_recipe(recipe_type=self.recipe_type, input=self.data)
        self.recipe_type2 = recipe_test_utils.create_recipe_type_v6(name='my-type2', definition=def_v6_dict)
        self.recipe2 = recipe_test_utils.create_recipe(recipe_type=self.recipe_type2, input=self.data2)
        self.recipe3 = recipe_test_utils.create_recipe(is_superseded=True)

        recipe_test_utils.process_recipe_inputs([self.recipe1.id, self.recipe2.id, self.recipe3.id])

    def test_successful_all(self):
        """Tests getting recipes"""

        url = '/%s/recipes/' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertEqual(results['count'], 5)

        # check new/removed fields
        for result in results['results']:
            if result['id'] == self.recipe1.id:
                self.assertIn('recipe', result)
                self.assertIn('batch', result)
                self.assertEqual(result['input_file_size'], 100.0)
                self.assertEqual(result['source_started'], '2016-01-01T00:00:00Z')
                self.assertEqual(result['source_ended'], '2016-01-02T00:00:00Z')
                self.assertEqual(result['source_sensor_class'], self.s_class)
                self.assertEqual(result['source_sensor'], self.s_sensor)
                self.assertEqual(result['source_collection'], self.collection)
                self.assertEqual(result['source_task'], self.task)
                self.assertEqual(result['jobs_total'], 2)
                self.assertEqual(result['jobs_pending'], 0)
                self.assertEqual(result['jobs_blocked'], 0)
                self.assertEqual(result['jobs_queued'], 2)
                self.assertEqual(result['jobs_running'], 0)
                self.assertEqual(result['jobs_failed'], 0)
                self.assertEqual(result['jobs_completed'], 0)
                self.assertEqual(result['jobs_canceled'], 0)
                self.assertEqual(result['sub_recipes_total'], 1)
                self.assertEqual(result['sub_recipes_completed'], 0)
                self.assertFalse(result['is_completed'])
                self.assertNotIn('root_superseded_recipe', result)
                self.assertNotIn('superseded_by_recipe', result)
            else:
                id = result['id']
                if result['recipe']:
                    id = result['recipe']['id']
                    self.assertTrue(id in [self.recipe1.id, self.recipe2.id])
                else:
                    self.assertTrue(id in [self.recipe2.id, self.recipe3.id])

    def test_time_successful(self):
        """Tests successfully calling the get recipes by time"""
        yesterday = timezone.now().date() - timezone.timedelta(days=1)
        yesterday = yesterday.isoformat() + 'T00:00:00Z'
        today = timezone.now().date()
        today = today.isoformat() + 'T00:00:00Z'
        tomorrow = timezone.now().date() + timezone.timedelta(days=1)
        tomorrow = tomorrow.isoformat() + 'T00:00:00Z'

        url = '/%s/recipes/?started=%s&ended=%s' % (self.api, today, tomorrow)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        result = json.loads(response.content)
        results = result['results']
        self.assertEqual(len(results), 5)

        url = '/%s/recipes/?started=%s&ended=%s' % (self.api, yesterday, today)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        result = json.loads(response.content)
        results = result['results']
        self.assertEqual(len(results), 0)

    def test_source_time_successful(self):
        """Tests successfully calling the get recipes by source time"""
        url = '/%s/recipes/?source_started=%s&source_ended=%s' % (self.api,
                                                               '2016-01-01T00:00:00Z',
                                                               '2016-01-02T00:00:00Z')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        result = json.loads(response.content)
        results = result['results']
        self.assertEqual(len(results), 1)
        for result in results:
            self.assertTrue(result['id'] in [self.recipe1.id])

    def test_source_sensor_class(self):
        """Tests successfully calling the recipes view filtered by source sensor class."""
        url = '/%s/recipes/?source_sensor_class=%s' % (self.api, self.s_class)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['source_sensor_class'], self.s_class)

    def test_source_sensor(self):
        """Tests successfully calling the recipes view filtered by source sensor."""
        url = '/%s/recipes/?source_sensor=%s' % (self.api, self.s_sensor)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['source_sensor'], self.s_sensor)

    def test_source_collection(self):
        """Tests successfully calling the recipes view filtered by source collection."""
        url = '/%s/recipes/?source_collection=%s' % (self.api, self.collection)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['source_collection'], self.collection)

    def test_source_task(self):
        """Tests successfully calling the recipes view filtered by source task."""
        url = '/%s/recipes/?source_task=%s' % (self.api, self.task)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['source_task'], self.task)

    def test_successful_id(self):
        """Tests getting recipes by id"""

        url = '/%s/recipes/?recipe_id=%s' % (self.api, self.recipe1.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertEqual(results['count'], 1)
        self.assertEqual(results['results'][0]['id'], self.recipe1.id)

    def test_successful_recipe_type_id(self):
        """Tests getting recipes by type id"""

        url = '/%s/recipes/?recipe_type_id=%s' % (self.api, self.recipe_type.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertEqual(results['count'], 1)
        self.assertEqual(results['results'][0]['recipe_type']['id'], self.recipe_type.id)

    def test_successful_recipe_type_name(self):
        """Tests getting recipes by type name"""

        url = '/%s/recipes/?recipe_type_name=my-type' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertEqual(results['count'], 1)
        self.assertEqual(results['results'][0]['recipe_type']['name'], 'my-type')

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

    def test_successful_superseded(self):
        """Tests getting superseded recipes"""

        url = '/%s/recipes/?is_superseded=true' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertEqual(results['count'], 1)

        url = '/%s/recipes/?is_superseded=false' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertEqual(results['count'], 4)

    def test_successful_completed(self):
        """Tests getting completed recipes"""

        url = '/%s/recipes/?is_completed=true' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertEqual(results['count'], 0)

        url = '/%s/recipes/?is_completed=false' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertEqual(results['count'], 5)

    def test_successful_order(self):
        """Tests ordering recipes"""

        url = '/%s/recipes/?order=-source_sensor_class' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertEqual(results['results'][4]['source_sensor_class'], 'A')


class TestRecipesPostViewV6(APITransactionTestCase):
    api = 'v6'

    def setUp(self):
            django.setup()

            rest.login_client(self.client, is_staff=True)

            self.workspace = storage_test_utils.create_workspace()
            self.source_file = source_test_utils.create_source(workspace=self.workspace)

            self.jt1 = job_test_utils.create_seed_job_type()

            self.jt2 = job_test_utils.create_seed_job_type()

            self.def_v6_dict = {'version': '6',
                                'input': {
                                    'files': [{'name': 'INPUT_IMAGE', 'media_types': ['image/tiff'], 'required': True,
                                               'multiple': True}],
                                    'json': []},
                                'nodes': {'node_a': {'dependencies': [],
                                                     'input': {'INPUT_IMAGE': {'type': 'recipe', 'input': 'INPUT_IMAGE'}},
                                                     'node_type': {'node_type': 'job', 'job_type_name': self.jt1.name,
                                                                   'job_type_version': self.jt1.version,
                                                                   'job_type_revision': 1}},
                                          'node_b': {'dependencies': [{'name': 'node_a'}],
                                                     'input': {'INPUT_IMAGE': {'type': 'dependency', 'node': 'node_a',
                                                                           'output': 'OUTPUT_IMAGE'}},
                                                     'node_type': {'node_type': 'job', 'job_type_name': self.jt2.name,
                                                                   'job_type_version': self.jt2.version,
                                                                   'job_type_revision': 1}}
                                          }

                                }

            self.recipe_type = recipe_test_utils.create_recipe_type_v6(definition=self.def_v6_dict)

    @patch('queue.models.CommandMessageManager')
    @patch('queue.models.create_process_recipe_input_messages')
    def test_successful_v1data(self, mock_create, mock_msg_mgr):

        data_dict = {
            'version': '1.0',
            'input_data': [{
                'name': 'INPUT_IMAGE',
                'file_id': self.source_file.id,
            }],
            'output_data': [{
                'name': 'output_a',
                'workspace_id': self.workspace.id
            }]
        }

        json_data = {
            "input" : data_dict,
            "recipe_type_id" : self.recipe_type.pk
        }

        url = '/%s/recipes/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        #Response should be new v6 recipe detail response
        result = json.loads(response.content)
        self.assertTrue('data' not in result)
        self.assertTrue('/%s/recipes/' % self.api in response['location'])

        mock_create.assert_called_once()

    @patch('queue.models.CommandMessageManager')
    @patch('queue.models.create_process_recipe_input_messages')
    def test_successful_v6data(self, mock_create, mock_msg_mgr):

        data = {'version': '6', 'files': {'INPUT_IMAGE': [self.source_file.id]}, 'json': {}}
        json_data = {
            "input": data,
            "recipe_type_id": self.recipe_type.pk
        }

        url = '/%s/recipes/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        # Response should be new v6 recipe detail response
        result = json.loads(response.content)
        self.assertTrue('data' not in result)
        self.assertTrue('/%s/recipes/' % self.api in response['location'])

        mock_create.assert_called_once()

    @patch('queue.models.CommandMessageManager')
    @patch('queue.models.create_process_recipe_input_messages')
    def test_successful_config(self, mock_create, mock_msg_mgr):

        data = {'version': '6', 'files': {'INPUT_IMAGE': [self.source_file.id]}, 'json': {}}
        config = {'version': '6', 'output_workspaces': {'default': self.workspace.name}}
        json_data = {
            "input": data,
            "recipe_type_id": self.recipe_type.pk,
            "configuration": config
        }

        url = '/%s/recipes/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        # Response should be new v6 recipe detail response
        result = json.loads(response.content)
        self.assertTrue('data' not in result)
        self.assertTrue('/%s/recipes/' % self.api in response['location'])

        mock_create.assert_called_once()

    def test_bad_data(self):

        data = {'version': 'bad', 'files': {'INPUT_IMAGE': [self.source_file.id]}, 'json': {}}
        json_data = {
            "input": data,
            "recipe_type_id": self.recipe_type.pk
        }

        url = '/%s/recipes/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_bad_config(self):

        data = {'version': '6', 'files': {'INPUT_IMAGE': [self.source_file.id]}, 'json': {}}
        config = {'version': 'bad'}
        json_data = {
            "input": data,
            "recipe_type_id": self.recipe_type.pk,
            "configuration": config
        }

        url = '/%s/recipes/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)


class TestRecipeDetailsViewV6(APITransactionTestCase):

    api = 'v6'

    def setUp(self):
        django.setup()

        rest.login_client(self.client, is_staff=True)

        self.date_1 = datetime.datetime(2016, 1, 1, tzinfo=utc)
        self.date_2 = datetime.datetime(2016, 1, 2, tzinfo=utc)
        self.date_3 = datetime.datetime(2016, 1, 2, tzinfo=utc)
        self.date_4 = datetime.datetime(2016, 1, 3, tzinfo=utc)
        self.s_class = 'A'
        self.s_sensor = '1'
        self.collection = '12345'
        self.task = 'abcd'

        manifest = copy.deepcopy(job_test_utils.COMPLETE_MANIFEST)
        manifest['job']['name'] = 'scale-batch-creator'

        self.jt1 = job_test_utils.create_seed_job_type(manifest=manifest)
        self.jt2 = job_test_utils.create_seed_job_type(manifest=job_test_utils.MINIMUM_MANIFEST)

        def_v6_dict_sub = {'version': '6',
                       'input': { 'files': [],
                                  'json': []},
                       'nodes': {'node_a': {'dependencies': [],
                                            'input': {},
                                            'node_type': {'node_type': 'job', 'job_type_name': self.jt2.name,
                                                          'job_type_version': self.jt2.version, 'job_type_revision': self.jt2.revision_num}}}}

        self.sub = recipe_test_utils.create_recipe_type_v6(definition=def_v6_dict_sub)

        self.def_v6_dict = {'version': '6',
                       'input': {'files': [{'name': 'INPUT_FILE', 'media_types': ['image/tiff'], 'required': True,
                                            'multiple': True}],
                                 'json': [{'name': 'INPUT_JSON', 'type': 'string', 'required': True}]},
                       'nodes': {'node_a': {'dependencies': [],
                                            'input': {'INPUT_FILE': {'type': 'recipe', 'input': 'INPUT_FILE'},
                                                      'INPUT_JSON': {'type': 'recipe', 'input': 'INPUT_JSON'}},
                                            'node_type': {'node_type': 'job', 'job_type_name': self.jt1.name,
                                                          'job_type_version': self.jt1.version,
                                                          'job_type_revision': 1}},
                                 'node_b': {'dependencies': [],
                                            'input': {},
                                            'node_type': {'node_type': 'recipe', 'recipe_type_name': self.sub.name,
                                                          'recipe_type_revision': self.sub.revision_num}}
                                 }

                       }

        self.workspace = storage_test_utils.create_workspace()
        self.file1 = storage_test_utils.create_file(workspace=self.workspace, file_size=104857600.0,
                                                    source_started=self.date_1, source_ended=self.date_2,
                                                    source_sensor_class=self.s_class, source_sensor=self.s_sensor,
                                                    source_collection=self.collection, source_task=self.task)


        self.data = {'version': '6', 'files': {'INPUT_FILE': [self.file1.id]},
                'json': {'INPUT_JSON': 'hello'}}

        self.recipe_type = recipe_test_utils.create_recipe_type_v6(name='my-type', definition=self.def_v6_dict)
        self.recipe1 = recipe_test_utils.create_recipe(recipe_type=self.recipe_type, input=self.data)

        recipe_test_utils.process_recipe_inputs([self.recipe1.id])

    def test_successful(self):
        """Tests getting recipe details"""

        url = '/%s/recipes/%i/' % (self.api, self.recipe1.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(result['id'], self.recipe1.id)
        self.assertEqual(result['recipe_type']['id'], self.recipe1.recipe_type.id)
        self.assertEqual(result['recipe_type_rev']['recipe_type']['id'], self.recipe1.recipe_type.id)

        self.assertEqual(result['source_sensor_class'], self.s_class)
        self.assertEqual(result['source_sensor'], self.s_sensor)
        self.assertEqual(result['source_collection'], self.collection)
        self.assertEqual(result['source_task'], self.task)

        self.assertTrue('inputs' not in result)
        self.assertTrue('definiton' not in result['recipe_type'])
        self.maxDiff = None
        self.assertEqual(result['input'], {u'files': {u'INPUT_FILE': [self.file1.id]}, u'json': {u'INPUT_JSON': u'hello'}})
        job_id = result['details']['nodes']['node_a']['node_type']['job_id']
        recipe_id = result['details']['nodes']['node_b']['node_type']['recipe_id']
        details_dict = {u'nodes':
              {u'node_a': {u'dependencies': [],
                          u'node_type': {u'job_id': job_id,
                                         u'job_type_name': u'scale-batch-creator',
                                         u'job_type_revision': 1,
                                         u'job_type_version': u'1.0.0',
                                         u'node_type': u'job',
                                         u'status': u'QUEUED'}},
               u'node_b': {u'dependencies': [],
                          u'node_type': {u'is_completed': False,
                                         u'jobs_blocked': 0,
                                         u'jobs_canceled': 0,
                                         u'jobs_completed': 0,
                                         u'jobs_failed': 0,
                                         u'jobs_pending': 0,
                                         u'jobs_queued': 1,
                                         u'jobs_running': 0,
                                         u'jobs_total': 1,
                                         u'node_type': u'recipe',
                                         u'recipe_id': recipe_id,
                                         u'recipe_type_name': self.sub.name,
                                         u'recipe_type_revision': 1,
                                         u'sub_recipes_completed': 0,
                                         u'sub_recipes_total': 0}}}}
        self.assertEqual(result['details'], details_dict)

        self.assertEqual(result['job_types'][0]['id'], self.jt1.id)
        self.assertEqual(result['sub_recipe_types'][0]['id'], self.sub.id)

    def test_superseded(self):
        """Tests successfully calling the recipe details view for superseded recipes."""

        new_recipe = recipe_test_utils.create_recipe(recipe_type=self.recipe_type, input=self.data,
                                                       superseded_recipe=self.recipe1)

        self.recipe1.is_superseded=True
        self.recipe1.superseded = timezone.now()
        self.recipe1.save()

        url = '/%s/recipes/%i/' % (self.api,  self.recipe1.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertTrue(result['is_superseded'])
        self.assertIsNotNone(result['superseded_by_recipe'])
        self.assertEqual(result['superseded_by_recipe']['id'], new_recipe.id)
        self.assertIsNotNone(result['superseded'])

        url = '/%s/recipes/%i/' % (self.api,  new_recipe.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertFalse(result['is_superseded'])
        self.assertIsNotNone(result['superseded_recipe'])
        self.assertEqual(result['superseded_recipe']['id'], self.recipe1.id)
        self.assertIsNone(result['superseded'])

    def test_not_found(self):
        """Tests calling the recipe details view with an id that does not exist."""

        url = '/%s/recipes/9999/' % self.api
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)


class TestRecipeReprocessViewV6(APITransactionTestCase):

    api = 'v6'

    def setUp(self):
        django.setup()

        rest.login_client(self.client, is_staff=True)

        self.date_1 = datetime.datetime(2016, 1, 1, tzinfo=utc)
        self.date_2 = datetime.datetime(2016, 1, 2, tzinfo=utc)
        self.s_class = 'A'
        self.s_sensor = '1'
        self.collection = '12345'
        self.task = 'abcd'

        manifest = copy.deepcopy(job_test_utils.COMPLETE_MANIFEST)
        manifest['job']['name'] = 'scale-batch-creator'

        self.job_type1 = job_test_utils.create_seed_job_type(manifest=manifest)
        self.jt2 = job_test_utils.create_seed_job_type(manifest=job_test_utils.MINIMUM_MANIFEST)

        def_v6_dict_sub = {'version': '6',
                       'input': { 'files': [],
                                  'json': []},
                       'nodes': {'node_a': {'dependencies': [],
                                            'input': {},
                                            'node_type': {'node_type': 'job', 'job_type_name': self.jt2.name,
                                                          'job_type_version': self.jt2.version, 'job_type_revision': self.jt2.revision_num}}}}

        self.sub = recipe_test_utils.create_recipe_type_v6(definition=def_v6_dict_sub)

        def_v6_dict = {'version': '6',
                       'input': {'files': [{'name': 'INPUT_FILE', 'media_types': ['image/tiff'], 'required': True,
                                            'multiple': True}],
                                 'json': [{'name': 'INPUT_JSON', 'type': 'string', 'required': True}]},
                       'nodes': {'node_a': {'dependencies': [],
                                            'input': {'INPUT_FILE': {'type': 'recipe', 'input': 'INPUT_FILE'},
                                                      'INPUT_JSON': {'type': 'recipe', 'input': 'INPUT_JSON'}},
                                            'node_type': {'node_type': 'job', 'job_type_name': self.job_type1.name,
                                                          'job_type_version': self.job_type1.version, 'job_type_revision': 1}},
                                 'node_b': {'dependencies': [],
                                            'input': {},
                                            'node_type': {'node_type': 'recipe', 'recipe_type_name': self.sub.name,
                                                          'recipe_type_revision': self.sub.revision_num}}

                       }

        }

        self.workspace = storage_test_utils.create_workspace()
        self.file1 = storage_test_utils.create_file(workspace=self.workspace, file_size=104857600.0,
                                               source_started=self.date_1, source_ended=self.date_2,
                                               source_sensor_class=self.s_class, source_sensor=self.s_sensor,
                                               source_collection=self.collection, source_task=self.task)


        self.data = {'version': '6', 'files': {'INPUT_FILE': [self.file1.id]},
                'json': {'INPUT_JSON': 'hello'}}

        self.config = {'version': '6', 'mounts': {'mount_1': {'type': 'host', 'host_path': '/the/host/path'},
                                                  'mount_2': {'type': 'volume', 'driver': 'driver',
                                                              'driver_opts': {'opt_1': 'foo', 'opt_2': 'bar'}}},
                       'output_workspaces': {'default': self.workspace.name, 'outputs': {'output': self.workspace.name}},
                       'priority': 999, 'settings': {'setting_1': '1234', 'setting_2': '5678'}}

        self.recipe_type = recipe_test_utils.create_recipe_type_v6(name='my-type', definition=def_v6_dict)
        self.recipe1 = recipe_test_utils.create_recipe(recipe_type=self.recipe_type, input=self.data, config=self.config)
        recipe_test_utils.process_recipe_inputs([self.recipe1.id])

    @patch('recipe.views.CommandMessageManager')
    def test_all_jobs(self, mock_mgr):
        """Tests reprocessing all jobs in an existing recipe"""

        mock_mgr.return_value = MockCommandMessageManager()

        json_data = {
            'forced_nodes': {
                'all': True
            }
        }

        url = '/%s/recipes/%i/reprocess/' % (self.api, self.recipe1.id)
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED, response.content)

        new_recipe = Recipe.objects.get(superseded_recipe_id=self.recipe1.id)
        self.assertEqual(new_recipe.configuration['output_workspaces']['default'], self.workspace.name)

    @patch('recipe.views.CommandMessageManager')
    @patch('recipe.views.create_reprocess_messages')
    def test_job(self, mock_create, mock_msg_mgr):
        """Tests reprocessing one job in an existing recipe"""

        json_data = {
            'forced_nodes': {
                'all': False,
                'nodes': ['node_a']
            }
        }

        url = '/%s/recipes/%i/reprocess/' % (self.api, self.recipe1.id)
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED, response.content)

        mock_create.assert_called()

    @patch('recipe.views.CommandMessageManager')
    @patch('recipe.views.create_reprocess_messages')
    def test_full_recipe(self, mock_create, mock_msg_mgr):
        """Tests reprocessing a full recipe"""

        json_data = {
            'forced_nodes': {
                'all': False,
                'nodes': ['node_a', 'node_b'],
                'sub_recipes': {
                    'node_b': {
                        'all': False,
                        'nodes': ['node_a']}
                }
            }
        }

        url = '/%s/recipes/%i/reprocess/' % (self.api, self.recipe1.id)
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED, response.content)

        mock_create.assert_called()

    def test_bad_job(self):
        """Tests reprocessing a non-existant job throws an error"""

        json_data = {
            'forced_nodes': {
                'all': False,
                'nodes': ['does-not-exist']
            }
        }

        url = '/%s/recipes/%i/reprocess/' % (self.api, self.recipe1.id)
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_bad_recipe(self):
        """Tests reprocessing a non-existant job throws an error"""

        json_data = {
            'forced_nodes': {
                'all': False,
                'nodes': ['node_a'],
                'sub_recipes': {
                    'node_a': {
                        'all': False,
                        'nodes': ['node_a']}
                }
            }
        }

        url = '/%s/recipes/%i/reprocess/' % (self.api, self.recipe1.id)
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_bad_json(self):
        """Tests reprocessing with bad forced_nodes json input"""

        json_data = {
            'forced_nodes': {
                'invalid': 'missing "all" field'
            }
        }

        url = '/%s/recipes/%i/reprocess/' % (self.api, self.recipe1.id)
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_superseded(self):
        """Tests reprocessing a recipe that is already superseded throws an error."""

        self.recipe1.is_superseded = True
        self.recipe1.save()

        json_data = {
            'forced_nodes': {
                'all': True
            }
        }

        url = '/%s/recipes/%i/reprocess/' % (self.api, self.recipe1.id)
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    @patch('recipe.models.CommandMessageManager')
    def test_updated_recipe(self, mock_mgr):
        """Tests reprocessing a recipe that has been updated"""
    
        mock_mgr.return_value = MockCommandMessageManager()
        
        # Test old revision number
        json_data = {
            
            'forced_nodes': {
                'all': True
            },
            'revision_num': 1
        }
        
        url = '/%s/recipes/%i/reprocess/' % (self.api, self.recipe1.id)
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED, response.content)
        
    def test_bad_revision_num(self):
        """Tests reprocessing a recipe with an invalid revision number"""
        
        json_data = {
            'forced_nodes': {
                'all': True
            },
            'revision_num': 3
        }
        
        url = '/%s/recipes/%i/reprocess/' % (self.api, self.recipe1.id)
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

class TestRecipeInputFilesViewV6(APITestCase):

    api = 'v6'

    def setUp(self):

        rest.login_client(self.client, is_staff=True)

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

        self.job_type1 = job_test_utils.create_seed_job_type()

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

        manifest = copy.deepcopy(job_test_utils.COMPLETE_MANIFEST)
        manifest['job']['name'] = 'scale-batch-creator'

        self.jt1 = job_test_utils.create_seed_job_type(manifest=manifest)
        self.jt2 = job_test_utils.create_seed_job_type(manifest=job_test_utils.MINIMUM_MANIFEST)

        def_v6_dict_sub = {'version': '6',
                       'input': { 'files': [],
                                  'json': []},
                       'nodes': {'node_a': {'dependencies': [],
                                            'input': {},
                                            'node_type': {'node_type': 'job', 'job_type_name': self.jt2.name,
                                                          'job_type_version': self.jt2.version, 'job_type_revision': self.jt2.revision_num}}}}

        self.sub = recipe_test_utils.create_recipe_type_v6(definition=def_v6_dict_sub)

        self.def_v6_dict = {'version': '6',
                       'input': {'files': [{'name': 'INPUT_FILE', 'media_types': ['image/tiff'], 'required': True,
                                            'multiple': True}],
                                 'json': [{'name': 'INPUT_JSON', 'type': 'string', 'required': True}]},
                       'nodes': {'node_a': {'dependencies': [],
                                            'input': {'INPUT_FILE': {'type': 'recipe', 'input': 'INPUT_FILE'},
                                                      'INPUT_JSON': {'type': 'recipe', 'input': 'INPUT_JSON'}},
                                            'node_type': {'node_type': 'job', 'job_type_name': self.jt1.name,
                                                          'job_type_version': self.jt1.version,
                                                          'job_type_revision': 1}},
                                 'node_b': {'dependencies': [],
                                            'input': {},
                                            'node_type': {'node_type': 'recipe', 'recipe_type_name': self.sub.name,
                                                          'recipe_type_revision': self.sub.revision_num}}
                                 }

                       }

        self.recipe_type = recipe_test_utils.create_recipe_type_v6(name='my-type', definition=self.def_v6_dict)
        self.recipe1 = recipe_test_utils.create_recipe(recipe_type=self.recipe_type)

        # Create RecipeInputFile entry files
        self.f3_file_name = 'foo.bar'
        self.f3_last_modified = datetime.datetime(2016, 1, 11, tzinfo=utc)
        self.f3_source_started = datetime.datetime(2016, 1, 10, tzinfo=utc)
        self.f3_source_ended = datetime.datetime(2016, 1, 11, tzinfo=utc)
        self.file3 = recipe_test_utils.create_input_file(file_name=self.f3_file_name,
                                                         source_started=self.f3_source_started,
                                                         source_ended=self.f3_source_ended, recipe=self.recipe1,
                                                         last_modified=self.f3_last_modified)

        self.f4_file_name = 'qaz.bar'
        self.f4_recipe_input = 'INPUT_FILE'
        self.f4_last_modified = datetime.datetime(2016, 1, 12, tzinfo=utc)
        self.f4_source_started = datetime.datetime(2016, 1, 11, tzinfo=utc)
        self.f4_source_ended = datetime.datetime(2016, 1, 12, tzinfo=utc)
        self.file4 = recipe_test_utils.create_input_file(file_name=self.f4_file_name,
                                                         source_started=self.f4_source_started,
                                                         source_ended=self.f4_source_ended, recipe=self.recipe1,
                                                         last_modified=self.f4_last_modified,
                                                         recipe_input=self.f4_recipe_input)

    def test_successful_file(self):
        """Tests successfully calling the recipe input files view"""

        url = '/%s/recipes/%i/input_files/' % (self.api, self.recipe1.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        results = result['results']
        self.assertEqual(len(results), 2)
        for result in results:
            self.assertTrue(result['id'] in [self.file3.id, self.file4.id])
            self.assertIn('file_name', result)
            self.assertIn('workspace', result)
            self.assertIn('media_type', result)
            self.assertIn('file_type', result)
            self.assertIn('file_size', result)
            self.assertIn('file_path', result)
            self.assertIn('is_deleted', result)
            self.assertIn('url', result)
            self.assertIn('created', result)
            self.assertIn('deleted', result)
            self.assertIn('data_started', result)
            self.assertIn('data_ended', result)
            self.assertIn('source_started', result)
            self.assertIn('source_ended', result)
            self.assertIn('last_modified', result)
            self.assertIn('geometry', result)
            self.assertIn('center_point', result)
            self.assertIn('countries', result)
            self.assertIn('job_type', result)
            self.assertIn('job', result)
            self.assertIn('job_exe', result)
            self.assertIn('job_output', result)
            self.assertIn('recipe_type', result)
            self.assertIn('recipe', result)
            self.assertIn('recipe_node', result)
            self.assertIn('batch', result)
            self.assertFalse(result['is_superseded'])
            self.assertIn('superseded', result)


    def test_filter_recipe_input(self):
        """Tests successfully calling the recipe input files view with recipe_input string filtering"""

        url = '/%s/recipes/%i/input_files/?recipe_input=%s' % (self.api, self.recipe1.id, self.f4_recipe_input)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        results = result['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], self.file4.id)

    def test_file_name_successful(self):
        """Tests successfully calling the get files by name view"""

        url = '/%s/recipes/%i/input_files/?file_name=%s' % (self.api, self.recipe1.id, self.f3_file_name)
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

        url = '/%s/recipes/%i/input_files/?file_name=%s' % (self.api, self.recipe1.id, 'not_a.file')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        result = results['results']
        self.assertEqual(len(result), 0)

    def test_time_successful(self):
        """Tests successfully calling the get recipe input files view by time"""

        url = '/%s/recipes/%i/input_files/?started=%s&ended=%s&time_field=%s' % (self.api, self.recipe1.id,
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
