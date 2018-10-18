from __future__ import unicode_literals

import datetime

import django
from django.db import transaction
from django.test import TransactionTestCase
from django.utils.timezone import now
from mock import patch

import job.test.utils as job_test_utils
import recipe.test.utils as recipe_test_utils
import storage.test.utils as storage_test_utils
import trigger.test.utils as trigger_test_utils
from data.data.data import Data
from data.data.json.data_v6 import convert_data_to_v6_json
from data.data.value import FileValue
from data.interface.interface import Interface
from data.interface.parameter import FileParameter
from error.models import get_unknown_error, reset_error_cache
from job.configuration.interface.job_interface import JobInterface
from job.models import Job, JobType, JobTypeRevision
from recipe.configuration.data.exceptions import InvalidRecipeConnection
from recipe.configuration.data.recipe_data import LegacyRecipeData
from recipe.configuration.definition.exceptions import InvalidDefinition
from recipe.configuration.definition.recipe_definition import LegacyRecipeDefinition
from recipe.definition.definition import RecipeDefinition
from recipe.definition.json.definition_v6 import convert_recipe_definition_to_v6_json
from recipe.exceptions import ReprocessError
from recipe.handlers.graph_delta import RecipeGraphDelta
from recipe.models import Recipe, RecipeInputFile, RecipeNode, RecipeType, RecipeTypeRevision
from storage.models import ScaleFile
from trigger.models import TriggerRule


class TestJobTypeManagerEditJobType(TransactionTestCase):

    def setUp(self):
        django.setup()

        self.workspace = storage_test_utils.create_workspace()

        interface = {
            'version': '1.0',
            'command': 'my_command',
            'command_arguments': 'args',
            'input_data': [{
                'name': 'Test Input 1',
                'type': 'file',
                'media_types': ['text/plain'],
            }],
            'output_data': [{
                'name': 'Test Output 1',
                'type': 'files',
                'media_type': 'image/png',
            }]}
        self.job_interface = JobInterface(interface)
        self.job_type = JobType.objects.create_job_type_v5('name', '1.0', self.job_interface)

        new_valid_interface = {
            'version': '1.0',
            'command': 'my_command',
            'command_arguments': 'args',
            'input_data': [{
                'name': 'Test Input 1',
                'type': 'file',
                'media_types': ['application/json'],
            }],
            'output_data': [{
                'name': 'Test Output 1',
                'type': 'files',
                'media_type': 'image/png',
            }]}
        self.new_valid_job_interface = JobInterface(new_valid_interface)

        new_invalid_interface = {
            'version': '1.0',
            'command': 'my_command',
            'command_arguments': 'args',
            'input_data': [{
                'name': 'Test Input 2',
                'type': 'files',
                'media_types': ['image/png', 'image/tiff'],
            }],
            'output_data': [{
                'name': 'Test Output 2',
                'type': 'file',
            }]}
        self.new_invalid_job_interface = JobInterface(new_invalid_interface)

        self.definition = {
            'version': '1.0',
            'input_data': [{
                'name': 'Recipe Input',
                'type': 'file',
                'media_types': ['text/plain'],
            }],
            'jobs': [{
                'name': 'Job 1',
                'job_type': {
                    'name': self.job_type.name,
                    'version': self.job_type.version,
                },
                'recipe_inputs': [{
                    'recipe_input': 'Recipe Input',
                    'job_input': 'Test Input 1',
                }]
            }]
        }
        self.recipe_def = LegacyRecipeDefinition(self.definition)
        self.recipe = RecipeType.objects.create_recipe_type('name', '1.0', 'title', 'description', self.recipe_def,
                                                            None)

    def test_valid_interface(self):
        """Tests calling JobTypeManager.edit_job_type_v5() where the job type is in a recipe and a valid interface change
        is made"""

        # Call test
        JobType.objects.edit_job_type_v5(self.job_type.id, self.new_valid_job_interface)

        # Check results
        job_type = JobType.objects.get(pk=self.job_type.id)
        self.assertDictEqual(job_type.get_job_interface().get_dict(), self.new_valid_job_interface.get_dict())
        self.assertEqual(job_type.revision_num, 2)
        # New revision due to interface change
        num_of_revs = JobTypeRevision.objects.filter(job_type_id=job_type.id).count()
        self.assertEqual(num_of_revs, 2)

    def test_invalid_interface(self):
        """Tests calling JobTypeManager.edit_job_type_v5() where the job type is in a recipe and an invalid interface
        change is made"""

        # Call test
        self.assertRaises(InvalidDefinition, JobType.objects.edit_job_type_v5, self.job_type.id,
                          self.new_invalid_job_interface)

        # Check results
        job_type = JobType.objects.get(pk=self.job_type.id)
        self.assertDictEqual(job_type.get_job_interface().get_dict(), self.job_interface.get_dict())
        self.assertEqual(job_type.revision_num, 1)
        num_of_revs = JobTypeRevision.objects.filter(job_type_id=job_type.id).count()
        self.assertEqual(num_of_revs, 1)


