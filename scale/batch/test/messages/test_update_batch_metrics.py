from __future__ import unicode_literals

import datetime

import django
from django.test import TestCase
from django.utils.timezone import now

from batch.messages.update_batch_metrics import UpdateBatchMetrics
from batch.models import Batch, BatchMetrics
from batch.test import utils as batch_test_utils
from job.execution.tasks.json.results.task_results import TaskResults
from job.models import Job
from job.test import utils as job_test_utils
from recipe.models import Recipe, RecipeNode
from recipe.test import utils as recipe_test_utils
from util.parse import datetime_to_string


class TestUpdateBatchMetrics(TestCase):

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

        # Generate recipe metrics
        Recipe.objects.update_recipe_metrics([recipe_1.id, recipe_2.id])

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

        # Generate recipe metrics
        Recipe.objects.update_recipe_metrics([recipe_1.id, recipe_2.id, recipe_3.id])

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
        self.assertIsNone(batch_metrics[0].min_seed_duration)
        self.assertIsNone(batch_metrics[0].avg_seed_duration)
        self.assertIsNone(batch_metrics[0].max_seed_duration)

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
        self.assertEqual(batch_metrics[1].min_seed_duration, datetime.timedelta(minutes=2))
        self.assertEqual(batch_metrics[1].avg_seed_duration, datetime.timedelta(minutes=2, seconds=30))
        self.assertEqual(batch_metrics[1].max_seed_duration, datetime.timedelta(minutes=3))

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
        self.assertIsNone(batch_metrics[2].min_seed_duration)
        self.assertIsNone(batch_metrics[2].avg_seed_duration)
        self.assertIsNone(batch_metrics[2].max_seed_duration)

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
        self.assertIsNone(batch_metrics[3].min_seed_duration)
        self.assertIsNone(batch_metrics[3].avg_seed_duration)
        self.assertIsNone(batch_metrics[3].max_seed_duration)

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
        self.assertIsNone(batch_metrics[4].min_seed_duration)
        self.assertIsNone(batch_metrics[4].avg_seed_duration)
        self.assertIsNone(batch_metrics[4].max_seed_duration)

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
        self.assertIsNone(batch_metrics[5].min_seed_duration)
        self.assertIsNone(batch_metrics[5].avg_seed_duration)
        self.assertIsNone(batch_metrics[5].max_seed_duration)

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
        self.assertIsNone(batch_metrics[6].min_seed_duration)
        self.assertIsNone(batch_metrics[6].avg_seed_duration)
        self.assertIsNone(batch_metrics[6].max_seed_duration)

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
        self.assertIsNone(batch_metrics[7].min_seed_duration)
        self.assertIsNone(batch_metrics[7].avg_seed_duration)
        self.assertIsNone(batch_metrics[7].max_seed_duration)

        # Test executing message again
        message_json_dict = message.to_json()
        message = UpdateBatchMetrics.from_json(message_json_dict)
        result = message.execute()
        self.assertTrue(result)

    def test_execute_with_sub_recipes(self):
        """Tests calling UpdateBatchMetrics.execute() successfully with sub-recipes"""

        batch = batch_test_utils.create_batch()
        recipe_1 = recipe_test_utils.create_recipe(batch=batch)
        recipe_2 = recipe_test_utils.create_recipe(batch=batch)
        # Recipe 1 jobs
        job_1 = job_test_utils.create_job(status='FAILED', save=False)
        job_2 = job_test_utils.create_job(status='CANCELED', save=False)
        job_3 = job_test_utils.create_job(status='BLOCKED', save=False)
        job_4 = job_test_utils.create_job(status='BLOCKED', save=False)
        job_5 = job_test_utils.create_job(status='COMPLETED', save=False)
        # Recipe 2 jobs
        job_6 = job_test_utils.create_job(status='COMPLETED', save=False)
        job_7 = job_test_utils.create_job(status='COMPLETED', save=False)
        job_8 = job_test_utils.create_job(status='RUNNING', save=False)
        job_9 = job_test_utils.create_job(status='QUEUED', save=False)
        job_10 = job_test_utils.create_job(status='PENDING', save=False)
        job_11 = job_test_utils.create_job(status='PENDING', save=False)
        job_12 = job_test_utils.create_job(status='PENDING', save=False)
        job_13 = job_test_utils.create_job(status='CANCELED', save=False)
        job_14 = job_test_utils.create_job(status='BLOCKED', save=False)
        Job.objects.bulk_create([job_1, job_2, job_3, job_4, job_5, job_6, job_7, job_8, job_9, job_10, job_11, job_12,
                                 job_13, job_14])

        # Recipe 1 sub-recipes
        sub_recipe_1 = recipe_test_utils.create_recipe(save=False)
        sub_recipe_1.recipe = recipe_1
        sub_recipe_1.jobs_total = 26
        sub_recipe_1.jobs_pending = 3
        sub_recipe_1.jobs_blocked = 4
        sub_recipe_1.jobs_queued = 5
        sub_recipe_1.jobs_running = 1
        sub_recipe_1.jobs_failed = 2
        sub_recipe_1.jobs_completed = 3
        sub_recipe_1.jobs_canceled = 8
        sub_recipe_1.is_completed = False
        sub_recipe_2 = recipe_test_utils.create_recipe(save=False)
        sub_recipe_2.recipe = recipe_1
        sub_recipe_2.jobs_total = 30
        sub_recipe_2.jobs_completed = 30
        sub_recipe_2.is_completed = True
        # Recipe 2 sub-recipes
        sub_recipe_3 = recipe_test_utils.create_recipe(save=False)
        sub_recipe_3.recipe = recipe_2
        sub_recipe_3.jobs_total = 21
        sub_recipe_3.jobs_pending = 2
        sub_recipe_3.jobs_blocked = 5
        sub_recipe_3.jobs_queued = 0
        sub_recipe_3.jobs_running = 3
        sub_recipe_3.jobs_failed = 2
        sub_recipe_3.jobs_completed = 8
        sub_recipe_3.jobs_canceled = 1
        sub_recipe_3.is_completed = False
        sub_recipe_4 = recipe_test_utils.create_recipe(save=False)
        sub_recipe_4.recipe = recipe_2
        sub_recipe_4.jobs_total = 7
        sub_recipe_4.jobs_completed = 7
        sub_recipe_4.is_completed = True
        sub_recipe_5 = recipe_test_utils.create_recipe(save=False)
        sub_recipe_5.recipe = recipe_2
        sub_recipe_5.jobs_total = 12
        sub_recipe_5.jobs_completed = 12
        sub_recipe_5.is_completed = True
        Recipe.objects.bulk_create([sub_recipe_1, sub_recipe_2, sub_recipe_3, sub_recipe_4, sub_recipe_5])
        # Recipe 1 nodes
        recipe_node_1 = recipe_test_utils.create_recipe_node(recipe=recipe_1, job=job_1)
        recipe_node_2 = recipe_test_utils.create_recipe_node(recipe=recipe_1, job=job_2)
        recipe_node_3 = recipe_test_utils.create_recipe_node(recipe=recipe_1, job=job_3)
        recipe_node_4 = recipe_test_utils.create_recipe_node(recipe=recipe_1, job=job_4)
        recipe_node_5 = recipe_test_utils.create_recipe_node(recipe=recipe_1, job=job_5)
        recipe_node_6 = recipe_test_utils.create_recipe_node(recipe=recipe_1, sub_recipe=sub_recipe_1)
        recipe_node_7 = recipe_test_utils.create_recipe_node(recipe=recipe_1, sub_recipe=sub_recipe_2)
        # Recipe 2 nodes
        recipe_node_8 = recipe_test_utils.create_recipe_node(recipe=recipe_2, job=job_6)
        recipe_node_9 = recipe_test_utils.create_recipe_node(recipe=recipe_2, job=job_7)
        recipe_node_10 = recipe_test_utils.create_recipe_node(recipe=recipe_2, job=job_8)
        recipe_node_11 = recipe_test_utils.create_recipe_node(recipe=recipe_2, job=job_9)
        recipe_node_12 = recipe_test_utils.create_recipe_node(recipe=recipe_2, job=job_10)
        recipe_node_13 = recipe_test_utils.create_recipe_node(recipe=recipe_2, job=job_11)
        recipe_node_14 = recipe_test_utils.create_recipe_node(recipe=recipe_2, job=job_12)
        recipe_node_15 = recipe_test_utils.create_recipe_node(recipe=recipe_2, job=job_13)
        recipe_node_16 = recipe_test_utils.create_recipe_node(recipe=recipe_2, job=job_14)
        recipe_node_17 = recipe_test_utils.create_recipe_node(recipe=recipe_2, sub_recipe=sub_recipe_3)
        recipe_node_18 = recipe_test_utils.create_recipe_node(recipe=recipe_2, sub_recipe=sub_recipe_4)
        recipe_node_19 = recipe_test_utils.create_recipe_node(recipe=recipe_2, sub_recipe=sub_recipe_5)
        RecipeNode.objects.bulk_create([recipe_node_1, recipe_node_2, recipe_node_3, recipe_node_4, recipe_node_5,
                                        recipe_node_6, recipe_node_7, recipe_node_8, recipe_node_9, recipe_node_10,
                                        recipe_node_11, recipe_node_12, recipe_node_13, recipe_node_14, recipe_node_15,
                                        recipe_node_16, recipe_node_17, recipe_node_18, recipe_node_19])

        # Generate recipe metrics
        Recipe.objects.update_recipe_metrics([sub_recipe_1.id, sub_recipe_2.id, sub_recipe_3.id, sub_recipe_4.id,
                                              sub_recipe_5.id])
        Recipe.objects.update_recipe_metrics([recipe_1.id, recipe_2.id])

        # Add batch to message
        message = UpdateBatchMetrics()
        if message.can_fit_more():
            message.add_batch(batch.id)

        # Execute message
        result = message.execute()
        self.assertTrue(result)

        batch = Batch.objects.get(id=batch.id)
        self.assertEqual(batch.jobs_total, 110)
        self.assertEqual(batch.jobs_pending, 8)
        self.assertEqual(batch.jobs_blocked, 12)
        self.assertEqual(batch.jobs_queued, 6)
        self.assertEqual(batch.jobs_running, 5)
        self.assertEqual(batch.jobs_failed, 5)
        self.assertEqual(batch.jobs_completed, 63)
        self.assertEqual(batch.jobs_canceled, 11)
        self.assertEqual(batch.recipes_total, 7)
        self.assertEqual(batch.recipes_completed, 3)

        # Test executing message again
        message_json_dict = message.to_json()
        message = UpdateBatchMetrics.from_json(message_json_dict)
        result = message.execute()
        self.assertTrue(result)
