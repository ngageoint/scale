from __future__ import unicode_literals

import datetime

import django
from django.test import TransactionTestCase
from django.utils.timezone import now

from job.configuration.results.job_results import JobResults
from job.messages.completed_jobs import CompletedJob, CompletedJobs
from job.models import Job
from job.test import utils as job_test_utils


class TestCompletedJobs(TransactionTestCase):

    def setUp(self):
        django.setup()

    def test_json(self):
        """Tests coverting a CompletedJobs message to and from JSON"""

        job_1 = job_test_utils.create_job(num_exes=0, status='QUEUED')
        job_test_utils.create_job_exe(job=job_1)
        job_2 = job_test_utils.create_job(num_exes=0, status='RUNNING')
        job_test_utils.create_job_exe(job=job_2)
        job_3 = job_test_utils.create_job(num_exes=0, status='PENDING')
        job_ids = [job_1.id, job_2.id, job_3.id]

        from recipe.test import utils as recipe_test_utils
        recipe_1 = recipe_test_utils.create_recipe()
        recipe_test_utils.create_recipe_job(recipe=recipe_1, job=job_2)

        when_ended = now()

        # Add jobs to message
        message = CompletedJobs()
        message.ended = when_ended
        if message.can_fit_more():
            message.add_completed_job(CompletedJob(job_1.id, job_1.num_exes))
        if message.can_fit_more():
            message.add_completed_job(CompletedJob(job_2.id, job_2.num_exes))
        if message.can_fit_more():
            message.add_completed_job(CompletedJob(job_3.id, job_3.num_exes))

        # Convert message to JSON and back, and then execute
        message_json_dict = message.to_json()
        new_message = CompletedJobs.from_json(message_json_dict)
        result = new_message.execute()

        self.assertTrue(result)
        jobs = Job.objects.filter(id__in=job_ids).order_by('id')
        # Job 1 should be completed
        self.assertEqual(jobs[0].status, 'COMPLETED')
        self.assertEqual(jobs[0].num_exes, 1)
        self.assertEqual(jobs[0].ended, when_ended)
        # Job 2 should be completed
        self.assertEqual(jobs[1].status, 'COMPLETED')
        self.assertEqual(jobs[1].num_exes, 1)
        self.assertEqual(jobs[1].ended, when_ended)
        # Job 3 should ignore update
        self.assertEqual(jobs[2].status, 'PENDING')
        self.assertEqual(jobs[2].num_exes, 0)

    def test_execute(self):
        """Tests calling CompletedJobs.execute() successfully"""

        from recipe.test import utils as recipe_test_utils
        recipe_1 = recipe_test_utils.create_recipe()

        job_1 = job_test_utils.create_job(num_exes=0, status='QUEUED')
        job_test_utils.create_job_exe(job=job_1)
        job_2 = job_test_utils.create_job(num_exes=0, status='RUNNING', recipe=recipe_1)
        job_test_utils.create_job_exe(job=job_2, output=JobResults())
        job_3 = job_test_utils.create_job(num_exes=0, status='PENDING')
        job_ids = [job_1.id, job_2.id, job_3.id]

        recipe_test_utils.create_recipe_job(recipe=recipe_1, job=job_2)

        when_ended = now()

        # Add jobs to message
        message = CompletedJobs()
        message.ended = when_ended
        if message.can_fit_more():
            message.add_completed_job(CompletedJob(job_1.id, job_1.num_exes))
        if message.can_fit_more():
            message.add_completed_job(CompletedJob(job_2.id, job_2.num_exes))
        if message.can_fit_more():
            message.add_completed_job(CompletedJob(job_3.id, job_3.num_exes))

        # Execute message
        result = message.execute()
        self.assertTrue(result)

        from recipe.diff.forced_nodes import ForcedNodes
        from recipe.diff.json.forced_nodes_v6 import convert_forced_nodes_to_v6
        forced_nodes = ForcedNodes()
        forced_nodes.set_all_nodes()
        forced_nodes_dict = convert_forced_nodes_to_v6(forced_nodes).get_dict()

        jobs = Job.objects.filter(id__in=job_ids).order_by('id')
        self.assertEqual(len(message.new_messages), 3)
        update_recipe_metrics_msg = None
        update_recipe_msg = None
        publish_job_msg = None
        for msg in message.new_messages:
            if msg.type == 'update_recipe':
                update_recipe_msg = msg
            elif msg.type == 'publish_job':
                publish_job_msg = msg
            elif msg.type == 'update_recipe_metrics':
                update_recipe_metrics_msg = msg
        self.assertIsNotNone(update_recipe_msg)
        self.assertIsNotNone(publish_job_msg)
        self.assertIsNotNone(update_recipe_metrics_msg)
        self.assertEqual(publish_job_msg.job_id, job_2.id)

        # Job 1 should be completed
        self.assertEqual(jobs[0].status, 'COMPLETED')
        self.assertEqual(jobs[0].num_exes, 1)
        self.assertEqual(jobs[0].ended, when_ended)
        # Job 2 should be completed and has output, so should be in update_recipe message
        self.assertEqual(jobs[1].status, 'COMPLETED')
        self.assertEqual(jobs[1].num_exes, 1)
        self.assertEqual(jobs[1].ended, when_ended)
        self.assertEqual(update_recipe_msg.root_recipe_id, recipe_1.id)
        self.assertDictEqual(convert_forced_nodes_to_v6(update_recipe_msg.forced_nodes).get_dict(), forced_nodes_dict)
        # Job 3 should ignore update
        self.assertEqual(jobs[2].status, 'PENDING')
        self.assertEqual(jobs[2].num_exes, 0)

        # Test executing message again
        new_ended = when_ended + datetime.timedelta(minutes=5)
        message_json_dict = message.to_json()
        message = CompletedJobs.from_json(message_json_dict)
        message.ended = new_ended
        result = message.execute()
        self.assertTrue(result)

        # Should have the same messages as before
        jobs = Job.objects.filter(id__in=job_ids).order_by('id')
        self.assertEqual(len(message.new_messages), 3)
        update_recipe_metrics_msg = None
        update_recipe_msg = None
        publish_job_msg = None
        for msg in message.new_messages:
            if msg.type == 'update_recipe':
                update_recipe_msg = msg
            elif msg.type == 'publish_job':
                publish_job_msg = msg
            elif msg.type == 'update_recipe_metrics':
                update_recipe_metrics_msg = msg
        self.assertIsNotNone(update_recipe_msg)
        self.assertIsNotNone(publish_job_msg)
        self.assertIsNotNone(update_recipe_metrics_msg)
        self.assertEqual(publish_job_msg.job_id, job_2.id)

        # Job 1 should be completed
        self.assertEqual(jobs[0].status, 'COMPLETED')
        self.assertEqual(jobs[0].num_exes, 1)
        self.assertEqual(jobs[0].ended, when_ended)
        # Job 2 should be completed and has output, so should be in update_recipe message
        self.assertEqual(jobs[1].status, 'COMPLETED')
        self.assertEqual(jobs[1].num_exes, 1)
        self.assertEqual(jobs[1].ended, when_ended)
        self.assertEqual(update_recipe_msg.root_recipe_id, recipe_1.id)
        self.assertDictEqual(convert_forced_nodes_to_v6(update_recipe_msg.forced_nodes).get_dict(), forced_nodes_dict)
        # Job 3 should ignore update
        self.assertEqual(jobs[2].status, 'PENDING')
        self.assertEqual(jobs[2].num_exes, 0)