class TestJobTypeManagerValidateJobType(TransactionTestCase):

    def setUp(self):
        django.setup()

        self.workspace = storage_test_utils.create_workspace()

        interface = {
            'version': '1.0',
            'command': 'my_command',
            'command_arguments': 'args',
            'input_data': [{
                'name': 'Test Input 1',
                'type': 'file',
                'media_types': ['text/plain'],
            }],
            'output_data': [{
                'name': 'Test Output 1',
                'type': 'files',
                'media_type': 'image/png',
            }]}
        self.job_interface = JobInterface(interface)
        self.job_type = JobType.objects.create_job_type_v5('name', '1.0', self.job_interface)

        new_valid_interface = {
            'version': '1.0',
            'command': 'my_command',
            'command_arguments': 'args',
            'input_data': [{
                'name': 'Test Input 1',
                'type': 'file',
                'media_types': ['application/json'],
            }],
            'output_data': [{
                'name': 'Test Output 1',
                'type': 'files',
                'media_type': 'image/png',
            }]}
        self.new_valid_job_interface = JobInterface(new_valid_interface)

        new_invalid_interface = {
            'version': '1.0',
            'command': 'my_command',
            'command_arguments': 'args',
            'input_data': [{
                'name': 'Test Input 2',
                'type': 'files',
                'media_types': ['image/png', 'image/tiff'],
            }],
            'output_data': [{
                'name': 'Test Output 2',
                'type': 'file',
            }]}
        self.new_invalid_job_interface = JobInterface(new_invalid_interface)

        self.definition = {
            'version': '1.0',
            'input_data': [{
                'name': 'Recipe Input',
                'type': 'file',
                'media_types': ['text/plain'],
            }],
            'jobs': [{
                'name': 'Job 1',
                'job_type': {
                    'name': self.job_type.name,
                    'version': self.job_type.version,
                },
                'recipe_inputs': [{
                    'recipe_input': 'Recipe Input',
                    'job_input': 'Test Input 1',
                }]
            }]
        }
        self.recipe_def = LegacyRecipeDefinition(self.definition)
        self.recipe = RecipeType.objects.create_recipe_type('name', '1.0', 'title', 'description', self.recipe_def,
                                                            None)

    def test_valid_interface(self):
        """Tests calling JobTypeManager.validate_job_type_v5() where the job type is in a recipe and a valid interface
        change is made"""

        # Call test
        warnings = JobType.objects.validate_job_type_v5(self.job_type.name, self.job_type.version,
                                                     self.new_valid_job_interface)

        # Check results
        job_type = JobType.objects.get(pk=self.job_type.id)
        self.assertDictEqual(job_type.get_job_interface().get_dict(), self.job_interface.get_dict())
        self.assertEqual(job_type.revision_num, 1)
        num_of_revs = JobTypeRevision.objects.filter(job_type_id=job_type.id).count()
        self.assertEqual(num_of_revs, 1)
        self.assertEqual(len(warnings), 1)

    def test_invalid_interface(self):
        """Tests calling JobTypeManager.validate_job_type_v5() where the job type is in a recipe and an invalid interface
        change is made"""

        # Call test
        self.assertRaises(InvalidDefinition, JobType.objects.validate_job_type_v5, self.job_type.name,
                          self.job_type.version, self.new_invalid_job_interface)

        # Check results
        job_type = JobType.objects.get(pk=self.job_type.id)
        self.assertDictEqual(job_type.get_job_interface().get_dict(), self.job_interface.get_dict())
        self.assertEqual(job_type.revision_num, 1)
        num_of_revs = JobTypeRevision.objects.filter(job_type_id=job_type.id).count()
        self.assertEqual(num_of_revs, 1)


