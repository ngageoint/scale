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

        # Create message
        message = create_jobs_message(job_type.name, job_type.version, job_type.revision_num, event.id, count=10,
                                      input_data_dict=data_dict)

        # Convert message to JSON and back, and then execute
        message_json_dict = message.to_json()
        new_message = CreateJobs.from_json(message_json_dict)
        result = new_message.execute()

        self.assertTrue(result)
        self.assertEqual(Job.objects.filter(job_type_id=job_type.id, event_id=event.id).count(), 10)

        # Check for process_job_input messages
        self.assertEqual(len(new_message.new_messages), 10)
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

    # def test_execute(self):
    #     """Tests calling CompletedJobs.execute() successfully"""

    #     job_1 = job_test_utils.create_job(num_exes=1, status='QUEUED')
    #     job_test_utils.create_job_exe(job=job_1)
    #     job_2 = job_test_utils.create_job(num_exes=1, status='RUNNING')
    #     job_test_utils.create_job_exe(job=job_2, output=JobResults())
    #     job_3 = job_test_utils.create_job(num_exes=0, status='PENDING')
    #     job_ids = [job_1.id, job_2.id, job_3.id]

    #     from recipe.test import utils as recipe_test_utils
    #     recipe_1 = recipe_test_utils.create_recipe()
    #     recipe_test_utils.create_recipe_job(recipe=recipe_1, job=job_2)

    #     when_ended = now()

    #     # Add jobs to message
    #     message = CompletedJobs()
    #     message.ended = when_ended
    #     if message.can_fit_more():
    #         message.add_completed_job(CompletedJob(job_1.id, job_1.num_exes))
    #     if message.can_fit_more():
    #         message.add_completed_job(CompletedJob(job_2.id, job_2.num_exes))
    #     if message.can_fit_more():
    #         message.add_completed_job(CompletedJob(job_3.id, job_3.num_exes))

    #     # Execute message
    #     result = message.execute()
    #     self.assertTrue(result)

    #     jobs = Job.objects.filter(id__in=job_ids).order_by('id')
    #     self.assertEqual(len(message.new_messages), 3)
    #     update_recipe_metrics_msg = None
    #     update_recipes_msg = None
    #     publish_job_msg = None
    #     for msg in message.new_messages:
    #         if msg.type == 'update_recipes':
    #             update_recipes_msg = msg
    #         elif msg.type == 'publish_job':
    #             publish_job_msg = msg
    #         elif msg.type == 'update_recipe_metrics':
    #             update_recipe_metrics_msg = msg
    #     self.assertIsNotNone(update_recipes_msg)
    #     self.assertIsNotNone(publish_job_msg)
    #     self.assertIsNotNone(update_recipe_metrics_msg)
    #     # Job 2 was only job both completed and with output
    #     self.assertEqual(len(update_recipes_msg._recipe_ids), 1)
    #     self.assertEqual(publish_job_msg.job_id, job_2.id)

    #     # Job 1 should be completed
    #     self.assertEqual(jobs[0].status, 'COMPLETED')
    #     self.assertEqual(jobs[0].num_exes, 1)
    #     self.assertEqual(jobs[0].ended, when_ended)
    #     # Job 2 should be completed and has output, so should be in update_recipes message
    #     self.assertEqual(jobs[1].status, 'COMPLETED')
    #     self.assertEqual(jobs[1].num_exes, 1)
    #     self.assertEqual(jobs[1].ended, when_ended)
    #     self.assertTrue(recipe_1.id in update_recipes_msg._recipe_ids)
    #     # Job 3 should ignore update
    #     self.assertEqual(jobs[2].status, 'PENDING')
    #     self.assertEqual(jobs[2].num_exes, 0)

    #     # Test executing message again
    #     new_ended = when_ended + datetime.timedelta(minutes=5)
    #     message_json_dict = message.to_json()
    #     message = CompletedJobs.from_json(message_json_dict)
    #     message.ended = new_ended
    #     result = message.execute()
    #     self.assertTrue(result)

    #     # Should have the same messages as before
    #     jobs = Job.objects.filter(id__in=job_ids).order_by('id')
    #     self.assertEqual(len(message.new_messages), 3)
    #     update_recipe_metrics_msg = None
    #     update_recipes_msg = None
    #     publish_job_msg = None
    #     for msg in message.new_messages:
    #         if msg.type == 'update_recipes':
    #             update_recipes_msg = msg
    #         elif msg.type == 'publish_job':
    #             publish_job_msg = msg
    #         elif msg.type == 'update_recipe_metrics':
    #             update_recipe_metrics_msg = msg
    #     self.assertIsNotNone(update_recipes_msg)
    #     self.assertIsNotNone(publish_job_msg)
    #     self.assertIsNotNone(update_recipe_metrics_msg)
    #     # Job 2 was only job both completed and with output
    #     self.assertEqual(len(update_recipes_msg._recipe_ids), 1)
    #     self.assertEqual(publish_job_msg.job_id, job_2.id)

    #     # Should have the same models as before
    #     self.assertEqual(jobs[0].status, 'COMPLETED')
    #     self.assertEqual(jobs[0].num_exes, 1)
    #     self.assertEqual(jobs[0].ended, when_ended)
    #     # Job 2 should be completed and has output, so should be in update_recipes message
    #     self.assertEqual(jobs[1].status, 'COMPLETED')
    #     self.assertEqual(jobs[1].num_exes, 1)
    #     self.assertEqual(jobs[1].ended, when_ended)
    #     self.assertTrue(recipe_1.id in update_recipes_msg._recipe_ids)
    #     # Job 3 should ignore update
    #     self.assertEqual(jobs[2].status, 'PENDING')
    #     self.assertEqual(jobs[2].num_exes, 0)
