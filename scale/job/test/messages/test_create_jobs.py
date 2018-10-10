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

        # Check for process_job_input message
        self.assertEqual(len(new_message.new_messages), 1)
        msg = new_message.new_messages[0]
        self.assertEqual(msg.type, 'process_job_input')

    def test_json_recipe(self):
        """Tests converting a CreateJobs message to and from JSON when creating jobs for a recipe"""

        from batch.test import utils as batch_test_utils
        from recipe.models import RecipeNode
        from recipe.test import utils as recipe_test_utils

        batch = batch_test_utils.create_batch()
        event = trigger_test_utils.create_trigger_event()
        job_type_1 = job_test_utils.create_seed_job_type()
        job_type_2 = job_test_utils.create_seed_job_type()
        recipe = recipe_test_utils.create_recipe(event=event, batch=batch)
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
        recipe_nodes = RecipeNode.objects.select_related('job').filter(recipe_id=recipe.id)
        self.assertEqual(len(recipe_nodes), 2)
        for recipe_node in recipe_nodes:
            if recipe_node.node_name == 'node_1':
                job_1 = recipe_node.job
                self.assertEqual(job_1.job_type_id, job_type_1.id)
                self.assertEqual(job_1.event_id, event.id)
                self.assertEqual(job_1.batch_id, batch.id)
            elif recipe_node.node_name == 'node_2':
                job_2 = recipe_node.job
                self.assertEqual(job_2.job_type_id, job_type_2.id)
                self.assertEqual(job_2.event_id, event.id)
                self.assertEqual(job_2.batch_id, batch.id)
            else:
                self.fail('%s is the worng node name' % recipe_node.node_name)

        # Should be two messages, one for processing job input and one for updating metrics for the recipe
        self.assertEqual(len(new_message.new_messages), 2)
        process_job_input_msg = None
        update_metrics_msg = None
        for msg in new_message.new_messages:
            if msg.type == 'process_job_input':
                process_job_input_msg = msg
            elif msg.type == 'update_recipe_metrics':
                update_metrics_msg = msg
        self.assertIsNotNone(process_job_input_msg)
        self.assertIsNotNone(update_metrics_msg)
        # Check message to process job input for new job 2
        self.assertEqual(process_job_input_msg.job_id, job_2.id)
        # Check message to update recipe metrics for the recipe containing the new jobs
        self.assertListEqual(update_metrics_msg._recipe_ids, [recipe.id])

    def test_json_recipe_superseded(self):
        """Tests converting a CreateJobs message to and from JSON when creating jobs for a recipe that supersedes
        another recipe
        """

        from batch.test import utils as batch_test_utils
        from recipe.models import RecipeNode
        from recipe.test import utils as recipe_test_utils

        batch = batch_test_utils.create_batch()
        event = trigger_test_utils.create_trigger_event()
        job_type_1 = job_test_utils.create_seed_job_type()
        job_type_2 = job_test_utils.create_seed_job_type()
        superseded_recipe = recipe_test_utils.create_recipe()
        superseded_job_1 = job_test_utils.create_job(job_type=job_type_1, is_superseded=True)
        superseded_job_2 = job_test_utils.create_job(job_type=job_type_2, is_superseded=True)
        recipe_test_utils.create_recipe_node(recipe=superseded_recipe, node_name='node_1', job=superseded_job_1,
                                             save=True)
        recipe_test_utils.create_recipe_node(recipe=superseded_recipe, node_name='node_2', job=superseded_job_2,
                                             save=True)
        recipe = recipe_test_utils.create_recipe(recipe_type=superseded_recipe.recipe_type,
                                                 superseded_recipe=superseded_recipe, event=event, batch=batch)
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
        recipe_nodes = RecipeNode.objects.select_related('job').filter(recipe_id=recipe.id)
        self.assertEqual(len(recipe_nodes), 2)
        for recipe_node in recipe_nodes:
            if recipe_node.node_name == 'node_1':
                job_1 = recipe_node.job
                self.assertEqual(job_1.job_type_id, job_type_1.id)
                self.assertEqual(job_1.event_id, event.id)
                self.assertEqual(job_1.batch_id, batch.id)
                self.assertEqual(job_1.recipe_id, recipe.id)
                self.assertEqual(job_1.root_recipe_id, superseded_recipe.id)
                self.assertEqual(job_1.superseded_job_id, superseded_job_1.id)
                self.assertEqual(job_1.root_superseded_job_id, superseded_job_1.id)
            elif recipe_node.node_name == 'node_2':
                job_2 = recipe_node.job
                self.assertEqual(job_2.job_type_id, job_type_2.id)
                self.assertEqual(job_2.event_id, event.id)
                self.assertEqual(job_2.batch_id, batch.id)
                self.assertEqual(job_2.recipe_id, recipe.id)
                self.assertEqual(job_2.root_recipe_id, superseded_recipe.id)
                self.assertEqual(job_2.superseded_job_id, superseded_job_2.id)
                self.assertEqual(job_2.root_superseded_job_id, superseded_job_2.id)
            else:
                self.fail('%s is the worng node name' % recipe_node.node_name)

        # Should be two messages, one for processing job input and one for updating metrics for the recipe
        self.assertEqual(len(new_message.new_messages), 2)
        process_job_input_msg = None
        update_metrics_msg = None
        for msg in new_message.new_messages:
            if msg.type == 'process_job_input':
                process_job_input_msg = msg
            elif msg.type == 'update_recipe_metrics':
                update_metrics_msg = msg
        self.assertIsNotNone(process_job_input_msg)
        self.assertIsNotNone(update_metrics_msg)
        # Check message to process job input for new job 2
        self.assertEqual(process_job_input_msg.job_id, job_2.id)
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

        # Check for process_job_input message
        self.assertEqual(len(message.new_messages), 1)
        msg = message.new_messages[0]
        self.assertEqual(msg.type, 'process_job_input')

        # Test executing message again
        message_json_dict = message.to_json()
        message = CreateJobs.from_json(message_json_dict)
        result = message.execute()
        self.assertTrue(result)

        # Check that a second job is not created
        self.assertEqual(Job.objects.filter(job_type_id=job_type.id, event_id=event.id).count(), 1)

        # Check for process_job_input message
        self.assertEqual(len(message.new_messages), 1)
        msg = message.new_messages[0]
        self.assertEqual(msg.type, 'process_job_input')

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

        batch = batch_test_utils.create_batch()
        event = trigger_test_utils.create_trigger_event()
        job_type_1 = job_test_utils.create_seed_job_type()
        job_type_2 = job_test_utils.create_seed_job_type()
        recipe = recipe_test_utils.create_recipe(event=event, batch=batch)
        recipe_jobs = [RecipeJob(job_type_1.name, job_type_1.version, job_type_1.revision_num, 'node_1', False),
                       RecipeJob(job_type_2.name, job_type_2.version, job_type_2.revision_num, 'node_2', True)]
        recipe = recipe_test_utils.create_recipe(event=event, batch=batch)

        # Create and execute message
        message = create_jobs_messages_for_recipe(recipe, recipe_jobs)[0]
        result = message.execute()
        self.assertTrue(result)

        self.assertEqual(Job.objects.filter(recipe_id=recipe.id, event_id=recipe.event_id).count(), 2)
        recipe_nodes = RecipeNode.objects.select_related('job').filter(recipe_id=recipe.id)
        self.assertEqual(len(recipe_nodes), 2)
        for recipe_node in recipe_nodes:
            if recipe_node.node_name == 'node_1':
                job_1 = recipe_node.job
                self.assertEqual(job_1.job_type_id, job_type_1.id)
                self.assertEqual(job_1.event_id, event.id)
                self.assertEqual(job_1.batch_id, batch.id)
            elif recipe_node.node_name == 'node_2':
                job_2 = recipe_node.job
                self.assertEqual(job_2.job_type_id, job_type_2.id)
                self.assertEqual(job_2.event_id, event.id)
                self.assertEqual(job_2.batch_id, batch.id)
            else:
                self.fail('%s is the worng node name' % recipe_node.node_name)

        # Should be two messages, one for processing job input and one for updating metrics for the recipe
        self.assertEqual(len(message.new_messages), 2)
        process_job_input_msg = None
        update_metrics_msg = None
        for msg in message.new_messages:
            if msg.type == 'process_job_input':
                process_job_input_msg = msg
            elif msg.type == 'update_recipe_metrics':
                update_metrics_msg = msg
        self.assertIsNotNone(process_job_input_msg)
        self.assertIsNotNone(update_metrics_msg)
        # Check message to process job input for new job 2
        self.assertEqual(process_job_input_msg.job_id, job_2.id)
        # Check message to update recipe metrics for the recipe containing the new jobs
        self.assertListEqual(update_metrics_msg._recipe_ids, [recipe.id])

        # Test executing message again
        message_json_dict = message.to_json()
        message = CreateJobs.from_json(message_json_dict)
        result = message.execute()
        self.assertTrue(result)

        self.assertEqual(Job.objects.filter(recipe_id=recipe.id, event_id=recipe.event_id).count(), 2)
        recipe_nodes = RecipeNode.objects.select_related('job').filter(recipe_id=recipe.id)
        self.assertEqual(len(recipe_nodes), 2)
        for recipe_node in recipe_nodes:
            if recipe_node.node_name == 'node_1':
                job_1 = recipe_node.job
                self.assertEqual(job_1.job_type_id, job_type_1.id)
                self.assertEqual(job_1.event_id, event.id)
                self.assertEqual(job_1.batch_id, batch.id)
            elif recipe_node.node_name == 'node_2':
                job_2 = recipe_node.job
                self.assertEqual(job_2.job_type_id, job_type_2.id)
                self.assertEqual(job_2.event_id, event.id)
                self.assertEqual(job_2.batch_id, batch.id)
            else:
                self.fail('%s is the worng node name' % recipe_node.node_name)

        # Should be two messages, one for processing job input and one for updating metrics for the recipe
        self.assertEqual(len(message.new_messages), 2)
        process_job_input_msg = None
        update_metrics_msg = None
        for msg in message.new_messages:
            if msg.type == 'process_job_input':
                process_job_input_msg = msg
            elif msg.type == 'update_recipe_metrics':
                update_metrics_msg = msg
        self.assertIsNotNone(process_job_input_msg)
        self.assertIsNotNone(update_metrics_msg)
        # Check message to process job input for new job 2
        self.assertEqual(process_job_input_msg.job_id, job_2.id)
        # Check message to update recipe metrics for the recipe containing the new jobs
        self.assertListEqual(update_metrics_msg._recipe_ids, [recipe.id])

    def test_execute_recipe_superseded(self):
        """Tests calling CreateJobs.execute() successfully for jobs within a recipe that supersedes another recipe"""

        from batch.test import utils as batch_test_utils
        from recipe.models import RecipeNode
        from recipe.test import utils as recipe_test_utils

        batch = batch_test_utils.create_batch()
        event = trigger_test_utils.create_trigger_event()
        job_type_1 = job_test_utils.create_seed_job_type()
        job_type_2 = job_test_utils.create_seed_job_type()
        superseded_recipe = recipe_test_utils.create_recipe()
        superseded_job_1 = job_test_utils.create_job(job_type=job_type_1, is_superseded=True)
        superseded_job_2 = job_test_utils.create_job(job_type=job_type_2, is_superseded=True)
        recipe_test_utils.create_recipe_node(recipe=superseded_recipe, node_name='node_1', job=superseded_job_1,
                                             save=True)
        recipe_test_utils.create_recipe_node(recipe=superseded_recipe, node_name='node_2', job=superseded_job_2,
                                             save=True)
        recipe = recipe_test_utils.create_recipe(recipe_type=superseded_recipe.recipe_type,
                                                 superseded_recipe=superseded_recipe, event=event, batch=batch)
        recipe_jobs = [RecipeJob(job_type_1.name, job_type_1.version, job_type_1.revision_num, 'node_1', False),
                       RecipeJob(job_type_2.name, job_type_2.version, job_type_2.revision_num, 'node_2', True)]

        # Create and execute message
        message = create_jobs_messages_for_recipe(recipe, recipe_jobs)[0]
        result = message.execute()
        self.assertTrue(result)

        self.assertEqual(Job.objects.filter(recipe_id=recipe.id, event_id=recipe.event_id).count(), 2)
        recipe_nodes = RecipeNode.objects.select_related('job').filter(recipe_id=recipe.id)
        self.assertEqual(len(recipe_nodes), 2)
        for recipe_node in recipe_nodes:
            if recipe_node.node_name == 'node_1':
                job_1 = recipe_node.job
                self.assertEqual(job_1.job_type_id, job_type_1.id)
                self.assertEqual(job_1.event_id, event.id)
                self.assertEqual(job_1.batch_id, batch.id)
                self.assertEqual(job_1.recipe_id, recipe.id)
                self.assertEqual(job_1.root_recipe_id, superseded_recipe.id)
                self.assertEqual(job_1.superseded_job_id, superseded_job_1.id)
                self.assertEqual(job_1.root_superseded_job_id, superseded_job_1.id)
            elif recipe_node.node_name == 'node_2':
                job_2 = recipe_node.job
                self.assertEqual(job_2.job_type_id, job_type_2.id)
                self.assertEqual(job_2.event_id, event.id)
                self.assertEqual(job_2.batch_id, batch.id)
                self.assertEqual(job_2.recipe_id, recipe.id)
                self.assertEqual(job_2.root_recipe_id, superseded_recipe.id)
                self.assertEqual(job_2.superseded_job_id, superseded_job_2.id)
                self.assertEqual(job_2.root_superseded_job_id, superseded_job_2.id)
            else:
                self.fail('%s is the worng node name' % recipe_node.node_name)

        # Should be two messages, one for processing job input and one for updating metrics for the recipe
        self.assertEqual(len(message.new_messages), 2)
        process_job_input_msg = None
        update_metrics_msg = None
        for msg in message.new_messages:
            if msg.type == 'process_job_input':
                process_job_input_msg = msg
            elif msg.type == 'update_recipe_metrics':
                update_metrics_msg = msg
        self.assertIsNotNone(process_job_input_msg)
        self.assertIsNotNone(update_metrics_msg)
        # Check message to process job input for new job 2
        self.assertEqual(process_job_input_msg.job_id, job_2.id)
        # Check message to update recipe metrics for the recipe containing the new jobs
        self.assertListEqual(update_metrics_msg._recipe_ids, [recipe.id])

        # Test executing message again
        message_json_dict = message.to_json()
        message = CreateJobs.from_json(message_json_dict)
        result = message.execute()
        self.assertTrue(result)

        self.assertEqual(Job.objects.filter(recipe_id=recipe.id, event_id=recipe.event_id).count(), 2)
        recipe_nodes = RecipeNode.objects.select_related('job').filter(recipe_id=recipe.id)
        self.assertEqual(len(recipe_nodes), 2)
        for recipe_node in recipe_nodes:
            if recipe_node.node_name == 'node_1':
                job_1 = recipe_node.job
                self.assertEqual(job_1.job_type_id, job_type_1.id)
                self.assertEqual(job_1.event_id, event.id)
                self.assertEqual(job_1.batch_id, batch.id)
                self.assertEqual(job_1.recipe_id, recipe.id)
                self.assertEqual(job_1.root_recipe_id, superseded_recipe.id)
                self.assertEqual(job_1.superseded_job_id, superseded_job_1.id)
                self.assertEqual(job_1.root_superseded_job_id, superseded_job_1.id)
            elif recipe_node.node_name == 'node_2':
                job_2 = recipe_node.job
                self.assertEqual(job_2.job_type_id, job_type_2.id)
                self.assertEqual(job_2.event_id, event.id)
                self.assertEqual(job_2.batch_id, batch.id)
                self.assertEqual(job_2.recipe_id, recipe.id)
                self.assertEqual(job_2.root_recipe_id, superseded_recipe.id)
                self.assertEqual(job_2.superseded_job_id, superseded_job_2.id)
                self.assertEqual(job_2.root_superseded_job_id, superseded_job_2.id)
            else:
                self.fail('%s is the worng node name' % recipe_node.node_name)

        # Should be two messages, one for processing job input and one for updating metrics for the recipe
        self.assertEqual(len(message.new_messages), 2)
        process_job_input_msg = None
        update_metrics_msg = None
        for msg in message.new_messages:
            if msg.type == 'process_job_input':
                process_job_input_msg = msg
            elif msg.type == 'update_recipe_metrics':
                update_metrics_msg = msg
        self.assertIsNotNone(process_job_input_msg)
        self.assertIsNotNone(update_metrics_msg)
        # Check message to process job input for new job 2
        self.assertEqual(process_job_input_msg.job_id, job_2.id)
        # Check message to update recipe metrics for the recipe containing the new jobs
        self.assertListEqual(update_metrics_msg._recipe_ids, [recipe.id])