class TestRecipeManager(TransactionTestCase):

    def setUp(self):
        django.setup()

    def test_process_recipe_input(self):
        """Tests calling RecipeManager.process_recipe_input()"""

        date_1 = now()
        min_src_started_recipe_1 = date_1 - datetime.timedelta(days=200)
        max_src_ended_recipe_1 = date_1 + datetime.timedelta(days=200)
        date_2 = date_1 + datetime.timedelta(minutes=30)
        date_3 = date_1 + datetime.timedelta(minutes=40)
        date_4 = date_1 + datetime.timedelta(minutes=50)
        min_src_started_recipe_2 = date_1 - datetime.timedelta(days=500)
        max_src_ended_recipe_2 = date_1 + datetime.timedelta(days=500)
        s_class = 'A'
        s_sensor = '1'
        collection = '12345'
        task = 'abcd'
        workspace = storage_test_utils.create_workspace()
        file_1 = storage_test_utils.create_file(workspace=workspace, file_size=10485760.0,
                                                source_sensor_class=s_class, source_sensor=s_sensor,
                                                source_collection=collection, source_task=task)
        file_2 = storage_test_utils.create_file(workspace=workspace, file_size=104857600.0,
                                                source_started=date_2, source_ended=date_3,
                                                source_sensor_class=s_class, source_sensor=s_sensor,
                                                source_collection=collection, source_task=task)
        file_3 = storage_test_utils.create_file(workspace=workspace, file_size=987654321.0,
                                                source_started=min_src_started_recipe_1, source_ended=date_4)
        file_4 = storage_test_utils.create_file(workspace=workspace, file_size=46546.0,
                                                source_ended=max_src_ended_recipe_1)
        file_5 = storage_test_utils.create_file(workspace=workspace, file_size=83457.0, source_started=date_2)
        file_6 = storage_test_utils.create_file(workspace=workspace, file_size=42126588636633.0, source_ended=date_4)
        file_7 = storage_test_utils.create_file(workspace=workspace, file_size=76645464662354.0)
        file_8 = storage_test_utils.create_file(workspace=workspace, file_size=4654.0,
                                                source_started=min_src_started_recipe_2)
        file_9 = storage_test_utils.create_file(workspace=workspace, file_size=545.0, source_started=date_3,
                                                source_ended=max_src_ended_recipe_2)
        file_10 = storage_test_utils.create_file(workspace=workspace, file_size=0.154, source_ended=date_4,
                                                 source_sensor_class=s_class, source_sensor=s_sensor,
                                                 source_collection=collection, source_task=task)
        recipe_interface = Interface()
        recipe_interface.add_parameter(FileParameter('input_a', ['text/plain']))
        recipe_interface.add_parameter(FileParameter('input_b', ['text/plain'], multiple=True))
        definition = RecipeDefinition(recipe_interface)
        definition_dict = convert_recipe_definition_to_v6_json(definition).get_dict()
        recipe_type = recipe_test_utils.create_recipe_type(definition=definition_dict)

        data_1 = Data()
        data_1.add_value(FileValue('input_a', [file_1.id]))
        data_1.add_value(FileValue('input_b', [file_2.id, file_3.id, file_4.id, file_5.id]))
        data_1_dict = convert_data_to_v6_json(data_1).get_dict()
        data_2 = Data()
        data_2.add_value(FileValue('input_a', [file_6.id]))
        data_2.add_value(FileValue('input_b', [file_7.id, file_8.id, file_9.id, file_10.id]))
        data_2_dict = convert_data_to_v6_json(data_2).get_dict()
        data_3 = Data()
        data_3_dict = convert_data_to_v6_json(data_3).get_dict()

        recipe_1 = recipe_test_utils.create_recipe(recipe_type=recipe_type, input=data_1_dict)
        recipe_2 = recipe_test_utils.create_recipe(recipe_type=recipe_type, input=data_2_dict)
        recipe_3 = recipe_test_utils.create_recipe(recipe_type=recipe_type, input=data_3_dict)

        # Execute method
        Recipe.objects.process_recipe_input(recipe_1)
        Recipe.objects.process_recipe_input(recipe_2)
        Recipe.objects.process_recipe_input(recipe_3)

        # Retrieve updated recipe models
        recipes = Recipe.objects.filter(id__in=[recipe_1.id, recipe_2.id, recipe_3.id]).order_by('id')
        recipe_1 = recipes[0]
        recipe_2 = recipes[1]
        recipe_3 = recipes[2]

        # Check recipes for expected fields
        self.assertEqual(recipe_1.input_file_size, 1053.0)
        self.assertEqual(recipe_1.source_started, min_src_started_recipe_1)
        self.assertEqual(recipe_1.source_ended, max_src_ended_recipe_1)
        self.assertEqual(recipe_1.source_sensor_class, s_class)
        self.assertEqual(recipe_1.source_sensor, s_sensor)
        self.assertEqual(recipe_1.source_collection, collection)
        self.assertEqual(recipe_1.source_task, task)
        self.assertEqual(recipe_2.input_file_size, 113269857.0)
        self.assertEqual(recipe_2.source_started, min_src_started_recipe_2)
        self.assertEqual(recipe_2.source_ended, max_src_ended_recipe_2)
        self.assertEqual(recipe_2.source_sensor_class, s_class)
        self.assertEqual(recipe_2.source_sensor, s_sensor)
        self.assertEqual(recipe_2.source_collection, collection)
        self.assertEqual(recipe_2.source_task, task)
        self.assertEqual(recipe_3.input_file_size, 0.0)
        self.assertIsNone(recipe_3.source_started)
        self.assertIsNone(recipe_3.source_ended)

        # Make sure recipe input file models are created
        recipe_input_files = RecipeInputFile.objects.filter(recipe_id=recipe_1.id)
        self.assertEqual(len(recipe_input_files), 5)
        input_files_dict = {'input_a': set(), 'input_b': set()}
        for recipe_input_file in recipe_input_files:
            input_files_dict[recipe_input_file.recipe_input].add(recipe_input_file.input_file_id)
        self.assertDictEqual(input_files_dict, {'input_a': {file_1.id}, 'input_b': {file_2.id, file_3.id, file_4.id,
                                                                                    file_5.id}})
        recipe_input_files = RecipeInputFile.objects.filter(recipe_id=recipe_2.id)
        self.assertEqual(len(recipe_input_files), 5)
        input_files_dict = {'input_a': set(), 'input_b': set()}
        for recipe_input_file in recipe_input_files:
            input_files_dict[recipe_input_file.recipe_input].add(recipe_input_file.input_file_id)
        self.assertDictEqual(input_files_dict, {'input_a': {file_6.id}, 'input_b': {file_7.id, file_8.id, file_9.id,
                                                                                    file_10.id}})

        self.assertEqual(RecipeInputFile.objects.filter(recipe_id=recipe_3.id).count(), 0)


