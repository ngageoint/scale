from __future__ import unicode_literals

import datetime
import time

import django
from django.utils.timezone import now
from django.test import TestCase, TransactionTestCase

import job.test.utils as job_test_utils
import product.test.utils as product_test_utils
import queue.test.utils as queue_test_utils
import recipe.test.utils as recipe_test_utils
import storage.test.utils as storage_test_utils
import source.test.utils as source_test_utils
import trigger.test.utils as trigger_test_utils
from error.models import reset_error_cache
from job.configuration.results.job_results import JobResults
from job.models import Job
from queue.models import JobLoad, Queue, QUEUE_ORDER_FIFO, QUEUE_ORDER_LIFO
from recipe.configuration.data.recipe_data import LegacyRecipeData
from recipe.configuration.definition.recipe_definition import LegacyRecipeDefinition as RecipeDefinition
from recipe.handlers.graph_delta import RecipeGraphDelta
from recipe.models import Recipe, RecipeJob


class TestJobLoadManager(TestCase):

    def setUp(self):
        django.setup()

    def test_calculate_empty(self):
        """Tests calculating job load when there are no jobs."""

        JobLoad.objects.calculate()
        results = JobLoad.objects.all()

        self.assertEqual(len(results), 1)

    def test_calculate_status(self):
        """Tests calculating job load filtering by status."""

        job_type = job_test_utils.create_job_type()
        job_test_utils.create_job(job_type=job_type, status='PENDING')
        job_test_utils.create_job(job_type=job_type, status='BLOCKED')
        job_test_utils.create_job(job_type=job_type, status='QUEUED')
        job_test_utils.create_job(job_type=job_type, status='RUNNING')
        job_test_utils.create_job(job_type=job_type, status='COMPLETED')
        job_test_utils.create_job(job_type=job_type, status='FAILED')
        job_test_utils.create_job(job_type=job_type, status='CANCELED')

        JobLoad.objects.calculate()
        results = JobLoad.objects.all()

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].job_type_id, job_type.id)
        self.assertIsNotNone(results[0].measured)
        self.assertEqual(results[0].pending_count, 1)
        self.assertEqual(results[0].queued_count, 1)
        self.assertEqual(results[0].running_count, 1)
        self.assertEqual(results[0].total_count, 3)

    def test_calculate_job_type(self):
        """Tests calculating job load grouping by job type."""

        job_type1 = job_test_utils.create_job_type()
        job_test_utils.create_job(job_type=job_type1, status='PENDING')

        job_type2 = job_test_utils.create_job_type()
        job_test_utils.create_job(job_type=job_type2, status='QUEUED')
        job_test_utils.create_job(job_type=job_type2, status='QUEUED')

        job_type3 = job_test_utils.create_job_type()
        job_test_utils.create_job(job_type=job_type3, status='RUNNING')
        job_test_utils.create_job(job_type=job_type3, status='RUNNING')
        job_test_utils.create_job(job_type=job_type3, status='RUNNING')

        JobLoad.objects.calculate()
        results = JobLoad.objects.all()

        self.assertEqual(len(results), 3)
        for result in results:
            if result.job_type_id == job_type1.id:
                self.assertEqual(result.pending_count, 1)
                self.assertEqual(result.queued_count, 0)
                self.assertEqual(result.running_count, 0)
                self.assertEqual(result.total_count, 1)
            elif result.job_type_id == job_type2.id:
                self.assertEqual(result.pending_count, 0)
                self.assertEqual(result.queued_count, 2)
                self.assertEqual(result.running_count, 0)
                self.assertEqual(result.total_count, 2)
            elif result.job_type_id == job_type3.id:
                self.assertEqual(result.pending_count, 0)
                self.assertEqual(result.queued_count, 0)
                self.assertEqual(result.running_count, 3)
                self.assertEqual(result.total_count, 3)
            else:
                self.fail('Found unexpected job type: %i' % result.job_type_id)


