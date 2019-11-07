from __future__ import unicode_literals

import django
from django.test import TransactionTestCase

from data.data.data import Data
from job.messages.create_jobs import create_jobs_message, create_jobs_messages_for_recipe, CreateJobs, RecipeJob
from job.models import Job
from job.test import utils as job_test_utils
from trigger.test import utils as trigger_test_utils



class TestCreateJobs(TransactionTestCase):

    def setUp(self):
        django.setup()

    def test_json_input_data(self):
        """Tests converting a CreateJobs message to and from JSON when creating a job from input data"""

        manifest = {
            'seedVersion': '1.0.0',
            'job': {
                'name': 'name',
                'jobVersion': '1.0.0',
                'packageVersion': '1.0.0',
                'title': 'Title',
                'description': 'This is a description',
                'maintainer': {
                    'name': 'John Doe',
                    'email': 'jdoe@example.com'
                },
                'timeout': 10
            }
        }
        job_type = job_test_utils.create_seed_job_type(manifest=manifest)
        event = trigger_test_utils.create_trigger_event()
        data = Data()

        # Create message
        message = create_jobs_message(job_type.name, job_type.version, job_type.revision_num, event.id, input_data=data)

        # Convert message to JSON and back, and then execute
        message_json_dict = message.to_json()
        new_message = CreateJobs.from_json(message_json_dict)
        result = new_message.execute()

        self.assertTrue(result)
        self.assertEqual(Job.objects.filter(job_type_id=job_type.id, event_id=event.id).count(), 1)

    def test_json_recipe(self):
        """Tests converting a CreateJobs message to and from JSON when creating jobs for a recipe"""

        from batch.test import utils as batch_test_utils
        from recipe.models import RecipeNode
        from recipe.test import utils as recipe_test_utils
        from storage.test import utils as storage_test_utils

        event = trigger_test_utils.create_trigger_event()
        job_type_1 = job_test_utils.create_seed_job_type()
        job_type_2 = job_test_utils.create_seed_job_type()
        definition = {
            'version': '7',
             'input': {'files': [{'name': 'INPUT_IMAGE', 'media_types': ['image/png'], 'required': True, 'multiple': False}],
                       'json': []},
            'nodes': {
                'node_1': {
                    'dependencies': [],
                    'input': {'INPUT_IMAGE': {'type': 'recipe', 'input': 'INPUT_IMAGE'}},
                    'node_type': {
                        'node_type': 'job',
                        'job_type_name': job_type_1.name,
                        'job_type_version': job_type_1.version,
                        'job_type_revision': job_type_1.revision_num
                    }
                },
                'node_2': {
                    'dependencies': [],
                    'input': {'INPUT_IMAGE': {'type': 'recipe', 'input': 'INPUT_IMAGE'}},
                    'node_type': {
                        'node_type': 'job',
                        'job_type_name': job_type_2.name,
                        'job_type_version': job_type_2.version,
                        'job_type_revision': job_type_2.revision_num
                    }
                }
            }
        }

        rtype = recipe_test_utils.create_recipe_type_v6(definition=definition)
        batch = batch_test_utils.create_batch(recipe_type=rtype)
        workspace = storage_test_utils.create_workspace()
        file1 = storage_test_utils.create_file(file_name='input_a.PNG', file_type='SOURCE', media_type='image/png',
                                                    file_size=10, data_type_tags=['type'], file_path='the_path',
                                                    workspace=workspace)
        recipe_data = {'version': '6', 'files': {'INPUT_IMAGE': [file1.id]}, 'json': {}}
        recipe = recipe_test_utils.create_recipe(event=event, batch=batch, recipe_type=rtype, input=recipe_data)
        recipe_jobs = [RecipeJob(job_type_1.name, job_type_1.version, job_type_1.revision_num, 'node_1', False),
                       RecipeJob(job_type_2.name, job_type_2.version, job_type_2.revision_num, 'node_2', True)]

        # Create message
        message = create_jobs_messages_for_recipe(recipe, recipe_jobs)[0]

        # Convert message to JSON and back, and then execute
        message_json_dict = message.to_json()
        new_message = CreateJobs.from_json(message_json_dict)
        result = new_message.execute()
        self.assertTrue(result)

        self.assertEqual(Job.objects.filter(recipe_id=recipe.id, event_id=recipe.event_id).count(), 2)
        recipe_nodes = RecipeNode.objects.filter(recipe_id=recipe.id)

        self.assertEqual(len(recipe_nodes), 2)
        for recipe_node in recipe_nodes:
            jobs = Job.objects.filter(recipe_node=recipe_node)
            self.assertEqual(len(jobs), 1)
            if recipe_node.node_name == 'node_1':
                job_1 = jobs[0]
                self.assertEqual(job_1.job_type_id, job_type_1.id)
                self.assertEqual(job_1.event_id, event.id)
                self.assertEqual(job_1.batch_id, batch.id)
            elif recipe_node.node_name == 'node_2':
                job_2 = jobs[0]
                self.assertEqual(job_2.job_type_id, job_type_2.id)
                self.assertEqual(job_2.event_id, event.id)
                self.assertEqual(job_2.batch_id, batch.id)
            else:
                self.fail('%s is the wrong node name' % recipe_node.node_name)

        # Should be one message for updating metrics for the recipe
        self.assertEqual(len(new_message.new_messages), 1)
        update_metrics_msg = None
        if new_message.new_messages[0].type == 'update_recipe_metrics':
            update_metrics_msg = new_message.new_messages[0]
        self.assertIsNotNone(update_metrics_msg)
        # Check message to update recipe metrics for the recipe containing the new jobs
        self.assertListEqual(update_metrics_msg._recipe_ids, [recipe.id])

    def test_json_recipe_superseded(self):
        """Tests converting a CreateJobs message to and from JSON when creating jobs for a recipe that supersedes
        another recipe
        """

        from batch.test import utils as batch_test_utils
        from recipe.models import RecipeNode
        from recipe.test import utils as recipe_test_utils
        from storage.test import utils as storage_test_utils

        job_type_1 = job_test_utils.create_seed_job_type()
        job_type_2 = job_test_utils.create_seed_job_type()
        definition = {
            'version': '7',
            'input': {
                'files': [{'name': 'INPUT_IMAGE', 'media_types': ['image/png'], 'required': True, 'multiple': False}],
                'json': []},
            'nodes': {
                'node_1': {
                    'dependencies': [],
                    'input': {'INPUT_IMAGE': {'type': 'recipe', 'input': 'INPUT_IMAGE'}},
                    'node_type': {
                        'node_type': 'job',
                        'job_type_name': job_type_1.name,
                        'job_type_version': job_type_1.version,
                        'job_type_revision': job_type_1.revision_num
                    }
                },
                'node_2': {
                    'dependencies': [],
                    'input': {'INPUT_IMAGE': {'type': 'recipe', 'input': 'INPUT_IMAGE'}},
                    'node_type': {
                        'node_type': 'job',
                        'job_type_name': job_type_2.name,
                        'job_type_version': job_type_2.version,
                        'job_type_revision': job_type_2.revision_num
                    }
                }
            }
        }
        rtype = recipe_test_utils.create_recipe_type_v6(definition=definition)
        batch = batch_test_utils.create_batch(recipe_type=rtype)
        event = trigger_test_utils.create_trigger_event()

        workspace = storage_test_utils.create_workspace()
        file1 = storage_test_utils.create_file(file_name='input_a.PNG', file_type='SOURCE', media_type='image/png',
                                               file_size=10, data_type_tags=['type'], file_path='the_path',
                                               workspace=workspace)
        recipe_data = {'version': '6', 'files': {'INPUT_IMAGE': [file1.id]}, 'json': {}}
        superseded_recipe  = recipe_test_utils.create_recipe(event=event, batch=batch, recipe_type=rtype, input=recipe_data)

        superseded_job_1 = job_test_utils.create_job(job_type=job_type_1, is_superseded=True)
        superseded_job_2 = job_test_utils.create_job(job_type=job_type_2, is_superseded=True)
        recipe_test_utils.create_recipe_node(recipe=superseded_recipe, node_name='node_1', job=superseded_job_1,
                                             save=True)
        recipe_test_utils.create_recipe_node(recipe=superseded_recipe, node_name='node_2', job=superseded_job_2,
                                             save=True)
        recipe = recipe_test_utils.create_recipe(recipe_type=superseded_recipe.recipe_type,
                                                 superseded_recipe=superseded_recipe, event=event, batch=batch,
                                                 input=recipe_data)
        recipe_jobs = [RecipeJob(job_type_1.name, job_type_1.version, job_type_1.revision_num, 'node_1', False),
                       RecipeJob(job_type_2.name, job_type_2.version, job_type_2.revision_num, 'node_2', True)]

        # Create message
        message = create_jobs_messages_for_recipe(recipe, recipe_jobs)[0]

        # Convert message to JSON and back, and then execute
        message_json_dict = message.to_json()
        new_message = CreateJobs.from_json(message_json_dict)
        result = new_message.execute()
        self.assertTrue(result)

        self.assertEqual(Job.objects.filter(recipe_id=recipe.id, event_id=recipe.event_id).count(), 2)
        recipe_nodes = RecipeNode.objects.filter(recipe_id=recipe.id)
        self.assertEqual(len(recipe_nodes), 2)
        for recipe_node in recipe_nodes:
            jobs = Job.objects.filter(recipe_node=recipe_node)
            self.assertEqual(len(jobs), 1)
            if recipe_node.node_name == 'node_1':
                job_1 = jobs[0]
                self.assertEqual(job_1.job_type_id, job_type_1.id)
                self.assertEqual(job_1.event_id, event.id)
                self.assertEqual(job_1.batch_id, batch.id)
                self.assertEqual(job_1.recipe_id, recipe.id)
                self.assertEqual(job_1.root_recipe_id, superseded_recipe.id)
                self.assertEqual(job_1.superseded_job_id, superseded_job_1.id)
                self.assertEqual(job_1.root_superseded_job_id, superseded_job_1.id)
            elif recipe_node.node_name == 'node_2':
                job_2 = jobs[0]
                self.assertEqual(job_2.job_type_id, job_type_2.id)
                self.assertEqual(job_2.event_id, event.id)
                self.assertEqual(job_2.batch_id, batch.id)
                self.assertEqual(job_2.recipe_id, recipe.id)
                self.assertEqual(job_2.root_recipe_id, superseded_recipe.id)
                self.assertEqual(job_2.superseded_job_id, superseded_job_2.id)
                self.assertEqual(job_2.root_superseded_job_id, superseded_job_2.id)
            else:
                self.fail('%s is the wrong node name' % recipe_node.node_name)

        # Should be one message for updating metrics for the recipe
        self.assertEqual(len(new_message.new_messages), 1)
        update_metrics_msg = None
        if new_message.new_messages[0].type == 'update_recipe_metrics':
            update_metrics_msg = new_message.new_messages[0]
        self.assertIsNotNone(update_metrics_msg)
        # Check message to update recipe metrics for the recipe containing the new jobs
        self.assertListEqual(update_metrics_msg._recipe_ids, [recipe.id])

    def test_execute_input_data(self):
        """Tests calling CreateJobs.execute() with input data"""

        manifest = {
            'seedVersion': '1.0.0',
            'job': {
                'name': 'name',
                'jobVersion': '1.0.0',
                'packageVersion': '1.0.0',
                'title': 'Title',
                'description': 'This is a description',
                'maintainer': {
                    'name': 'John Doe',
                    'email': 'jdoe@example.com'
                },
                'timeout': 10,
                'interface': {
                    'command': 'the command'
                }
            }
        }
        job_type = job_test_utils.create_seed_job_type(manifest=manifest)
        event = trigger_test_utils.create_trigger_event()
        data = Data()

        # Create and execute message
        message = create_jobs_message(job_type.name, job_type.version, job_type.revision_num, event.id, input_data=data)
        result = message.execute()
        self.assertTrue(result)

        # Check for job creation
        self.assertEqual(Job.objects.filter(job_type_id=job_type.id, event_id=event.id).count(), 1)

        # Test executing message again
        message_json_dict = message.to_json()
        message = CreateJobs.from_json(message_json_dict)
        result = message.execute()
        self.assertTrue(result)

        # Check that a second job is not created
        self.assertEqual(Job.objects.filter(job_type_id=job_type.id, event_id=event.id).count(), 1)

    def test_execute_input_data_invalid(self):
        """Tests calling CreateJobs.execute() when the input data is invalid"""

        manifest = {
            'seedVersion': '1.0.0',
            'job': {
                'name': 'name',
                'jobVersion': '1.0.0',
                'packageVersion': '1.0.0',
                'title': 'Title',
                'description': 'This is a description',
                'maintainer': {
                    'name': 'John Doe',
                    'email': 'jdoe@example.com'
                },
                'timeout': 10,
                'interface': {
                    'command': 'the command',
                    'inputs': {
                        'files': [{'name': 'input_a'}]
                    }
                }
            }
        }
        job_type = job_test_utils.create_seed_job_type(manifest=manifest)
        event = trigger_test_utils.create_trigger_event()
        # Data does not provide required input_a so it is invalid
        data = Data()

        # Create and execute message
        message = create_jobs_message(job_type.name, job_type.version, job_type.revision_num, event.id, input_data=data)
        result = message.execute()
        self.assertTrue(result)

        # Check that no job is created
        self.assertEqual(Job.objects.filter(job_type_id=job_type.id, event_id=event.id).count(), 0)

        # Should be no new messages
        self.assertEqual(len(message.new_messages), 0)

    def test_execute_recipe(self):
        """Tests calling CreateJobs.execute() successfully for jobs within a recipe"""

        from batch.test import utils as batch_test_utils
        from recipe.models import RecipeNode
        from recipe.test import utils as recipe_test_utils
        from storage.test import utils as storage_test_utils

        event = trigger_test_utils.create_trigger_event()
        job_type_1 = job_test_utils.create_seed_job_type()
        job_type_2 = job_test_utils.create_seed_job_type()

        definition = {
            'version': '7',
            'input': {
                'files': [{'name': 'INPUT_IMAGE', 'media_types': ['image/png'], 'required': True, 'multiple': False}],
                'json': []},
            'nodes': {
                'node_1': {
                    'dependencies': [],
                    'input': {'INPUT_IMAGE': {'type': 'recipe', 'input': 'INPUT_IMAGE'}},
                    'node_type': {
                        'node_type': 'job',
                        'job_type_name': job_type_1.name,
                        'job_type_version': job_type_1.version,
                        'job_type_revision': job_type_1.revision_num
                    }
                },
                'node_2': {
                    'dependencies': [],
                    'input': {'INPUT_IMAGE': {'type': 'recipe', 'input': 'INPUT_IMAGE'}},
                    'node_type': {
                        'node_type': 'job',
                        'job_type_name': job_type_2.name,
                        'job_type_version': job_type_2.version,
                        'job_type_revision': job_type_2.revision_num
                    }
                }
            }
        }
        rtype = recipe_test_utils.create_recipe_type_v6(definition=definition)

        batch = batch_test_utils.create_batch(recipe_type=rtype)
        recipe_jobs = [RecipeJob(job_type_1.name, job_type_1.version, job_type_1.revision_num, 'node_1', False),
                       RecipeJob(job_type_2.name, job_type_2.version, job_type_2.revision_num, 'node_2', True)]

        workspace = storage_test_utils.create_workspace()
        file1 = storage_test_utils.create_file(file_name='input_a.PNG', file_type='SOURCE', media_type='image/png',
                                               file_size=10, data_type_tags=['type'], file_path='the_path',
                                               workspace=workspace)
        recipe_data = {'version': '6', 'files': {'INPUT_IMAGE': [file1.id]}, 'json': {}}
        recipe = recipe_test_utils.create_recipe(event=event, recipe_type=rtype, batch=batch, input=recipe_data)

        # Create and execute message
        message = create_jobs_messages_for_recipe(recipe, recipe_jobs)[0]
        result = message.execute()
        self.assertTrue(result)

        self.assertEqual(Job.objects.filter(recipe_id=recipe.id, event_id=recipe.event_id).count(), 2)
        recipe_nodes = RecipeNode.objects.filter(recipe_id=recipe.id)
        self.assertEqual(len(recipe_nodes), 2)
        for recipe_node in recipe_nodes:
            jobs = Job.objects.filter(recipe_node=recipe_node)
            self.assertEqual(len(jobs), 1)
            if recipe_node.node_name == 'node_1':
                job_1 = jobs[0]
                self.assertEqual(job_1.job_type_id, job_type_1.id)
                self.assertEqual(job_1.event_id, event.id)
                self.assertEqual(job_1.batch_id, batch.id)
            elif recipe_node.node_name == 'node_2':
                job_2 = jobs[0]
                self.assertEqual(job_2.job_type_id, job_type_2.id)
                self.assertEqual(job_2.event_id, event.id)
                self.assertEqual(job_2.batch_id, batch.id)
            else:
                self.fail('%s is the wrong node name' % recipe_node.node_name)

        # Should be one message for updating metrics for the recipe
        self.assertEqual(len(message.new_messages), 1)
        update_metrics_msg = None
        if message.new_messages[0].type == 'update_recipe_metrics':
            update_metrics_msg = message.new_messages[0]
        self.assertIsNotNone(update_metrics_msg)
        # Check message to update recipe metrics for the recipe containing the new jobs
        self.assertListEqual(update_metrics_msg._recipe_ids, [recipe.id])

        # Test executing message again
        message_json_dict = message.to_json()
        message = CreateJobs.from_json(message_json_dict)
        result = message.execute()
        self.assertTrue(result)

        self.assertEqual(Job.objects.filter(recipe_id=recipe.id, event_id=recipe.event_id).count(), 2)
        recipe_nodes = RecipeNode.objects.filter(recipe_id=recipe.id)
        self.assertEqual(len(recipe_nodes), 2)
        for recipe_node in recipe_nodes:
            jobs = Job.objects.filter(recipe_node=recipe_node)
            self.assertEqual(len(jobs), 1)
            if recipe_node.node_name == 'node_1':
                job_1 = jobs[0]
                self.assertEqual(job_1.job_type_id, job_type_1.id)
                self.assertEqual(job_1.event_id, event.id)
                self.assertEqual(job_1.batch_id, batch.id)
            elif recipe_node.node_name == 'node_2':
                job_2 = jobs[0]
                self.assertEqual(job_2.job_type_id, job_type_2.id)
                self.assertEqual(job_2.event_id, event.id)
                self.assertEqual(job_2.batch_id, batch.id)
            else:
                self.fail('%s is the wrong node name' % recipe_node.node_name)

        # Should be one messages for updating metrics for the recipe
        self.assertEqual(len(message.new_messages), 1)
        update_metrics_msg = None
        if message.new_messages[0].type == 'update_recipe_metrics':
            update_metrics_msg = message.new_messages[0]
        self.assertIsNotNone(update_metrics_msg)
        # Check message to update recipe metrics for the recipe containing the new jobs
        self.assertListEqual(update_metrics_msg._recipe_ids, [recipe.id])

    def test_execute_recipe_superseded(self):
        """Tests calling CreateJobs.execute() successfully for jobs within a recipe that supersedes another recipe"""

        from batch.test import utils as batch_test_utils
        from recipe.models import RecipeNode
        from recipe.test import utils as recipe_test_utils
        from storage.test import utils as storage_test_utils

        event = trigger_test_utils.create_trigger_event()
        job_type_1 = job_test_utils.create_seed_job_type()
        job_type_2 = job_test_utils.create_seed_job_type()

        definition = {
            'version': '7',
            'input': {
                'files': [{'name': 'INPUT_IMAGE', 'media_types': ['image/png'], 'required': True, 'multiple': False}],
                'json': []},
            'nodes': {
                'node_1': {
                    'dependencies': [],
                    'input': {'INPUT_IMAGE': {'type': 'recipe', 'input': 'INPUT_IMAGE'}},
                    'node_type': {
                        'node_type': 'job',
                        'job_type_name': job_type_1.name,
                        'job_type_version': job_type_1.version,
                        'job_type_revision': job_type_1.revision_num
                    }
                },
                'node_2': {
                    'dependencies': [],
                    'input': {'INPUT_IMAGE': {'type': 'recipe', 'input': 'INPUT_IMAGE'}},
                    'node_type': {
                        'node_type': 'job',
                        'job_type_name': job_type_2.name,
                        'job_type_version': job_type_2.version,
                        'job_type_revision': job_type_2.revision_num
                    }
                }
            }
        }
        rtype = recipe_test_utils.create_recipe_type_v6(definition=definition)
        batch = batch_test_utils.create_batch(recipe_type=rtype)

        workspace = storage_test_utils.create_workspace()
        file1 = storage_test_utils.create_file(file_name='input_a.PNG', file_type='SOURCE', media_type='image/png',
                                               file_size=10, data_type_tags=['type'], file_path='the_path',
                                               workspace=workspace)
        recipe_data = {'version': '6', 'files': {'INPUT_IMAGE': [file1.id]}, 'json': {}}
        superseded_recipe = recipe_test_utils.create_recipe(event=event, recipe_type=rtype, batch=batch, input=recipe_data)

        superseded_job_1 = job_test_utils.create_job(job_type=job_type_1, is_superseded=True)
        superseded_job_2 = job_test_utils.create_job(job_type=job_type_2, is_superseded=True)
        recipe_test_utils.create_recipe_node(recipe=superseded_recipe, node_name='node_1', job=superseded_job_1,
                                             save=True)
        recipe_test_utils.create_recipe_node(recipe=superseded_recipe, node_name='node_2', job=superseded_job_2,
                                             save=True)
        recipe = recipe_test_utils.create_recipe(recipe_type=superseded_recipe.recipe_type,
                                                 superseded_recipe=superseded_recipe, event=event, batch=batch,
                                                 input=recipe_data)
        recipe_jobs = [RecipeJob(job_type_1.name, job_type_1.version, job_type_1.revision_num, 'node_1', False),
                       RecipeJob(job_type_2.name, job_type_2.version, job_type_2.revision_num, 'node_2', True)]

        # Create and execute message
        message = create_jobs_messages_for_recipe(recipe, recipe_jobs)[0]
        result = message.execute()
        self.assertTrue(result)

        self.assertEqual(Job.objects.filter(recipe_id=recipe.id, event_id=recipe.event_id).count(), 2)
        recipe_nodes = RecipeNode.objects.filter(recipe_id=recipe.id)
        self.assertEqual(len(recipe_nodes), 2)
        for recipe_node in recipe_nodes:
            jobs = Job.objects.filter(recipe_node=recipe_node)
            self.assertEqual(len(jobs), 1)
            if recipe_node.node_name == 'node_1':
                job_1 = jobs[0]
                self.assertEqual(job_1.job_type_id, job_type_1.id)
                self.assertEqual(job_1.event_id, event.id)
                self.assertEqual(job_1.batch_id, batch.id)
                self.assertEqual(job_1.recipe_id, recipe.id)
                self.assertEqual(job_1.root_recipe_id, superseded_recipe.id)
                self.assertEqual(job_1.superseded_job_id, superseded_job_1.id)
                self.assertEqual(job_1.root_superseded_job_id, superseded_job_1.id)
            elif recipe_node.node_name == 'node_2':
                job_2 = jobs[0]
                self.assertEqual(job_2.job_type_id, job_type_2.id)
                self.assertEqual(job_2.event_id, event.id)
                self.assertEqual(job_2.batch_id, batch.id)
                self.assertEqual(job_2.recipe_id, recipe.id)
                self.assertEqual(job_2.root_recipe_id, superseded_recipe.id)
                self.assertEqual(job_2.superseded_job_id, superseded_job_2.id)
                self.assertEqual(job_2.root_superseded_job_id, superseded_job_2.id)
            else:
                self.fail('%s is the wrong node name' % recipe_node.node_name)

        # Should be two messages, one for processing job input and one for updating metrics for the recipe
        self.assertEqual(len(message.new_messages), 1)
        update_metrics_msg = None
        if message.new_messages[0].type == 'update_recipe_metrics':
            update_metrics_msg = message.new_messages[0]
        self.assertIsNotNone(update_metrics_msg)
        # Check message to update recipe metrics for the recipe containing the new jobs
        self.assertListEqual(update_metrics_msg._recipe_ids, [recipe.id])

        # Test executing message again
        message_json_dict = message.to_json()
        message = CreateJobs.from_json(message_json_dict)
        result = message.execute()
        self.assertTrue(result)

        self.assertEqual(Job.objects.filter(recipe_id=recipe.id, event_id=recipe.event_id).count(), 2)
        recipe_nodes = RecipeNode.objects.filter(recipe_id=recipe.id)
        self.assertEqual(len(recipe_nodes), 2)
        for recipe_node in recipe_nodes:

            jobs = Job.objects.filter(recipe_node=recipe_node)
            self.assertEqual(len(jobs), 1)
            if recipe_node.node_name == 'node_1':
                job_1 = jobs[0]
                self.assertEqual(job_1.job_type_id, job_type_1.id)
                self.assertEqual(job_1.event_id, event.id)
                self.assertEqual(job_1.batch_id, batch.id)
                self.assertEqual(job_1.recipe_id, recipe.id)
                self.assertEqual(job_1.root_recipe_id, superseded_recipe.id)
                self.assertEqual(job_1.superseded_job_id, superseded_job_1.id)
                self.assertEqual(job_1.root_superseded_job_id, superseded_job_1.id)
            elif recipe_node.node_name == 'node_2':
                job_2 = jobs[0]
                self.assertEqual(job_2.job_type_id, job_type_2.id)
                self.assertEqual(job_2.event_id, event.id)
                self.assertEqual(job_2.batch_id, batch.id)
                self.assertEqual(job_2.recipe_id, recipe.id)
                self.assertEqual(job_2.root_recipe_id, superseded_recipe.id)
                self.assertEqual(job_2.superseded_job_id, superseded_job_2.id)
                self.assertEqual(job_2.root_superseded_job_id, superseded_job_2.id)
            else:
                self.fail('%s is the wrong node name' % recipe_node.node_name)

        # Should be two messages, one for processing job input and one for updating metrics for the recipe
        self.assertEqual(len(message.new_messages), 1)
        update_metrics_msg = None
        if message.new_messages[0].type == 'update_recipe_metrics':
            update_metrics_msg = message.new_messages[0]
        self.assertIsNotNone(update_metrics_msg)
        # Check message to update recipe metrics for the recipe containing the new jobs
        self.assertListEqual(update_metrics_msg._recipe_ids, [recipe.id])
