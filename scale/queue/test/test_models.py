from __future__ import unicode_literals

import time
from datetime import timedelta

import django
from django.utils.timezone import now
from django.test import TestCase, TransactionTestCase
from mock import MagicMock

import error.test.utils as error_test_utils
import job.test.utils as job_test_utils
import product.test.utils as product_test_utils
import recipe.test.utils as recipe_test_utils
import storage.test.utils as storage_test_utils
import source.test.utils as source_test_utils
import trigger.test.utils as trigger_test_utils
from job.configuration.data.exceptions import StatusError
from job.configuration.results.job_results import JobResults
from job.configuration.results.results_manifest.results_manifest import ResultsManifest
from job.models import Job
from job.models import JobExecution
from queue.models import JobLoad, Queue, QueueEventProcessor
from recipe.configuration.definition.recipe_definition import RecipeDefinition
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
                self.fail('Found unexpected job type: %s', result.job_type_id)


class TestQueueManagerHandleJobCancellation(TransactionTestCase):

    def setUp(self):
        django.setup()

    def test_successful_with_pending_job(self):
        """Tests calling QueueManager.handle_job_cancellation() successfully with a pending job."""

        # Create the job
        job = job_test_utils.create_job(status='PENDING')

        # Call method to test
        Queue.objects.handle_job_cancellation(job.id, now())

        # Make sure job is canceled (there should be no job executions)
        final_job = Job.objects.get(pk=job.id)
        self.assertEqual(final_job.status, 'CANCELED')
        self.assertEqual(JobExecution.objects.filter(job_id=job.id).count(), 0)

    def test_successful_with_blocked_job(self):
        """Tests calling QueueManager.handle_job_cancellation() successfully with a blocked job."""

        # Create the job
        job = job_test_utils.create_job(status='BLOCKED')

        # Call method to test
        Queue.objects.handle_job_cancellation(job.id, now())

        # Make sure job is canceled (there should be no job executions)
        final_job = Job.objects.get(pk=job.id)
        self.assertEqual(final_job.status, 'CANCELED')
        self.assertEqual(JobExecution.objects.filter(job_id=job.id).count(), 0)

    def test_successful_with_queued_job(self):
        """Tests calling QueueManager.handle_job_cancellation() successfully with a queued job."""

        # Queue the job
        job = job_test_utils.create_job()
        job_exe = Queue.objects._queue_jobs([job])[0]
        job_exe_id = job_exe.id

        # Call method to test
        Queue.objects.handle_job_cancellation(job.id, now())

        # Make sure job is canceled and queue model is gone
        final_job = Job.objects.get(pk=job.id)
        final_job_exe = JobExecution.objects.get(pk=job_exe_id)
        self.assertEqual(final_job.status, 'CANCELED')
        self.assertEqual(final_job_exe.status, 'CANCELED')
        self.assertEqual(Queue.objects.filter(job_exe_id=job_exe_id).count(), 0)

    def test_successful_with_running_job(self):
        """Tests calling QueueManager.handle_job_cancellation() successfully with a running job."""

        # Create the running job
        job_exe = job_test_utils.create_job_exe()

        # Call method to test
        Queue.objects.handle_job_cancellation(job_exe.job_id, now())

        # Make sure job is canceled
        final_job = Job.objects.get(pk=job_exe.job_id)
        final_job_exe = JobExecution.objects.get(pk=job_exe.id)
        self.assertEqual(final_job.status, 'CANCELED')
        self.assertEqual(final_job_exe.status, 'CANCELED')

    def test_successful_with_failed_job(self):
        """Tests calling QueueManager.handle_job_cancellation() successfully with a failed job."""

        # Create the failed job
        job = job_test_utils.create_job(status='FAILED')
        job_exe_1 = job_test_utils.create_job_exe(job=job, status='FAILED')
        time.sleep(0.001)
        job_exe_2 = job_test_utils.create_job_exe(job=job, status='FAILED')
        time.sleep(0.001)
        job_exe_3 = job_test_utils.create_job_exe(job=job, status='FAILED')

        # Call method to test
        Queue.objects.handle_job_cancellation(job.id, now())

        # Make sure job is canceled (execution stays FAILED)
        final_job = Job.objects.get(pk=job.id)
        final_job_exe = JobExecution.objects.get(pk=job_exe_3.id)
        self.assertEqual(final_job.status, 'CANCELED')
        self.assertEqual(final_job_exe.status, 'FAILED')

    def test_exception_with_completed_job(self):
        """Tests calling QueueManager.handle_job_cancellation() with a completed job that results in an exception."""

        # Create the completed job
        job = job_test_utils.create_job(status='COMPLETED')
        job_exe_1 = job_test_utils.create_job_exe(job=job, status='FAILED')
        time.sleep(0.001)
        job_exe_2 = job_test_utils.create_job_exe(job=job, status='COMPLETED')

        # Call method to test
        self.assertRaises(Exception, Queue.objects.handle_job_cancellation, job.id, now())

    def test_exception_with_canceled_job(self):
        """Tests calling QueueManager.handle_job_cancellation() with a canceled job that results in an exception."""

        # Create the canceled job
        job = job_test_utils.create_job(status='CANCELED')
        job_exe_1 = job_test_utils.create_job_exe(job=job, status='FAILED')
        time.sleep(0.001)
        job_exe_2 = job_test_utils.create_job_exe(job=job, status='CANCELED')

        # Call method to test
        self.assertRaises(Exception, Queue.objects.handle_job_cancellation, job.id, now())