class TestQueueManager(TransactionTestCase):

    fixtures = ['basic_errors.json']

    def setUp(self):
        django.setup()

        reset_error_cache()

    def test_get_queue_fifo(self):
        """Tests calling QueueManager.get_queue() in FIFO mode"""

        time_1 = now()
        time_2 = time_1 + datetime.timedelta(seconds=1)
        queue_1 = queue_test_utils.create_queue(priority=100, queued=time_1)
        queue_2 = queue_test_utils.create_queue(priority=100, queued=time_2)

        # Call method to test
        first = True
        for queue in Queue.objects.get_queue(QUEUE_ORDER_FIFO):
            if first:
                self.assertEqual(queue.id, queue_1.id)
                first = False
            else:
                self.assertEqual(queue.id, queue_2.id)

    def test_get_queue_lifo(self):
        """Tests calling QueueManager.get_queue() in LIFO mode"""

        time_1 = now()
        time_2 = time_1 + datetime.timedelta(seconds=1)
        queue_1 = queue_test_utils.create_queue(priority=100, queued=time_1)
        queue_2 = queue_test_utils.create_queue(priority=100, queued=time_2)

        # Call method to test
        first = True
        for queue in Queue.objects.get_queue(QUEUE_ORDER_LIFO):
            if first:
                self.assertEqual(queue.id, queue_2.id)
                first = False
            else:
                self.assertEqual(queue.id, queue_1.id)


class TestQueueManagerHandleJobCancellation(TransactionTestCase):

    def setUp(self):
        django.setup()

    def test_successful_with_pending_job(self):
        """Tests calling QueueManager.handle_job_cancellation() successfully with a pending job."""

        # Create the job
        job = job_test_utils.create_job(status='PENDING')

        # Call method to test
        Queue.objects.handle_job_cancellation(job.id, now())

        # Make sure job is canceled
        final_job = Job.objects.get(pk=job.id)
        self.assertEqual(final_job.status, 'CANCELED')

    def test_successful_with_blocked_job(self):
        """Tests calling QueueManager.handle_job_cancellation() successfully with a blocked job."""

        # Create the job
        job = job_test_utils.create_job(status='BLOCKED')

        # Call method to test
        Queue.objects.handle_job_cancellation(job.id, now())

        # Make sure job is canceled
        final_job = Job.objects.get(pk=job.id)
        self.assertEqual(final_job.status, 'CANCELED')

    def test_successful_with_queued_job(self):
        """Tests calling QueueManager.handle_job_cancellation() successfully with a queued job."""

        # Queue the job
        job = job_test_utils.create_job()
        Queue.objects.queue_jobs([job])

        # Call method to test
        Queue.objects.handle_job_cancellation(job.id, now())

        # Make sure job is canceled and queue model is marked canceled
        final_job = Job.objects.get(pk=job.id)
        self.assertEqual(final_job.status, 'CANCELED')
        self.assertTrue(Queue.objects.get(job_id=job.id).is_canceled)

    def test_successful_with_running_job(self):
        """Tests calling QueueManager.handle_job_cancellation() successfully with a running job."""

        # Create the running job
        job = job_test_utils.create_job(status='RUNNING')

        # Call method to test
        Queue.objects.handle_job_cancellation(job.id, now())

        # Make sure job is canceled
        final_job = Job.objects.get(pk=job.id)
        self.assertEqual(final_job.status, 'CANCELED')

    def test_successful_with_failed_job(self):
        """Tests calling QueueManager.handle_job_cancellation() successfully with a failed job."""

        # Create the failed job
        job = job_test_utils.create_job(status='FAILED')
        job_test_utils.create_job_exe(job=job, exe_num=1, status='FAILED')
        time.sleep(0.001)
        job_test_utils.create_job_exe(job=job, exe_num=2, status='FAILED')
        time.sleep(0.001)
        job_exe_3 = job_test_utils.create_job_exe(job=job, status='FAILED')

        # Call method to test
        Queue.objects.handle_job_cancellation(job.id, now())

        # Make sure job is canceled
        final_job = Job.objects.get(pk=job.id)
        self.assertEqual(final_job.status, 'CANCELED')

    def test_exception_with_completed_job(self):
        """Tests calling QueueManager.handle_job_cancellation() with a completed job."""

        # Create the completed job
        job = job_test_utils.create_job(status='COMPLETED')
        job_test_utils.create_job_exe(job=job, exe_num=1, status='FAILED')
        time.sleep(0.001)
        job_test_utils.create_job_exe(job=job, exe_num=2, status='COMPLETED')

        # Call method to test
        Queue.objects.handle_job_cancellation(job.id, now())

        # Make sure job is still completed
        final_job = Job.objects.get(pk=job.id)
        self.assertEqual(final_job.status, 'COMPLETED')

    def test_exception_with_canceled_job(self):
        """Tests calling QueueManager.handle_job_cancellation() with a canceled job."""

        # Create the canceled job
        job = job_test_utils.create_job(status='CANCELED')
        job_test_utils.create_job_exe(job=job, exe_num=1, status='FAILED')
        time.sleep(0.001)
        job_test_utils.create_job_exe(job=job, exe_num=2, status='CANCELED')

        # Call method to test
        Queue.objects.handle_job_cancellation(job.id, now())

        # Make sure job is still canceled
        final_job = Job.objects.get(pk=job.id)
        self.assertEqual(final_job.status, 'CANCELED')


