from __future__ import unicode_literals

import datetime

import django
from django.test import TestCase
from django.utils.timezone import now

from batch.messages.update_batch_metrics import UpdateBatchMetrics
from batch.models import Batch, BatchMetrics
from batch.test import utils as batch_test_utils
from job.execution.tasks.json.results.task_results import TaskResults
from job.test import utils as job_test_utils
from recipe.test import utils as recipe_test_utils
from util.parse import datetime_to_string


class TestUpdateBatchMetrics(TestCase):

    fixtures = ['batch_job_types.json']

    def setUp(self):
        django.setup()

    def test_json(self):
        """Tests coverting an UpdateBatchMetrics message to and from JSON"""

        batch = batch_test_utils.create_batch()

        recipe_1 = recipe_test_utils.create_recipe(batch=batch)
        job_1 = job_test_utils.create_job(status='FAILED')
        job_2 = job_test_utils.create_job(status='CANCELED')
        job_3 = job_test_utils.create_job(status='BLOCKED')
        job_4 = job_test_utils.create_job(status='BLOCKED')
        job_5 = job_test_utils.create_job(status='COMPLETED')
        recipe_test_utils.create_recipe_job(recipe=recipe_1, job=job_1)
        recipe_test_utils.create_recipe_job(recipe=recipe_1, job=job_2)
        recipe_test_utils.create_recipe_job(recipe=recipe_1, job=job_3)
        recipe_test_utils.create_recipe_job(recipe=recipe_1, job=job_4)
        recipe_test_utils.create_recipe_job(recipe=recipe_1, job=job_5)

        recipe_2 = recipe_test_utils.create_recipe(batch=batch)
        recipe_2.is_completed = True
        recipe_2.save()
        job_6 = job_test_utils.create_job(status='COMPLETED')
        job_7 = job_test_utils.create_job(status='COMPLETED')
        job_8 = job_test_utils.create_job(status='COMPLETED')
        recipe_test_utils.create_recipe_job(recipe=recipe_2, job=job_6)
        recipe_test_utils.create_recipe_job(recipe=recipe_2, job=job_7)
        recipe_test_utils.create_recipe_job(recipe=recipe_2, job=job_8)

        # Add batch to message
        message = UpdateBatchMetrics()
        if message.can_fit_more():
            message.add_batch(batch.id)

        # Convert message to JSON and back, and then execute
        message_json_dict = message.to_json()
        new_message = UpdateBatchMetrics.from_json(message_json_dict)
        result = new_message.execute()

        self.assertTrue(result)
        batch = Batch.objects.get(id=batch.id)
        self.assertEqual(batch.jobs_total, 8)
        self.assertEqual(batch.jobs_pending, 0)
        self.assertEqual(batch.jobs_blocked, 2)
        self.assertEqual(batch.jobs_queued, 0)
        self.assertEqual(batch.jobs_running, 0)
        self.assertEqual(batch.jobs_failed, 1)
        self.assertEqual(batch.jobs_completed, 4)
        self.assertEqual(batch.jobs_canceled, 1)
        self.assertEqual(batch.recipes_total, 2)
        self.assertEqual(batch.recipes_completed, 1)

    def test_execute(self):
        """Tests calling UpdateBatchMetrics.execute() successfully"""

        job_type = job_test_utils.create_job_type()
        definition = {
            'version': '1.0',
            'input_data': [],
            'jobs': [{
                'name': 'a',
                'job_type': {
                    'name': job_type.name,
                    'version': job_type.version,
                },
            }, {
                'name': 'b',
                'job_type': {
                    'name': job_type.name,
                    'version': job_type.version,
                },
            }, {
                'name': 'c',
                'job_type': {
                    'name': job_type.name,
                    'version': job_type.version,
                },
                'dependencies': [{
                    'name': 'b',
                }],
            }, {
                'name': 'd',
                'job_type': {
                    'name': job_type.name,
                    'version': job_type.version,
                },
                'dependencies': [{
                    'name': 'b',
                }],
            }, {
                'name': 'e',
                'job_type': {
                    'name': job_type.name,
                    'version': job_type.version,
                },
                'dependencies': [{
                    'name': 'd',
                }],
            }, {
                'name': 'f',
                'job_type': {
                    'name': job_type.name,
                    'version': job_type.version,
                },
            }, {
                'name': 'g',
                'job_type': {
                    'name': job_type.name,
                    'version': job_type.version,
                },
                'dependencies': [{
                    'name': 'f',
                }],
            }, {
                'name': 'h',
                'job_type': {
                    'name': job_type.name,
                    'version': job_type.version,
                },
            }]
        }
        recipe_type = recipe_test_utils.create_recipe_type(definition=definition)
        batch = batch_test_utils.create_batch(recipe_type=recipe_type)

        started = now()
        ended_1 = started + datetime.timedelta(minutes=1)
        ended_2 = started + datetime.timedelta(minutes=2)
        ended_3 = started + datetime.timedelta(minutes=3)
        ended_4 = started + datetime.timedelta(minutes=7)
        recipe_1 = recipe_test_utils.create_recipe(batch=batch, recipe_type=recipe_type)
        job_1 = job_test_utils.create_job(status='COMPLETED', started=started, ended=ended_1)
        job_2 = job_test_utils.create_job(status='COMPLETED')
        task_results = {'version': '1.0', 'tasks': [{'task_id': '1234', 'type': 'main',
                                                     'started': datetime_to_string(started),
                                                     'ended': datetime_to_string(ended_2)}]}
        task_results = TaskResults(task_results=task_results, do_validate=False)
        job_test_utils.create_job_exe(job=job_2, status='COMPLETED', task_results=task_results)
        job_3 = job_test_utils.create_job(status='QUEUED')
        job_4 = job_test_utils.create_job(status='QUEUED')
        job_5 = job_test_utils.create_job(status='RUNNING')
        job_6 = job_test_utils.create_job(status='RUNNING')
        job_7 = job_test_utils.create_job(status='RUNNING')
        job_8 = job_test_utils.create_job(status='PENDING')
        job_9 = job_test_utils.create_job(status='PENDING')
        job_10 = job_test_utils.create_job(status='CANCELED')
        job_11 = job_test_utils.create_job(status='BLOCKED')
        job_12 = job_test_utils.create_job(status='FAILED')
        recipe_test_utils.create_recipe_job(recipe=recipe_1, job=job_1, job_name='a')
        recipe_test_utils.create_recipe_job(recipe=recipe_1, job=job_2, job_name='b')
        recipe_test_utils.create_recipe_job(recipe=recipe_1, job=job_3, job_name='c')
        recipe_test_utils.create_recipe_job(recipe=recipe_1, job=job_4, job_name='c')
        recipe_test_utils.create_recipe_job(recipe=recipe_1, job=job_5, job_name='c')
        recipe_test_utils.create_recipe_job(recipe=recipe_1, job=job_6, job_name='d')
        recipe_test_utils.create_recipe_job(recipe=recipe_1, job=job_7, job_name='d')
        recipe_test_utils.create_recipe_job(recipe=recipe_1, job=job_8, job_name='e')
        recipe_test_utils.create_recipe_job(recipe=recipe_1, job=job_9, job_name='e')
        recipe_test_utils.create_recipe_job(recipe=recipe_1, job=job_10, job_name='f')
        recipe_test_utils.create_recipe_job(recipe=recipe_1, job=job_11, job_name='g')
        recipe_test_utils.create_recipe_job(recipe=recipe_1, job=job_12, job_name='h')

        recipe_2 = recipe_test_utils.create_recipe(batch=batch, recipe_type=recipe_type)
        recipe_2.is_completed = True
        recipe_2.save()
        job_13 = job_test_utils.create_job(status='FAILED')
        job_14 = job_test_utils.create_job(status='COMPLETED')
        job_15 = job_test_utils.create_job(status='RUNNING')
        job_16 = job_test_utils.create_job(status='RUNNING')
        job_17 = job_test_utils.create_job(status='QUEUED')
        job_18 = job_test_utils.create_job(status='QUEUED')
        job_19 = job_test_utils.create_job(status='QUEUED')
        job_20 = job_test_utils.create_job(status='QUEUED')
        job_21 = job_test_utils.create_job(status='PENDING')
        recipe_test_utils.create_recipe_job(recipe=recipe_2, job=job_13, job_name='a')
        recipe_test_utils.create_recipe_job(recipe=recipe_2, job=job_14, job_name='b')
        recipe_test_utils.create_recipe_job(recipe=recipe_2, job=job_15, job_name='c')
        recipe_test_utils.create_recipe_job(recipe=recipe_2, job=job_16, job_name='c')
        recipe_test_utils.create_recipe_job(recipe=recipe_2, job=job_17, job_name='d')
        recipe_test_utils.create_recipe_job(recipe=recipe_2, job=job_18, job_name='d')
        recipe_test_utils.create_recipe_job(recipe=recipe_2, job=job_19, job_name='d')
        recipe_test_utils.create_recipe_job(recipe=recipe_2, job=job_20, job_name='d')
        recipe_test_utils.create_recipe_job(recipe=recipe_2, job=job_21, job_name='e')

        recipe_3 = recipe_test_utils.create_recipe(batch=batch, recipe_type=recipe_type)
        recipe_3.is_completed = True
        recipe_3.save()
        job_22 = job_test_utils.create_job(status='COMPLETED')
        job_23 = job_test_utils.create_job(status='COMPLETED')
        task_results = {'version': '1.0', 'tasks': [{'task_id': '1234', 'type': 'main',
                                                     'started': datetime_to_string(started),
                                                     'ended': datetime_to_string(ended_3)}]}
        task_results = TaskResults(task_results=task_results, do_validate=False)
        job_test_utils.create_job_exe(job=job_23, status='COMPLETED', task_results=task_results)
        job_24 = job_test_utils.create_job(status='COMPLETED', started=started, ended=ended_2)
        job_25 = job_test_utils.create_job(status='COMPLETED', started=started, ended=ended_3)
        job_26 = job_test_utils.create_job(status='COMPLETED', started=started, ended=ended_4)
        job_27 = job_test_utils.create_job(status='COMPLETED')
        recipe_test_utils.create_recipe_job(recipe=recipe_3, job=job_22, job_name='a')
        recipe_test_utils.create_recipe_job(recipe=recipe_3, job=job_23, job_name='b')
        recipe_test_utils.create_recipe_job(recipe=recipe_3, job=job_24, job_name='c')
        recipe_test_utils.create_recipe_job(recipe=recipe_3, job=job_25, job_name='c')
        recipe_test_utils.create_recipe_job(recipe=recipe_3, job=job_26, job_name='c')
        recipe_test_utils.create_recipe_job(recipe=recipe_3, job=job_27, job_name='c')

        # Add batch to message
        message = UpdateBatchMetrics()
        if message.can_fit_more():
            message.add_batch(batch.id)

        # Execute message
        result = message.execute()
        self.assertTrue(result)

        batch = Batch.objects.get(id=batch.id)
        self.assertEqual(batch.jobs_total, 27)
        self.assertEqual(batch.jobs_pending, 3)
        self.assertEqual(batch.jobs_blocked, 1)
        self.assertEqual(batch.jobs_queued, 6)
        self.assertEqual(batch.jobs_running, 5)
        self.assertEqual(batch.jobs_failed, 2)
        self.assertEqual(batch.jobs_completed, 9)
        self.assertEqual(batch.jobs_canceled, 1)
        self.assertEqual(batch.recipes_total, 3)
        self.assertEqual(batch.recipes_completed, 2)

        batch_metrics = BatchMetrics.objects.filter(batch_id=batch.id).order_by('job_name')
        self.assertEqual(len(batch_metrics), 8)

        # Job A
        self.assertEqual(batch_metrics[0].job_name, 'a')
        self.assertEqual(batch_metrics[0].jobs_total, 3)
        self.assertEqual(batch_metrics[0].jobs_pending, 0)
        self.assertEqual(batch_metrics[0].jobs_blocked, 0)
        self.assertEqual(batch_metrics[0].jobs_queued, 0)
        self.assertEqual(batch_metrics[0].jobs_running, 0)
        self.assertEqual(batch_metrics[0].jobs_failed, 1)
        self.assertEqual(batch_metrics[0].jobs_completed, 2)
        self.assertEqual(batch_metrics[0].jobs_canceled, 0)
        self.assertEqual(batch_metrics[0].min_job_duration, datetime.timedelta(minutes=1))
        self.assertEqual(batch_metrics[0].avg_job_duration, datetime.timedelta(minutes=1))
        self.assertEqual(batch_metrics[0].max_job_duration, datetime.timedelta(minutes=1))
        self.assertIsNone(batch_metrics[0].min_alg_duration)
        self.assertIsNone(batch_metrics[0].avg_alg_duration)
        self.assertIsNone(batch_metrics[0].max_alg_duration)

        # Job B
        self.assertEqual(batch_metrics[1].job_name, 'b')
        self.assertEqual(batch_metrics[1].jobs_total, 3)
        self.assertEqual(batch_metrics[1].jobs_pending, 0)
        self.assertEqual(batch_metrics[1].jobs_blocked, 0)
        self.assertEqual(batch_metrics[1].jobs_queued, 0)
        self.assertEqual(batch_metrics[1].jobs_running, 0)
        self.assertEqual(batch_metrics[1].jobs_failed, 0)
        self.assertEqual(batch_metrics[1].jobs_completed, 3)
        self.assertEqual(batch_metrics[1].jobs_canceled, 0)
        self.assertIsNone(batch_metrics[1].min_job_duration)
        self.assertIsNone(batch_metrics[1].avg_job_duration)
        self.assertIsNone(batch_metrics[1].max_job_duration)
        self.assertEqual(batch_metrics[1].min_alg_duration, datetime.timedelta(minutes=2))
        self.assertEqual(batch_metrics[1].avg_alg_duration, datetime.timedelta(minutes=2, seconds=30))
        self.assertEqual(batch_metrics[1].max_alg_duration, datetime.timedelta(minutes=3))

        # Job C
        self.assertEqual(batch_metrics[2].job_name, 'c')
        self.assertEqual(batch_metrics[2].jobs_total, 9)
        self.assertEqual(batch_metrics[2].jobs_pending, 0)
        self.assertEqual(batch_metrics[2].jobs_blocked, 0)
        self.assertEqual(batch_metrics[2].jobs_queued, 2)
        self.assertEqual(batch_metrics[2].jobs_running, 3)
        self.assertEqual(batch_metrics[2].jobs_failed, 0)
        self.assertEqual(batch_metrics[2].jobs_completed, 4)
        self.assertEqual(batch_metrics[2].jobs_canceled, 0)
        self.assertEqual(batch_metrics[2].min_job_duration, datetime.timedelta(minutes=2))
        self.assertEqual(batch_metrics[2].avg_job_duration, datetime.timedelta(minutes=4))
        self.assertEqual(batch_metrics[2].max_job_duration, datetime.timedelta(minutes=7))
        self.assertIsNone(batch_metrics[2].min_alg_duration)
        self.assertIsNone(batch_metrics[2].avg_alg_duration)
        self.assertIsNone(batch_metrics[2].max_alg_duration)

        # Job D
        self.assertEqual(batch_metrics[3].job_name, 'd')
        self.assertEqual(batch_metrics[3].jobs_total, 6)
        self.assertEqual(batch_metrics[3].jobs_pending, 0)
        self.assertEqual(batch_metrics[3].jobs_blocked, 0)
        self.assertEqual(batch_metrics[3].jobs_queued, 4)
        self.assertEqual(batch_metrics[3].jobs_running, 2)
        self.assertEqual(batch_metrics[3].jobs_failed, 0)
        self.assertEqual(batch_metrics[3].jobs_completed, 0)
        self.assertEqual(batch_metrics[3].jobs_canceled, 0)
        self.assertIsNone(batch_metrics[3].min_job_duration)
        self.assertIsNone(batch_metrics[3].avg_job_duration)
        self.assertIsNone(batch_metrics[3].max_job_duration)
        self.assertIsNone(batch_metrics[3].min_alg_duration)
        self.assertIsNone(batch_metrics[3].avg_alg_duration)
        self.assertIsNone(batch_metrics[3].max_alg_duration)

        # Job E
        self.assertEqual(batch_metrics[4].job_name, 'e')
        self.assertEqual(batch_metrics[4].jobs_total, 3)
        self.assertEqual(batch_metrics[4].jobs_pending, 3)
        self.assertEqual(batch_metrics[4].jobs_blocked, 0)
        self.assertEqual(batch_metrics[4].jobs_queued, 0)
        self.assertEqual(batch_metrics[4].jobs_running, 0)
        self.assertEqual(batch_metrics[4].jobs_failed, 0)
        self.assertEqual(batch_metrics[4].jobs_completed, 0)
        self.assertEqual(batch_metrics[4].jobs_canceled, 0)
        self.assertIsNone(batch_metrics[4].min_job_duration)
        self.assertIsNone(batch_metrics[4].avg_job_duration)
        self.assertIsNone(batch_metrics[4].max_job_duration)
        self.assertIsNone(batch_metrics[4].min_alg_duration)
        self.assertIsNone(batch_metrics[4].avg_alg_duration)
        self.assertIsNone(batch_metrics[4].max_alg_duration)

        # Job F
        self.assertEqual(batch_metrics[5].job_name, 'f')
        self.assertEqual(batch_metrics[5].jobs_total, 1)
        self.assertEqual(batch_metrics[5].jobs_pending, 0)
        self.assertEqual(batch_metrics[5].jobs_blocked, 0)
        self.assertEqual(batch_metrics[5].jobs_queued, 0)
        self.assertEqual(batch_metrics[5].jobs_running, 0)
        self.assertEqual(batch_metrics[5].jobs_failed, 0)
        self.assertEqual(batch_metrics[5].jobs_completed, 0)
        self.assertEqual(batch_metrics[5].jobs_canceled, 1)
        self.assertIsNone(batch_metrics[5].min_job_duration)
        self.assertIsNone(batch_metrics[5].avg_job_duration)
        self.assertIsNone(batch_metrics[5].max_job_duration)
        self.assertIsNone(batch_metrics[5].min_alg_duration)
        self.assertIsNone(batch_metrics[5].avg_alg_duration)
        self.assertIsNone(batch_metrics[5].max_alg_duration)

        # Job G
        self.assertEqual(batch_metrics[6].job_name, 'g')
        self.assertEqual(batch_metrics[6].jobs_total, 1)
        self.assertEqual(batch_metrics[6].jobs_pending, 0)
        self.assertEqual(batch_metrics[6].jobs_blocked, 1)
        self.assertEqual(batch_metrics[6].jobs_queued, 0)
        self.assertEqual(batch_metrics[6].jobs_running, 0)
        self.assertEqual(batch_metrics[6].jobs_failed, 0)
        self.assertEqual(batch_metrics[6].jobs_completed, 0)
        self.assertEqual(batch_metrics[6].jobs_canceled, 0)
        self.assertIsNone(batch_metrics[6].min_job_duration)
        self.assertIsNone(batch_metrics[6].avg_job_duration)
        self.assertIsNone(batch_metrics[6].max_job_duration)
        self.assertIsNone(batch_metrics[6].min_alg_duration)
        self.assertIsNone(batch_metrics[6].avg_alg_duration)
        self.assertIsNone(batch_metrics[6].max_alg_duration)

        # Job H
        self.assertEqual(batch_metrics[7].job_name, 'h')
        self.assertEqual(batch_metrics[7].jobs_total, 1)
        self.assertEqual(batch_metrics[7].jobs_pending, 0)
        self.assertEqual(batch_metrics[7].jobs_blocked, 0)
        self.assertEqual(batch_metrics[7].jobs_queued, 0)
        self.assertEqual(batch_metrics[7].jobs_running, 0)
        self.assertEqual(batch_metrics[7].jobs_failed, 1)
        self.assertEqual(batch_metrics[7].jobs_completed, 0)
        self.assertEqual(batch_metrics[7].jobs_canceled, 0)
        self.assertIsNone(batch_metrics[7].min_job_duration)
        self.assertIsNone(batch_metrics[7].avg_job_duration)
        self.assertIsNone(batch_metrics[7].max_job_duration)
        self.assertIsNone(batch_metrics[7].min_alg_duration)
        self.assertIsNone(batch_metrics[7].avg_alg_duration)
        self.assertIsNone(batch_metrics[7].max_alg_duration)

        # Test executing message again
        message_json_dict = message.to_json()
        message = UpdateBatchMetrics.from_json(message_json_dict)
        result = message.execute()
        self.assertTrue(result)

        # TODO: check results again