class TestQueueManagerHandleJobCompletion(TransactionTestCase):

    def setUp(self):
        django.setup()

        self.workspace = storage_test_utils.create_workspace()
        source_file = source_test_utils.create_source(workspace=self.workspace)

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

        self.data = {
            'version': '1.0',
            'input_data': [{
                'name': 'Recipe Input',
                'file_id': source_file.id,
            }],
            'workspace_id': self.workspace.id,
        }

        # Register a fake processor
        self.mock_processor = MagicMock(QueueEventProcessor)
        Queue.objects.register_processor(lambda: self.mock_processor)

    def test_successful_with_partial_recipe(self):
        """Tests calling QueueManager.handle_job_completion() successfully with a job in a recipe."""

        # Queue the recipe
        recipe_id = Queue.objects.queue_new_recipe(self.recipe_type, self.data, self.event)

        # Fake out completing Job 1
        job_1 = RecipeJob.objects.select_related('job').get(recipe_id=recipe_id, job_name='Job 1').job
        job_exe_1 = JobExecution.objects.get(job_id=job_1.id)
        output_file_1 = product_test_utils.create_product(job_exe=job_exe_1, workspace=self.workspace)
        output_file_2 = product_test_utils.create_product(job_exe=job_exe_1, workspace=self.workspace)

        results = JobResults()
        results.add_file_list_parameter('Test Output 1', [output_file_1.id, output_file_2.id])
        JobExecution.objects.post_steps_results(job_exe_1.id, results, ResultsManifest())

        Job.objects.filter(pk=job_1.id).update(status='RUNNING')
        JobExecution.objects.filter(pk=job_exe_1.id).update(status='RUNNING')

        # Call method to test
        Queue.objects.handle_job_completion(job_exe_1.id, now())

        # Make sure processor was called
        self.assertTrue(self.mock_processor.process_completed.called)

        # Make sure Job 2 in the recipe is successfully queued
        recipe_job_2 = RecipeJob.objects.select_related('job', 'recipe').get(recipe_id=recipe_id, job_name='Job 2')
        self.assertEqual(recipe_job_2.job.status, 'QUEUED')
        self.assertIsNone(recipe_job_2.recipe.completed)

    def test_successful_with_full_recipe(self):
        """Tests calling QueueManager.handle_job_completion() successfully with all jobs in a recipe."""

        # Queue the recipe
        recipe_id = Queue.objects.queue_new_recipe(self.recipe_type, self.data, self.event)

        # Fake out completing Job 1
        job_1 = RecipeJob.objects.select_related('job').get(recipe_id=recipe_id, job_name='Job 1').job
        job_exe_1 = JobExecution.objects.get(job_id=job_1.id)
        output_file_1 = product_test_utils.create_product(job_exe=job_exe_1, workspace=self.workspace)
        output_file_2 = product_test_utils.create_product(job_exe=job_exe_1, workspace=self.workspace)

        results = JobResults()
        results.add_file_list_parameter('Test Output 1', [output_file_1.id, output_file_2.id])
        JobExecution.objects.post_steps_results(job_exe_1.id, results, ResultsManifest())

        Job.objects.filter(pk=job_1.id).update(status='RUNNING')
        JobExecution.objects.filter(pk=job_exe_1.id).update(status='RUNNING')

        Queue.objects.handle_job_completion(job_exe_1.id, now())

        # Fake out completing Job 2
        job_2 = RecipeJob.objects.select_related('job').get(recipe_id=recipe_id, job_name='Job 2').job
        job_exe_2 = JobExecution.objects.get(job_id=job_2.id)
        output_file_1 = product_test_utils.create_product(job_exe=job_exe_2, workspace=self.workspace)
        output_file_2 = product_test_utils.create_product(job_exe=job_exe_2, workspace=self.workspace)

        results = JobResults()
        results.add_file_list_parameter('Test Output 2', [output_file_1.id, output_file_2.id])
        JobExecution.objects.post_steps_results(job_exe_2.id, results, ResultsManifest())

        Job.objects.filter(pk=job_2.id).update(status='RUNNING')
        JobExecution.objects.filter(pk=job_exe_2.id).update(status='RUNNING')

        # Call method to test
        Queue.objects.handle_job_completion(job_exe_2.id, now())

        # Make sure processor was called
        self.assertEqual(self.mock_processor.process_completed.call_count, 2)

        # Make sure final recipe attributes are updated
        recipe = Recipe.objects.get(pk=recipe_id)
        self.assertIsNotNone(recipe.completed)