class TestQueueManagerQueueNewRecipe(TransactionTestCase):

    fixtures = ['basic_system_job_types.json']

    def setUp(self):
        django.setup()

        workspace = storage_test_utils.create_workspace()
        source_file = source_test_utils.create_source(workspace=workspace)
        self.event = trigger_test_utils.create_trigger_event()

        interface_1 = {
            'version': '1.0',
            'command': 'test_command',
            'command_arguments': 'test_arg',
            'input_data': [{
                'name': 'Test Input 1',
                'type': 'file',
                'media_types': ['text/plain'],
            }],
            'output_data': [{
                'name': 'Test Output 1',
                'type': 'files',
                'media_type': 'image/png',
            }]
        }
        self.job_type_1 = job_test_utils.create_job_type(interface=interface_1)

        interface_2 = {
            'version': '1.0',
            'command': 'test_command',
            'command_arguments': 'test_arg',
            'input_data': [{
                'name': 'Test Input 2',
                'type': 'files',
                'media_types': ['image/png', 'image/tiff'],
            }],
            'output_data': [{
                'name': 'Test Output 2',
                'type': 'file',
            }]
        }
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

        recipe_definition = RecipeDefinition(definition)
        recipe_definition.validate_job_interfaces()

        self.recipe_type = recipe_test_utils.create_recipe_type(definition=definition)

        data = {
            'version': '1.0',
            'input_data': [{
                'name': 'Recipe Input',
                'file_id': source_file.id,
            }],
            'workspace_id': workspace.id,
        }
        self.data = LegacyRecipeData(data)

    def test_successful(self):
        """Tests calling QueueManager.queue_new_recipe() successfully."""

        handler = Queue.objects.queue_new_recipe(self.recipe_type, self.data, self.event)

        # Make sure the recipe jobs are created and Job 1 is queued
        recipe_job_1 = RecipeJob.objects.select_related('job').get(recipe_id=handler.recipe.id, job_name='Job 1')
        self.assertEqual(recipe_job_1.job.job_type.id, self.job_type_1.id)
        self.assertEqual(recipe_job_1.job.status, 'QUEUED')

        recipe_job_2 = RecipeJob.objects.select_related('job').get(recipe_id=handler.recipe.id, job_name='Job 2')
        self.assertEqual(recipe_job_2.job.job_type.id, self.job_type_2.id)
        self.assertEqual(recipe_job_2.job.status, 'PENDING')

        recipe = Recipe.objects.get(pk=handler.recipe.id)
        self.assertIsNone(recipe.completed)

    def test_successful_priority(self):
        """Tests calling QueueManager.queue_new_recipe() successfully with an override priority."""

        handler = Queue.objects.queue_new_recipe(recipe_type=self.recipe_type, data=self.data, event=self.event,
                                                 priority=1111)

        # Make sure the recipe jobs are created and Job 1 is queued
        recipe_job_1 = RecipeJob.objects.select_related('job').get(recipe_id=handler.recipe.id, job_name='Job 1')
        self.assertEqual(recipe_job_1.job.job_type.id, self.job_type_1.id)
        self.assertEqual(recipe_job_1.job.status, 'QUEUED')
        self.assertEqual(recipe_job_1.job.priority, 1111)

    def test_successful_supersede(self):
        """Tests calling QueueManager.queue_new_recipe() successfully when superseding a recipe."""

        # Queue initial recipe and complete its first job
        handler = Queue.objects.queue_new_recipe(self.recipe_type, self.data, self.event)
        recipe = Recipe.objects.get(id=handler.recipe.id)
        recipe_job_1 = RecipeJob.objects.select_related('job')
        recipe_job_1 = recipe_job_1.get(recipe_id=handler.recipe.id, job_name='Job 1')
        Job.objects.update_jobs_to_running([recipe_job_1.job], now())
        results = JobResults()
        results.add_file_list_parameter('Test Output 1', [product_test_utils.create_product().id])
        job_test_utils.create_job_exe(job=recipe_job_1.job, status='COMPLETED', output=results)
        Job.objects.update_jobs_to_completed([recipe_job_1.job], now())
        Job.objects.process_job_output([recipe_job_1.job_id], now())

        # Create a new recipe type that has a new version of job 2 (job 1 is identical)
        new_job_type_2 = job_test_utils.create_job_type(name=self.job_type_2.name, version='New Version',
                                                        interface=self.job_type_2.interface)
        new_definition = {
            'version': '1.0',
            'input_data': [{
                'name': 'Recipe Input',
                'type': 'file',
                'media_types': ['text/plain'],
            }],
            'jobs': [{
                'name': 'New Job 1',
                'job_type': {
                    'name': self.job_type_1.name,
                    'version': self.job_type_1.version,
                },
                'recipe_inputs': [{
                    'recipe_input': 'Recipe Input',
                    'job_input': 'Test Input 1',
                }]
            }, {
                'name': 'New Job 2',
                'job_type': {
                    'name': new_job_type_2.name,
                    'version': new_job_type_2.version,
                },
                'dependencies': [{
                    'name': 'New Job 1',
                    'connections': [{
                        'output': 'Test Output 1',
                        'input': 'Test Input 2',
                    }]
                }]
            }]
        }
        new_recipe_type = recipe_test_utils.create_recipe_type(name=self.recipe_type.name, definition=new_definition)
        event = trigger_test_utils.create_trigger_event()
        recipe_job_1 = RecipeJob.objects.select_related('job').get(recipe_id=handler.recipe.id, job_name='Job 1')
        recipe_job_2 = RecipeJob.objects.select_related('job').get(recipe_id=handler.recipe.id, job_name='Job 2')
        superseded_jobs = {'Job 1': recipe_job_1.job, 'Job 2': recipe_job_2.job}
        graph_a = self.recipe_type.get_recipe_definition().get_graph()
        graph_b = new_recipe_type.get_recipe_definition().get_graph()
        delta = RecipeGraphDelta(graph_a, graph_b)

        # Queue new recipe that supersedes the old recipe
        new_handler = Queue.objects.queue_new_recipe(new_recipe_type, None, event, superseded_recipe=recipe,
                                                     delta=delta, superseded_jobs=superseded_jobs)

        # Ensure old recipe is superseded
        recipe = Recipe.objects.get(id=handler.recipe.id)
        self.assertTrue(recipe.is_superseded)

        # Ensure new recipe supersedes old recipe
        new_recipe = Recipe.objects.get(id=new_handler.recipe.id)
        self.assertEqual(new_recipe.superseded_recipe_id, handler.recipe.id)

        # Ensure that job 1 is already completed (it was copied from original recipe) and that job 2 is queued
        new_recipe_job_1 = RecipeJob.objects.select_related('job').get(recipe_id=new_handler.recipe.id,
                                                                       job_name='New Job 1')
        new_recipe_job_2 = RecipeJob.objects.select_related('job').get(recipe_id=new_handler.recipe.id,
                                                                       job_name='New Job 2')
        self.assertEqual(new_recipe_job_1.job.status, 'COMPLETED')
        self.assertFalse(new_recipe_job_1.is_original)
        self.assertEqual(new_recipe_job_2.job.status, 'QUEUED')
        self.assertTrue(new_recipe_job_2.is_original)


