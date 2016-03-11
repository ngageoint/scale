from __future__ import unicode_literals

import django
from django.db import transaction
from django.test import TransactionTestCase

import job.test.utils as job_test_utils
import recipe.test.utils as recipe_test_utils
import storage.test.utils as storage_test_utils
import trigger.test.utils as trigger_test_utils
from job.configuration.interface.job_interface import JobInterface
from job.models import JobType, JobTypeRevision
from recipe.configuration.data.exceptions import InvalidRecipeConnection
from recipe.configuration.definition.exceptions import InvalidDefinition
from recipe.configuration.definition.recipe_definition import RecipeDefinition
from recipe.models import Recipe, RecipeJob, RecipeType, RecipeTypeRevision
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
        self.job_type = JobType.objects.create_job_type('name', '1.0', self.job_interface)

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
        self.recipe_def = RecipeDefinition(self.definition)
        self.recipe = RecipeType.objects.create_recipe_type('name', '1.0', 'title', 'description', self.recipe_def,
                                                            None)

    def test_valid_interface(self):
        """Tests calling JobTypeManager.edit_job_type() where the job type is in a recipe and a valid interface change
        is made"""

        # Call test
        JobType.objects.edit_job_type(self.job_type.id, self.new_valid_job_interface)

        # Check results
        job_type = JobType.objects.get(pk=self.job_type.id)
        self.assertDictEqual(job_type.get_job_interface().get_dict(), self.new_valid_job_interface.get_dict())
        self.assertEqual(job_type.revision_num, 2)
        # New revision due to interface change
        num_of_revs = JobTypeRevision.objects.filter(job_type_id=job_type.id).count()
        self.assertEqual(num_of_revs, 2)

    def test_invalid_interface(self):
        """Tests calling JobTypeManager.edit_job_type() where the job type is in a recipe and an invalid interface
        change is made"""

        # Call test
        self.assertRaises(InvalidDefinition, JobType.objects.edit_job_type, self.job_type.id, self.new_invalid_job_interface)

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
        self.job_type = JobType.objects.create_job_type('name', '1.0', self.job_interface)

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
        self.recipe_def = RecipeDefinition(self.definition)
        self.recipe = RecipeType.objects.create_recipe_type('name', '1.0', 'title', 'description', self.recipe_def,
                                                            None)

    def test_valid_interface(self):
        """Tests calling JobTypeManager.validate_job_type() where the job type is in a recipe and a valid interface
        change is made"""

        # Call test
        warnings = JobType.objects.validate_job_type(self.job_type.name, self.job_type.version,
                                                     self.new_valid_job_interface)

        # Check results
        job_type = JobType.objects.get(pk=self.job_type.id)
        self.assertDictEqual(job_type.get_job_interface().get_dict(), self.job_interface.get_dict())
        self.assertEqual(job_type.revision_num, 1)
        num_of_revs = JobTypeRevision.objects.filter(job_type_id=job_type.id).count()
        self.assertEqual(num_of_revs, 1)
        self.assertEqual(len(warnings), 1)

    def test_invalid_interface(self):
        """Tests calling JobTypeManager.validate_job_type() where the job type is in a recipe and an invalid interface
        change is made"""

        # Call test
        self.assertRaises(InvalidDefinition, JobType.objects.validate_job_type, self.job_type.name, self.job_type.version,
                          self.new_invalid_job_interface)

        # Check results
        job_type = JobType.objects.get(pk=self.job_type.id)
        self.assertDictEqual(job_type.get_job_interface().get_dict(), self.job_interface.get_dict())
        self.assertEqual(job_type.revision_num, 1)
        num_of_revs = JobTypeRevision.objects.filter(job_type_id=job_type.id).count()
        self.assertEqual(num_of_revs, 1)


class TestRecipeManagerCreateRecipe(TransactionTestCase):

    def setUp(self):
        django.setup()

        self.workspace = storage_test_utils.create_workspace()

        self.file = storage_test_utils.create_file()

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

        definition = {
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
        RecipeDefinition(definition).validate_job_interfaces()
        self.recipe_type = recipe_test_utils.create_recipe_type(definition=definition)

        self.data = {
            'version': '1.0',
            'input_data': [{
                'name': 'Recipe Input',
                'file_id': self.file.id,
            }],
            'workspace_id': self.workspace.id,
        }

    def test_successful(self):
        """Tests calling RecipeManager.create_recipe() successfully."""

        event = trigger_test_utils.create_trigger_event()
        handler = Recipe.objects.create_recipe(recipe_type=self.recipe_type, event=event, data=self.data)

        # Make sure the recipe jobs get created with the correct job types
        recipe_job_1 = RecipeJob.objects.get(recipe_id=handler.recipe_id, job_name='Job 1')
        recipe_job_2 = RecipeJob.objects.get(recipe_id=handler.recipe_id, job_name='Job 2')
        self.assertEqual(recipe_job_1.job.job_type.id, self.job_type_1.id)
        self.assertEqual(recipe_job_2.job.job_type.id, self.job_type_2.id)
        # Make sure the recipe jobs get created in the correct order
        self.assertLess(recipe_job_1.job_id, recipe_job_2.job_id)


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
        self.assertTrue(jobs[0].job_name in ['job 1', 'job 2', 'job 3'])
        self.assertTrue(jobs[0].job_name in ['job 1', 'job 2', 'job 3'])
        self.assertTrue(jobs[0].job_name in ['job 1', 'job 2', 'job 3'])


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
        self.recipe_def = RecipeDefinition(self.definition)
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
        self.recipe_def = RecipeDefinition(self.definition)
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
        self.new_recipe_def = RecipeDefinition(self.new_definition)
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
        """Tests calling RecipeTypeManager.edit_recipe_type() with a change to both the definition and the trigger rule"""

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
            RecipeType.objects.edit_recipe_type(recipe_type.id, None, None, self.new_recipe_def, new_trigger_rule, False)
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