class TestRecipePopulateJobs(TransactionTestCase):

    def setUp(self):
        django.setup()

        self.recipe = recipe_test_utils.create_recipe()
        self.recipe_job1 = recipe_test_utils.create_recipe_job(self.recipe, job_name='job 1')
        self.recipe_job2 = recipe_test_utils.create_recipe_job(self.recipe, job_name='job 2')
        self.recipe_job3 = recipe_test_utils.create_recipe_job(self.recipe, job_name='job 3')

    def test_successful(self):
        """Tests calling ProductFileManager.populate_source_ancestors() successfully"""

        recipe = Recipe.objects.get_details(self.recipe.id)
        jobs = list(recipe.jobs)
        self.assertEqual(len(jobs), 3)
        self.assertTrue(jobs[0].node_name in ['job 1', 'job 2', 'job 3'])
        self.assertTrue(jobs[0].node_name in ['job 1', 'job 2', 'job 3'])
        self.assertTrue(jobs[0].node_name in ['job 1', 'job 2', 'job 3'])


class TestRecipeTypeManagerCreateRecipeType(TransactionTestCase):

    def setUp(self):
        django.setup()

        self.workspace = storage_test_utils.create_workspace()

        interface_1 = {
            'version': '1.0',
            'command': 'my_command',
            'command_arguments': 'args',
            'input_data': [{
                'name': 'Test Input 1',
                'type': 'file',
                'media_types': ['text/plain'],
            }],
            'output_data': [{
                'name': 'Test Output 1',
                'type': 'files',
                'media_type': 'image/png',
            }]}
        self.job_type_1 = job_test_utils.create_job_type(interface=interface_1)

        interface_2 = {
            'version': '1.0',
            'command': 'my_command',
            'command_arguments': 'args',
            'input_data': [{
                'name': 'Test Input 2',
                'type': 'files',
                'media_types': ['image/png', 'image/tiff'],
            }],
            'output_data': [{
                'name': 'Test Output 2',
                'type': 'file',
            }]}
        self.job_type_2 = job_test_utils.create_job_type(interface=interface_2)

        self.definition = {
            'version': '1.0',
            'input_data': [{
                'name': 'Recipe Input',
                'type': 'file',
                'media_types': ['text/plain'],
            }],
            'jobs': [{
                'name': 'Job 1',
                'job_type': {
                    'name': self.job_type_1.name,
                    'version': self.job_type_1.version,
                },
                'recipe_inputs': [{
                    'recipe_input': 'Recipe Input',
                    'job_input': 'Test Input 1',
                }]
            }, {
                'name': 'Job 2',
                'job_type': {
                    'name': self.job_type_2.name,
                    'version': self.job_type_2.version,
                },
                'dependencies': [{
                    'name': 'Job 1',
                    'connections': [{
                        'output': 'Test Output 1',
                        'input': 'Test Input 2',
                    }]
                }]
            }]
        }
        self.recipe_def = LegacyRecipeDefinition(self.definition)
        self.recipe_def.validate_job_interfaces()

    def test_successful(self):
        """Tests calling RecipeTypeManager.create_recipe_type() successfully."""

        name = 'test-recipe'
        version = '1.0'
        title = 'Test Recipe'
        desc = 'Test description'
        recipe_type = RecipeType.objects.create_recipe_type(name, version, title, desc, self.recipe_def, None)

        results_recipe_type = RecipeType.objects.get(pk=recipe_type.id)
        self.assertEqual(results_recipe_type.name, name)
        self.assertEqual(results_recipe_type.version, version)
        self.assertEqual(results_recipe_type.title, title)
        self.assertEqual(results_recipe_type.description, desc)
        self.assertDictEqual(results_recipe_type.definition, self.definition)

        results_recipe_type_rev = RecipeTypeRevision.objects.get(recipe_type_id=recipe_type.id, revision_num=1)
        self.assertDictEqual(results_recipe_type_rev.definition, self.definition)