class TestQueueManagerQueueNewRecipe(TransactionTestCase):

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

        self.data = {
            'version': '1.0',
            'input_data': [{
                'name': 'Recipe Input',
                'file_id': source_file.id,
            }],
            'workspace_id': workspace.id,
        }

        # Register a fake processor
        self.mock_processor = MagicMock(QueueEventProcessor)
        Queue.objects.register_processor(lambda: self.mock_processor)

    def test_successful(self):
        """Tests calling QueueManager.queue_new_recipe() successfully."""

        recipe_id = Queue.objects.queue_new_recipe(self.recipe_type, self.data, self.event)

        # Make sure the recipe jobs are created and Job 1 is queued
        recipe_job_1 = RecipeJob.objects.select_related('job').get(recipe_id=recipe_id, job_name='Job 1')
        self.assertEqual(recipe_job_1.job.job_type.id, self.job_type_1.id)
        self.assertEqual(recipe_job_1.job.status, 'QUEUED')

        # Make sure processor was called
        job_exe_1 = JobExecution.objects.get(job=recipe_job_1.job)
        self.assertTrue(self.mock_processor.process_queued.called_with(job_exe_1, True))

        recipe_job_2 = RecipeJob.objects.select_related('job').get(recipe_id=recipe_id, job_name='Job 2')
        self.assertEqual(recipe_job_2.job.job_type.id, self.job_type_2.id)
        self.assertEqual(recipe_job_2.job.status, 'PENDING')

        recipe = Recipe.objects.get(pk=recipe_id)
        self.assertIsNone(recipe.completed)