class TestQueueManagerRequeueJobs(TransactionTestCase):

    def setUp(self):
        django.setup()

        self.new_priority = 200
        self.standalone_failed_job = job_test_utils.create_job(status='FAILED', num_exes=3, priority=100)
        self.standalone_superseded_job = job_test_utils.create_job(status='FAILED', num_exes=1)
        self.standalone_canceled_job = job_test_utils.create_job(status='CANCELED', num_exes=1, priority=100)
        self.standalone_completed_job = job_test_utils.create_job(status='COMPLETED')
        Job.objects.supersede_jobs([self.standalone_superseded_job], now())

        # Create recipe for re-queing a job that should now be PENDING (and its dependencies)
        job_type_a_1 = job_test_utils.create_job_type()
        job_type_a_2 = job_test_utils.create_job_type()
        definition_a = {
            'version': '1.0',
            'input_data': [],
            'jobs': [{
                'name': 'Job 1',
                'job_type': {
                    'name': job_type_a_1.name,
                    'version': job_type_a_1.version,
                }
            }, {
                'name': 'Job 2',
                'job_type': {
                    'name': job_type_a_2.name,
                    'version': job_type_a_2.version,
                },
                'dependencies': [{
                    'name': 'Job 1'
                }],
            }],
        }
        recipe_type_a = recipe_test_utils.create_recipe_type(definition=definition_a)
        self.job_a_1 = job_test_utils.create_job(job_type=job_type_a_1, status='FAILED', num_exes=1)
        self.job_a_2 = job_test_utils.create_job(job_type=job_type_a_2, status='BLOCKED')
        data_a = {
            'version': '1.0',
            'input_data': [],
            'workspace_id': 1,
        }
        recipe_a = recipe_test_utils.create_recipe(recipe_type=recipe_type_a, input=data_a)
        recipe_test_utils.create_recipe_job(recipe=recipe_a, job_name='Job 1', job=self.job_a_1)
        recipe_test_utils.create_recipe_job(recipe=recipe_a, job_name='Job 2', job=self.job_a_2)

        # Create recipe for re-queing a job that should now be BLOCKED (and its dependencies)
        job_type_b_1 = job_test_utils.create_job_type()
        job_type_b_2 = job_test_utils.create_job_type()
        job_type_b_3 = job_test_utils.create_job_type()
        definition_b = {
            'version': '1.0',
            'input_data': [],
            'jobs': [{
                'name': 'Job 1',
                'job_type': {
                    'name': job_type_b_1.name,
                    'version': job_type_b_1.version,
                }
            }, {
                'name': 'Job 2',
                'job_type': {
                    'name': job_type_b_2.name,
                    'version': job_type_b_2.version,
                },
                'dependencies': [{
                    'name': 'Job 1'
                }],
            }, {
                'name': 'Job 3',
                'job_type': {
                    'name': job_type_b_3.name,
                    'version': job_type_b_3.version,
                },
                'dependencies': [{
                    'name': 'Job 2'
                }],
            }],
        }
        recipe_type_b = recipe_test_utils.create_recipe_type(definition=definition_b)
        self.job_b_1 = job_test_utils.create_job(job_type=job_type_b_1, status='FAILED')
        self.job_b_2 = job_test_utils.create_job(job_type=job_type_b_2, status='CANCELED', num_exes=0)
        self.job_b_3 = job_test_utils.create_job(job_type=job_type_b_3, status='BLOCKED', num_exes=0)
        data_b = {
            'version': '1.0',
            'input_data': [],
            'workspace_id': 1,
        }
        recipe_b = recipe_test_utils.create_recipe(recipe_type=recipe_type_b, input=data_b)
        recipe_test_utils.create_recipe_job(recipe=recipe_b, job_name='Job 1', job=self.job_b_1)
        recipe_test_utils.create_recipe_job(recipe=recipe_b, job_name='Job 2', job=self.job_b_2)
        recipe_test_utils.create_recipe_job(recipe=recipe_b, job_name='Job 3', job=self.job_b_3)

        # Job IDs to re-queue
        self.job_ids = [self.standalone_failed_job.id, self.standalone_canceled_job.id,
                        self.standalone_completed_job.id, self.job_a_1.id, self.job_b_2.id]

    def test_successful(self):
        """Tests calling QueueManager.requeue_jobs() successfully"""

        Queue.objects.requeue_jobs(self.job_ids, self.new_priority)

        standalone_failed_job = Job.objects.get(id=self.standalone_failed_job.id)
        self.assertEqual(standalone_failed_job.status, 'QUEUED')
        self.assertEqual(standalone_failed_job.max_tries, 4)

        standalone_canceled_job = Job.objects.get(id=self.standalone_canceled_job.id)
        self.assertEqual(standalone_canceled_job.status, 'QUEUED')
        self.assertEqual(standalone_canceled_job.max_tries, 2)

        # Superseded job should not be re-queued
        standalone_superseded_job = Job.objects.get(id=self.standalone_superseded_job.id)
        self.assertEqual(standalone_superseded_job.status, 'FAILED')

        # Completed job should not be re-queued
        standalone_completed_job = Job.objects.get(id=self.standalone_completed_job.id)
        self.assertEqual(standalone_completed_job.status, 'COMPLETED')

        job_a_1 = Job.objects.get(id=self.job_a_1.id)
        self.assertEqual(job_a_1.status, 'QUEUED')
        job_a_2 = Job.objects.get(id=self.job_a_2.id)
        self.assertEqual(job_a_2.status, 'PENDING')

        job_b_1 = Job.objects.get(id=self.job_b_1.id)
        self.assertEqual(job_b_1.status, 'FAILED')
        job_b_2 = Job.objects.get(id=self.job_b_2.id)
        self.assertEqual(job_b_2.status, 'BLOCKED')
        job_b_3 = Job.objects.get(id=self.job_b_3.id)
        self.assertEqual(job_b_3.status, 'BLOCKED')