class TestRecipeTypeManagerEditRecipeType(TransactionTestCase):

    def setUp(self):
        django.setup()

        self.workspace = storage_test_utils.create_workspace()

        interface_1 = {
            'version': '1.0',
            'command': 'my_command',
            'command_arguments': 'args',
            'input_data': [{
                'name': 'Test Input 1',
                'type': 'file',
                'media_types': ['text/plain'],
            }],
            'output_data': [{
                'name': 'Test Output 1',
                'type': 'files',
                'media_type': 'image/png',
            }]}
        self.job_type_1 = job_test_utils.create_job_type(interface=interface_1)

        interface_2 = {
            'version': '1.0',
            'command': 'my_command',
            'command_arguments': 'args',
            'input_data': [{
                'name': 'Test Input 2',
                'type': 'files',
                'media_types': ['image/png', 'image/tiff'],
            }],
            'output_data': [{
                'name': 'Test Output 2',
                'type': 'file',
            }]}
        self.job_type_2 = job_test_utils.create_job_type(interface=interface_2)

        self.definition = {
            'version': '1.0',
            'input_data': [{
                'name': 'Recipe Input',
                'type': 'file',
                'media_types': ['text/plain'],
            }],
            'jobs': [{
                'name': 'Job 1',
                'job_type': {
                    'name': self.job_type_1.name,
                    'version': self.job_type_1.version,
                },
                'recipe_inputs': [{
                    'recipe_input': 'Recipe Input',
                    'job_input': 'Test Input 1',
                }]
            }, {
                'name': 'Job 2',
                'job_type': {
                    'name': self.job_type_2.name,
                    'version': self.job_type_2.version,
                },
                'dependencies': [{
                    'name': 'Job 1',
                    'connections': [{
                        'output': 'Test Output 1',
                        'input': 'Test Input 2',
                    }]
                }]
            }]
        }
        self.recipe_def = LegacyRecipeDefinition(self.definition)
        self.recipe_def.validate_job_interfaces()

        self.new_definition = {
            'version': '1.0',
            'input_data': [{
                'name': 'Recipe Input',
                'type': 'file',
                'media_types': ['text/plain'],
            }],
            'jobs': [{
                'name': 'Job 1',
                'job_type': {
                    'name': self.job_type_1.name,
                    'version': self.job_type_1.version,
                },
                'recipe_inputs': [{
                    'recipe_input': 'Recipe Input',
                    'job_input': 'Test Input 1',
                }]
            }]
        }
        self.new_recipe_def = LegacyRecipeDefinition(self.new_definition)
        self.new_recipe_def.validate_job_interfaces()

        self.configuration = {
            'version': '1.0',
            'condition': {
                'media_type': 'text/plain'
            },
            'data': {
                'input_data_name': 'Recipe Input',
                'workspace_name': self.workspace.name
            }
        }
        self.trigger_config = recipe_test_utils.MockTriggerRuleConfiguration(recipe_test_utils.MOCK_TYPE,
                                                                             self.configuration)

        self.new_configuration = {
            'version': '1.0',
            'condition': {
                'media_type': 'application/json'
            },
            'data': {
                'input_data_name': 'Recipe Input',
                'workspace_name': self.workspace.name
            }
        }
        self.new_trigger_config = recipe_test_utils.MockTriggerRuleConfiguration(recipe_test_utils.MOCK_TYPE,
                                                                                 self.new_configuration)

    def test_change_simple_no_trigger(self):
        """Tests calling RecipeTypeManager.edit_recipe_type() with only basic attributes and no previous trigger rule"""

        # Create recipe_type
        name = 'test-recipe'
        version = '1.0'
        title = 'Test Recipe'
        desc = 'Test description'
        recipe_type = RecipeType.objects.create_recipe_type(name, version, title, desc, self.recipe_def, None)
        with transaction.atomic():
            recipe_type = RecipeType.objects.select_for_update().get(pk=recipe_type.id)
            # Edit the recipe
            new_title = 'New title'
            new_desc = 'New description'
            RecipeType.objects.edit_recipe_type(recipe_type.id, new_title, new_desc, None, None, False)
        recipe_type = RecipeType.objects.select_related('trigger_rule').get(pk=recipe_type.id)

        # Check results
        self.assertEqual(recipe_type.title, new_title)
        self.assertEqual(recipe_type.description, new_desc)
        self.assertDictEqual(recipe_type.get_recipe_definition().get_dict(), self.recipe_def.get_dict())
        self.assertEqual(recipe_type.revision_num, 1)
        self.assertIsNone(recipe_type.trigger_rule)
        num_of_revs = RecipeTypeRevision.objects.filter(recipe_type_id=recipe_type.id).count()
        self.assertEqual(num_of_revs, 1)

    def test_change_simple_with_trigger(self):
        """Tests calling RecipeTypeManager.edit_recipe_type() with only basic attributes and a previous trigger rule"""

        # Create recipe_type
        name = 'test-recipe'
        version = '1.0'
        title = 'Test Recipe'
        desc = 'Test description'
        trigger_rule = trigger_test_utils.create_trigger_rule(trigger_type=recipe_test_utils.MOCK_TYPE,
                                                              configuration=self.trigger_config.get_dict())
        trigger_rule_id = trigger_rule.id
        recipe_type = RecipeType.objects.create_recipe_type(name, version, title, desc, self.recipe_def, trigger_rule)
        with transaction.atomic():
            recipe_type = RecipeType.objects.select_for_update().get(pk=recipe_type.id)
            # Edit the recipe
            new_title = 'New title'
            new_desc = 'New description'
            RecipeType.objects.edit_recipe_type(recipe_type.id, new_title, new_desc, None, None, False)
        recipe_type = RecipeType.objects.select_related('trigger_rule').get(pk=recipe_type.id)

        # Check results
        self.assertEqual(recipe_type.title, new_title)
        self.assertEqual(recipe_type.description, new_desc)
        self.assertDictEqual(recipe_type.get_recipe_definition().get_dict(), self.recipe_def.get_dict())
        self.assertEqual(recipe_type.revision_num, 1)
        self.assertEqual(recipe_type.trigger_rule_id, trigger_rule_id)
        num_of_revs = RecipeTypeRevision.objects.filter(recipe_type_id=recipe_type.id).count()
        self.assertEqual(num_of_revs, 1)

    def test_change_to_definition(self):
        """Tests calling RecipeTypeManager.edit_recipe_type() with a change to the definition"""

        # Create recipe_type
        name = 'test-recipe'
        version = '1.0'
        title = 'Test Recipe'
        desc = 'Test description'
        trigger_rule = trigger_test_utils.create_trigger_rule(trigger_type=recipe_test_utils.MOCK_TYPE,
                                                              configuration=self.trigger_config.get_dict())
        trigger_rule_id = trigger_rule.id
        recipe_type = RecipeType.objects.create_recipe_type(name, version, title, desc, self.recipe_def, trigger_rule)
        with transaction.atomic():
            recipe_type = RecipeType.objects.select_for_update().get(pk=recipe_type.id)
            # Edit the recipe
            RecipeType.objects.edit_recipe_type(recipe_type.id, None, None, self.new_recipe_def, None, False)
        recipe_type = RecipeType.objects.select_related('trigger_rule').get(pk=recipe_type.id)

        # Check results
        self.assertEqual(recipe_type.title, title)
        self.assertEqual(recipe_type.description, desc)
        self.assertDictEqual(recipe_type.get_recipe_definition().get_dict(), self.new_recipe_def.get_dict())
        self.assertEqual(recipe_type.revision_num, 2)
        self.assertEqual(recipe_type.trigger_rule_id, trigger_rule_id)
        trigger_rule = TriggerRule.objects.get(pk=trigger_rule_id)
        self.assertTrue(trigger_rule.is_active)
        # New revision due to definition change
        num_of_revs = RecipeTypeRevision.objects.filter(recipe_type_id=recipe_type.id).count()
        self.assertEqual(num_of_revs, 2)

    def test_change_to_trigger_rule(self):
        """Tests calling RecipeTypeManager.edit_recipe_type() with a change to the trigger rule"""

        # Create recipe_type
        name = 'test-recipe'
        version = '1.0'
        title = 'Test Recipe'
        desc = 'Test description'
        trigger_rule = trigger_test_utils.create_trigger_rule(trigger_type=recipe_test_utils.MOCK_TYPE,
                                                              configuration=self.trigger_config.get_dict())
        trigger_rule_id = trigger_rule.id
        new_trigger_rule = trigger_test_utils.create_trigger_rule(trigger_type=recipe_test_utils.MOCK_TYPE,
                                                                  configuration=self.new_trigger_config.get_dict())
        new_trigger_rule_id = new_trigger_rule.id
        recipe_type = RecipeType.objects.create_recipe_type(name, version, title, desc, self.recipe_def, trigger_rule)
        with transaction.atomic():
            recipe_type = RecipeType.objects.select_for_update().get(pk=recipe_type.id)
            # Edit the recipe
            RecipeType.objects.edit_recipe_type(recipe_type.id, None, None, None, new_trigger_rule, False)
        recipe_type = RecipeType.objects.select_related('trigger_rule').get(pk=recipe_type.id)

        # Check results
        self.assertEqual(recipe_type.title, title)
        self.assertEqual(recipe_type.description, desc)
        self.assertDictEqual(recipe_type.get_recipe_definition().get_dict(), self.recipe_def.get_dict())
        self.assertEqual(recipe_type.revision_num, 1)
        self.assertEqual(recipe_type.trigger_rule_id, new_trigger_rule_id)
        trigger_rule = TriggerRule.objects.get(pk=trigger_rule_id)
        self.assertFalse(trigger_rule.is_active)
        new_trigger_rule = TriggerRule.objects.get(pk=new_trigger_rule_id)
        self.assertTrue(new_trigger_rule.is_active)
        num_of_revs = RecipeTypeRevision.objects.filter(recipe_type_id=recipe_type.id).count()
        self.assertEqual(num_of_revs, 1)

    def test_remove_trigger_rule(self):
        """Tests calling RecipeTypeManager.edit_recipe_type() that removes the trigger rule"""

        # Create recipe_type
        name = 'test-recipe'
        version = '1.0'
        title = 'Test Recipe'
        desc = 'Test description'
        trigger_rule = trigger_test_utils.create_trigger_rule(trigger_type=recipe_test_utils.MOCK_TYPE,
                                                              configuration=self.trigger_config.get_dict())
        trigger_rule_id = trigger_rule.id
        recipe_type = RecipeType.objects.create_recipe_type(name, version, title, desc, self.recipe_def, trigger_rule)
        with transaction.atomic():
            recipe_type = RecipeType.objects.select_for_update().get(pk=recipe_type.id)
            # Edit the recipe
            RecipeType.objects.edit_recipe_type(recipe_type.id, None, None, None, None, True)
        recipe_type = RecipeType.objects.select_related('trigger_rule').get(pk=recipe_type.id)

        # Check results
        self.assertEqual(recipe_type.title, title)
        self.assertEqual(recipe_type.description, desc)
        self.assertDictEqual(recipe_type.get_recipe_definition().get_dict(), self.recipe_def.get_dict())
        self.assertEqual(recipe_type.revision_num, 1)
        self.assertIsNone(recipe_type.trigger_rule)
        trigger_rule = TriggerRule.objects.get(pk=trigger_rule_id)
        self.assertFalse(trigger_rule.is_active)
        num_of_revs = RecipeTypeRevision.objects.filter(recipe_type_id=recipe_type.id).count()
        self.assertEqual(num_of_revs, 1)

    def test_change_to_both(self):
        """Tests calling RecipeTypeManager.edit_recipe_type() with a change to both the definition and trigger rule"""

        # Create recipe_type
        name = 'test-recipe'
        version = '1.0'
        title = 'Test Recipe'
        desc = 'Test description'
        trigger_rule = trigger_test_utils.create_trigger_rule(trigger_type=recipe_test_utils.MOCK_TYPE,
                                                              configuration=self.trigger_config.get_dict())
        trigger_rule_id = trigger_rule.id
        new_trigger_rule = trigger_test_utils.create_trigger_rule(trigger_type=recipe_test_utils.MOCK_TYPE,
                                                                  configuration=self.new_trigger_config.get_dict())
        new_trigger_rule_id = new_trigger_rule.id
        recipe_type = RecipeType.objects.create_recipe_type(name, version, title, desc, self.recipe_def, trigger_rule)
        with transaction.atomic():
            recipe_type = RecipeType.objects.select_for_update().get(pk=recipe_type.id)
            # Edit the recipe
            RecipeType.objects.edit_recipe_type(recipe_type.id, None, None, self.new_recipe_def, new_trigger_rule,
                                                False)
        recipe_type = RecipeType.objects.select_related('trigger_rule').get(pk=recipe_type.id)

        # Check results
        self.assertEqual(recipe_type.title, title)
        self.assertEqual(recipe_type.description, desc)
        self.assertDictEqual(recipe_type.get_recipe_definition().get_dict(), self.new_recipe_def.get_dict())
        self.assertEqual(recipe_type.revision_num, 2)
        self.assertEqual(recipe_type.trigger_rule_id, new_trigger_rule_id)
        trigger_rule = TriggerRule.objects.get(pk=trigger_rule_id)
        self.assertFalse(trigger_rule.is_active)
        new_trigger_rule = TriggerRule.objects.get(pk=new_trigger_rule_id)
        self.assertTrue(new_trigger_rule.is_active)
        # New revision due to definition change
        num_of_revs = RecipeTypeRevision.objects.filter(recipe_type_id=recipe_type.id).count()
        self.assertEqual(num_of_revs, 2)

    def test_invalid_trigger_rule(self):
        """Tests calling RecipeTypeManager.edit_recipe_type() with a new invalid trigger rule"""

        # Create recipe_type
        name = 'test-recipe'
        version = '1.0'
        title = 'Test Recipe'
        desc = 'Test description'
        trigger_rule = trigger_test_utils.create_trigger_rule(trigger_type=recipe_test_utils.MOCK_TYPE,
                                                              configuration=self.trigger_config.get_dict())
        trigger_rule_id = trigger_rule.id
        new_trigger_rule = trigger_test_utils.create_trigger_rule(trigger_type=recipe_test_utils.MOCK_ERROR_TYPE,
                                                                  configuration=self.new_trigger_config.get_dict())
        recipe_type = RecipeType.objects.create_recipe_type(name, version, title, desc, self.recipe_def, trigger_rule)
        with transaction.atomic():
            recipe_type = RecipeType.objects.select_for_update().get(pk=recipe_type.id)
            # Edit the recipe
            self.assertRaises(InvalidRecipeConnection, RecipeType.objects.edit_recipe_type, recipe_type.id, None, None,
                              self.new_recipe_def, new_trigger_rule, False)
        recipe_type = RecipeType.objects.select_related('trigger_rule').get(pk=recipe_type.id)

        # Check results
        self.assertEqual(recipe_type.title, title)
        self.assertEqual(recipe_type.description, desc)
        self.assertDictEqual(recipe_type.get_recipe_definition().get_dict(), self.recipe_def.get_dict())
        self.assertEqual(recipe_type.revision_num, 1)
        self.assertEqual(recipe_type.trigger_rule_id, trigger_rule_id)
        trigger_rule = TriggerRule.objects.get(pk=trigger_rule_id)
        self.assertTrue(trigger_rule.is_active)
        num_of_revs = RecipeTypeRevision.objects.filter(recipe_type_id=recipe_type.id).count()
        self.assertEqual(num_of_revs, 1)
