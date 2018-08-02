from __future__ import unicode_literals

import django
from django.test import TransactionTestCase

from data.data.data import Data
from data.data.json.data_v6 import convert_data_to_v6_json
from job.messages.create_jobs import create_jobs_message, create_jobs_message_for_recipe, CreateJobs
from job.models import Job
from job.test import utils as job_test_utils
from trigger.test import utils as trigger_test_utils


class TestCreateJobs(TransactionTestCase):

    def setUp(self):
        django.setup()

    def test_json_no_recipe(self):
        """Tests converting a CreateJobs message (without a recipe) to and from JSON"""

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
        data_dict = convert_data_to_v6_json(Data()).get_dict()
        count = 10

        # Create message
        message = create_jobs_message(job_type.name, job_type.version, job_type.revision_num, event.id, count=count,
                                      input_data_dict=data_dict)

        # Convert message to JSON and back, and then execute
        message_json_dict = message.to_json()
        new_message = CreateJobs.from_json(message_json_dict)
        result = new_message.execute()

        self.assertTrue(result)
        self.assertEqual(Job.objects.filter(job_type_id=job_type.id, event_id=event.id).count(), count)

        # Check for process_job_input messages
        self.assertEqual(len(new_message.new_messages), count)
        for msg in new_message.new_messages:
            self.assertEqual(msg.type, 'process_job_input')

    def test_json_recipe(self):
        """Tests converting a CreateJobs message (with a recipe) to and from JSON"""

        from recipe.models import RecipeNode
        from recipe.test import utils as recipe_test_utils

        job_type = job_test_utils.create_seed_job_type()
        recipe = recipe_test_utils.create_recipe()
        node_name = 'recipe_node'
        count = 7

        # Create message
        message = create_jobs_message_for_recipe(recipe, node_name, job_type.name, job_type.version,
                                                 job_type.revision_num, count=count, process_input=True)

        # Convert message to JSON and back, and then execute
        message_json_dict = message.to_json()
        new_message = CreateJobs.from_json(message_json_dict)
        result = new_message.execute()

        self.assertTrue(result)
        check_count = Job.objects.filter(job_type_id=job_type.id, recipe_id=recipe.id, event_id=recipe.event_id).count()
        self.assertEqual(check_count, count)
        self.assertEqual(RecipeNode.objects.filter(recipe_id=recipe.id, node_name=node_name).count(), count)

        # Check for process_job_input messages (because process_input=True)
        self.assertEqual(len(new_message.new_messages), count)
        for msg in new_message.new_messages:
            self.assertEqual(msg.type, 'process_job_input')

    def test_execute_invalid_data(self):
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
        data_dict = convert_data_to_v6_json(Data()).get_dict()

        # Create and execute message
        message = create_jobs_message(job_type.name, job_type.version, job_type.revision_num, event.id, count=10,
                                      input_data_dict=data_dict)
        result = message.execute()

        self.assertTrue(result)
        self.assertEqual(Job.objects.filter(job_type_id=job_type.id, event_id=event.id).count(), 0)

        # Should be no new messages
        self.assertEqual(len(message.new_messages), 0)

    def test_execute_with_recipe(self):
        """Tests calling CreateJobs.execute() successfully with a recipe that supersedes another recipe"""

        from batch.test import utils as batch_test_utils
        from recipe.models import RecipeNode
        from recipe.test import utils as recipe_test_utils

        job_type = job_test_utils.create_seed_job_type()
        recipe_type = recipe_test_utils.create_recipe_type()
        superseded_recipe = recipe_test_utils.create_recipe(recipe_type=recipe_type, is_superseded=True)
        node_name = 'recipe_node'
        superseded_job = job_test_utils.create_job(job_type=job_type, is_superseded=True)
        recipe_test_utils.create_recipe_node(recipe=superseded_recipe, node_name=node_name, job=superseded_job,
                                             save=True)
        batch = batch_test_utils.create_batch()
        recipe = recipe_test_utils.create_recipe(recipe_type=recipe_type, superseded_recipe=superseded_recipe,
                                                 batch=batch)

        # Create and execute message
        message = create_jobs_message_for_recipe(recipe, node_name, job_type.name, job_type.version,
                                                 job_type.revision_num, process_input=True)
        result = message.execute()
        self.assertTrue(result)

        new_job = Job.objects.get(job_type_id=job_type.id, recipe_id=recipe.id)
        self.assertEqual(new_job.event_id, recipe.event_id)
        self.assertEqual(new_job.recipe_id, recipe.id)
        self.assertEqual(new_job.root_recipe_id, superseded_recipe.id)
        self.assertEqual(new_job.root_superseded_job_id, superseded_job.id)
        self.assertEqual(new_job.superseded_job_id, superseded_job.id)
        self.assertEqual(new_job.batch_id, batch.id)
        node_count = RecipeNode.objects.filter(recipe_id=recipe.id, node_name=node_name, job_id=new_job.id).count()
        self.assertEqual(node_count, 1)

        # Check for process_job_input message (because process_input=True)
        self.assertEqual(len(message.new_messages), 1)
        self.assertEqual(message.new_messages[0].type, 'process_job_input')
        self.assertEqual(message.new_messages[0].job_id, new_job.id)

        # Test executing message again
        message.new_messages = []
        result = message.execute()
        self.assertTrue(result)

        # Make sure a new job is not created
        self.assertEqual(Job.objects.filter(recipe_id=recipe.id).count(), 1)
        self.assertEqual(RecipeNode.objects.filter(recipe_id=recipe.id, node_name=node_name).count(), 1)

        # Check for same process_job_input message
        self.assertEqual(len(message.new_messages), 1)
        self.assertEqual(message.new_messages[0].type, 'process_job_input')
        self.assertEqual(message.new_messages[0].job_id, new_job.id)