class TestQueueManagerRequeueExistingJob(TransactionTestCase):

    def setUp(self):
        django.setup()

        workspace = storage_test_utils.create_workspace()
        source_file = source_test_utils.create_source(workspace=workspace)

        self.data = {
            'version': '1.0',
            'input_data': [{
                'name': 'Recipe Input',
                'file_id': source_file.id,
            }],
            'workspace_id': workspace.id,
        }

        self.job_type = job_test_utils.create_job_type()

        # Register a fake processor
        self.mock_processor = MagicMock(QueueEventProcessor)
        Queue.objects.register_processor(lambda: self.mock_processor)

    def test_invalid_status(self):
        """Tests rejecting requeue of existing job with an incorrect status."""
        job = job_test_utils.create_job(job_type=self.job_type, status='RUNNING')

        self.assertRaises(StatusError, Queue.objects.requeue_existing_job, job.id)

    def test_successful(self):
        """Tests calling QueueManager.requeue_existing_job() successfully."""
        job = job_test_utils.create_job(job_type=self.job_type, status='FAILED', error=error_test_utils.create_error(),
                                        data=self.data, num_exes=1)

        old_max_tries = job.max_tries
        job_exe = Queue.objects.requeue_existing_job(job.id)

        # Make sure processor was called
        self.assertTrue(self.mock_processor.process_queued.called_with(job_exe, False))

        # Make sure the job attributes were updated (must refresh the model first)
        job = Job.objects.get(pk=job.id)
        self.assertGreater(job.max_tries, old_max_tries)
        self.assertIsNone(job.error)

        # Make sure a job execution was queued
        self.assertTrue(Queue.objects.get(job_exe=job_exe))


class TestQueueManagerRequeueJobs(TransactionTestCase):

    def setUp(self):
        django.setup()

        self.new_priority = 200
        self.standalone_failed_job = job_test_utils.create_job(status='FAILED', num_exes=3, priority=100)
        self.standalone_canceled_job = job_test_utils.create_job(status='CANCELED', num_exes=1, priority=100)
        self.standalone_completed_job = job_test_utils.create_job(status='COMPLETED')

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
        recipe_a = recipe_test_utils.create_recipe(recipe_type=recipe_type_a, data=data_a)
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
        self.job_b_2 = job_test_utils.create_job(job_type=job_type_b_2, status='CANCELED')
        self.job_b_3 = job_test_utils.create_job(job_type=job_type_b_3, status='BLOCKED')
        data_b = {
            'version': '1.0',
            'input_data': [],
            'workspace_id': 1,
        }
        recipe_b = recipe_test_utils.create_recipe(recipe_type=recipe_type_b, data=data_b)
        recipe_test_utils.create_recipe_job(recipe=recipe_b, job_name='Job 1', job=self.job_b_1)
        recipe_test_utils.create_recipe_job(recipe=recipe_b, job_name='Job 2', job=self.job_b_2)
        recipe_test_utils.create_recipe_job(recipe=recipe_b, job_name='Job 3', job=self.job_b_3)

        # Job IDs to re-queue
        self.job_ids = [self.standalone_failed_job.id, self.standalone_canceled_job.id,
                        self.standalone_completed_job.id, self.job_a_1.id, self.job_b_2.id]

        # Register a fake processor
        self.mock_processor = MagicMock(QueueEventProcessor)
        Queue.objects.register_processor(lambda: self.mock_processor)

    def test_successful(self):
        """Tests calling QueueManager.requeue_jobs() successfully"""

        Queue.objects.requeue_jobs(self.job_ids, self.new_priority)

        standalone_failed_job = Job.objects.get(id=self.standalone_failed_job.id)
        self.assertEqual(standalone_failed_job.status, 'QUEUED')
        self.assertEqual(standalone_failed_job.max_tries, 4)
        self.assertEqual(standalone_failed_job.priority, self.new_priority)

        standalone_canceled_job = Job.objects.get(id=self.standalone_canceled_job.id)
        self.assertEqual(standalone_canceled_job.status, 'QUEUED')
        self.assertEqual(standalone_canceled_job.max_tries, 2)
        self.assertEqual(standalone_canceled_job.priority, self.new_priority)

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
