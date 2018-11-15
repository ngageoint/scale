from __future__ import unicode_literals

import datetime

import django
from django.utils.timezone import now
from django.test import TransactionTestCase

from job.messages.uncancel_jobs import UncancelJobs
from job.models import Job
from job.test import utils as job_test_utils
from recipe.test import utils as recipe_test_utils


class TestUncancelJobs(TransactionTestCase):

    def setUp(self):
        django.setup()

    def test_json(self):
        """Tests coverting an UncancelJobs message to and from JSON"""

        old_when = now()
        when = old_when + datetime.timedelta(minutes=60)

        job_1 = job_test_utils.create_job(num_exes=0, status='PENDING', last_status_change=old_when)
        job_2 = job_test_utils.create_job(num_exes=0, status='CANCELED', last_status_change=old_when)
        job_3 = job_test_utils.create_job(num_exes=1, status='CANCELED', last_status_change=old_when)
        job_4 = job_test_utils.create_job(num_exes=1, status='FAILED', last_status_change=old_when)
        job_ids = [job_1.id, job_2.id, job_3.id, job_4.id]

        # Add jobs to message
        message = UncancelJobs()
        message.when = when
        if message.can_fit_more():
            message.add_job(job_1.id)
        if message.can_fit_more():
            message.add_job(job_2.id)
        if message.can_fit_more():
            message.add_job(job_3.id)
        if message.can_fit_more():
            message.add_job(job_4.id)

        # Convert message to JSON and back, and then execute
        message_json_dict = message.to_json()
        new_message = UncancelJobs.from_json(message_json_dict)
        result = new_message.execute()

        self.assertTrue(result)
        jobs = Job.objects.filter(id__in=job_ids).order_by('id')
        # Job 1 should not be updated because it was not CANCELED
        self.assertEqual(jobs[0].status, 'PENDING')
        self.assertEqual(jobs[0].last_status_change, old_when)
        # Job 2 should be uncanceled
        self.assertEqual(jobs[1].status, 'PENDING')
        self.assertEqual(jobs[1].last_status_change, when)
        # Job 3 should not be updated since it has already been queued
        self.assertEqual(jobs[2].status, 'CANCELED')
        self.assertEqual(jobs[2].last_status_change, old_when)
        # Job 4 should not be updated because it was not CANCELED
        self.assertEqual(jobs[3].status, 'FAILED')
        self.assertEqual(jobs[3].last_status_change, old_when)

    def test_execute(self):
        """Tests calling UncancelJobs.execute() successfully"""

        old_when = now()
        when = old_when + datetime.timedelta(minutes=60)
        recipe = recipe_test_utils.create_recipe()

        job_1 = job_test_utils.create_job(num_exes=0, status='PENDING', last_status_change=old_when)
        job_2 = job_test_utils.create_job(num_exes=0, status='CANCELED', last_status_change=old_when, recipe=recipe)
        job_3 = job_test_utils.create_job(num_exes=1, status='CANCELED', last_status_change=old_when)
        job_4 = job_test_utils.create_job(num_exes=1, status='FAILED', last_status_change=old_when)
        job_ids = [job_1.id, job_2.id, job_3.id, job_4.id]

        recipe_test_utils.create_recipe_job(recipe=recipe, job=job_2)

        # Add jobs to message
        message = UncancelJobs()
        message.when = when
        if message.can_fit_more():
            message.add_job(job_1.id)
        if message.can_fit_more():
            message.add_job(job_2.id)
        if message.can_fit_more():
            message.add_job(job_3.id)
        if message.can_fit_more():
            message.add_job(job_4.id)

        # Execute message
        result = message.execute()
        self.assertTrue(result)

        from recipe.diff.forced_nodes import ForcedNodes
        from recipe.diff.json.forced_nodes_v6 import convert_forced_nodes_to_v6
        forced_nodes = ForcedNodes()
        forced_nodes.set_all_nodes()
        forced_nodes_dict = convert_forced_nodes_to_v6(forced_nodes).get_dict()

        jobs = Job.objects.filter(id__in=job_ids).order_by('id')
        # Job 1 should not be updated because it was not CANCELED
        self.assertEqual(jobs[0].status, 'PENDING')
        self.assertEqual(jobs[0].last_status_change, old_when)
        # Job 2 should be uncanceled
        self.assertEqual(jobs[1].status, 'PENDING')
        self.assertEqual(jobs[1].last_status_change, when)
        # Job 3 should not be updated since it has already been queued
        self.assertEqual(jobs[2].status, 'CANCELED')
        self.assertEqual(jobs[2].last_status_change, old_when)
        # Job 4 should not be updated because it was not CANCELED
        self.assertEqual(jobs[3].status, 'FAILED')
        self.assertEqual(jobs[3].last_status_change, old_when)

        # Make sure update_recipe and update_recipe_metrics messages were created
        self.assertEqual(len(message.new_messages), 2)
        update_recipe_msg = None
        update_recipe_metrics_msg = None
        for msg in message.new_messages:
            if msg.type == 'update_recipe':
                update_recipe_msg = msg
            elif msg.type == 'update_recipe_metrics':
                update_recipe_metrics_msg = msg
        self.assertIsNotNone(update_recipe_msg)
        self.assertIsNotNone(update_recipe_metrics_msg)
        self.assertEqual(update_recipe_msg.root_recipe_id, recipe.id)
        self.assertDictEqual(convert_forced_nodes_to_v6(update_recipe_msg.forced_nodes).get_dict(), forced_nodes_dict)
        self.assertListEqual(update_recipe_metrics_msg._recipe_ids, [recipe.id])

        # Test executing message again
        newer_when = when + datetime.timedelta(minutes=60)
        message_json_dict = message.to_json()
        message = UncancelJobs.from_json(message_json_dict)
        message.when = newer_when
        result = message.execute()
        self.assertTrue(result)

        jobs = Job.objects.filter(id__in=job_ids).order_by('id')
        # Job 1 should not be updated because it was not CANCELED
        self.assertEqual(jobs[0].status, 'PENDING')
        self.assertEqual(jobs[0].last_status_change, old_when)
        # Job 2 should not be updated since it already was last mexxage execution
        self.assertEqual(jobs[1].status, 'PENDING')
        self.assertEqual(jobs[1].last_status_change, when)
        # Job 3 should not be updated since it has already been queued
        self.assertEqual(jobs[2].status, 'CANCELED')
        self.assertEqual(jobs[2].last_status_change, old_when)
        # Job 4 should not be updated because it was not CANCELED
        self.assertEqual(jobs[3].status, 'FAILED')
        self.assertEqual(jobs[3].last_status_change, old_when)

        # Make sure update_recipe and update_recipe_metrics messages were created
        self.assertEqual(len(message.new_messages), 2)
        update_recipe_msg = None
        update_recipe_metrics_msg = None
        for msg in message.new_messages:
            if msg.type == 'update_recipe':
                update_recipe_msg = msg
            elif msg.type == 'update_recipe_metrics':
                update_recipe_metrics_msg = msg
        self.assertIsNotNone(update_recipe_msg)
        self.assertIsNotNone(update_recipe_metrics_msg)
        self.assertEqual(update_recipe_msg.root_recipe_id, recipe.id)
        self.assertDictEqual(convert_forced_nodes_to_v6(update_recipe_msg.forced_nodes).get_dict(), forced_nodes_dict)
        self.assertListEqual(update_recipe_metrics_msg._recipe_ids, [recipe.id])
