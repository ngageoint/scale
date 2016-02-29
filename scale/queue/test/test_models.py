#@PydevCodeAnalysisIgnore
from __future__ import unicode_literals

import time
from datetime import timedelta

import django
from django.utils.timezone import now
from django.test import TestCase, TransactionTestCase
from mock import MagicMock

import error.test.utils as error_test_utils
import job.test.utils as job_test_utils
import node.test.utils as node_test_utils
import product.test.utils as product_test_utils
import recipe.test.utils as recipe_test_utils
import shared_resource.test.utils as shared_resource_test_utils
import storage.test.utils as storage_test_utils
import source.test.utils as source_test_utils
import trigger.test.utils as trigger_test_utils
from job.configuration.data.exceptions import StatusError
from job.configuration.results.job_results import JobResults
from job.configuration.results.results_manifest.results_manifest import ResultsManifest
from job.models import Job
from job.models import JobExecution
from queue.models import JobLoad, Queue, QueueDepthByJobType, QueueDepthByPriority, QueueEventProcessor
from recipe.configuration.definition.recipe_definition import RecipeDefinition
from recipe.models import Recipe, RecipeJob


class TestJobLoadManager(TestCase):

    def setUp(self):
        django.setup()

    def test_calculate_empty(self):
        '''Tests calculating job load when there are no jobs.'''

        JobLoad.objects.calculate()
        results = JobLoad.objects.all()

        self.assertEqual(len(results), 1)

    def test_calculate_status(self):
        '''Tests calculating job load filtering by status.'''

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
        '''Tests calculating job load grouping by job type.'''

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


# TODO: Remove this once the UI migrates to /load
class TestQueueManagerGetCurrentQueueDepth(TestCase):

    def setUp(self):
        django.setup()

        self.job_type_1 = job_test_utils.create_job_type(priority=1)
        self.job_type_2 = job_test_utils.create_job_type(priority=1)
        self.job_type_3 = job_test_utils.create_job_type(priority=3)
        self.job_type_4 = job_test_utils.create_job_type(priority=4)
        self.job_type_5 = job_test_utils.create_job_type(priority=4)

        self.trigger_event_1 = trigger_test_utils.create_trigger_event()

    def test_successful_with_nonempty_queue(self):
        '''Tests QueueManager.get_current_queue_depth() successfully with a non-empty queue.'''

        # Set up queue
        Queue.objects.queue_new_job(self.job_type_1, {}, self.trigger_event_1)
        Queue.objects.queue_new_job(self.job_type_1, {}, self.trigger_event_1)
        Queue.objects.queue_new_job(self.job_type_1, {}, self.trigger_event_1)
        Queue.objects.queue_new_job(self.job_type_2, {}, self.trigger_event_1)
        Queue.objects.queue_new_job(self.job_type_2, {}, self.trigger_event_1)
        Queue.objects.queue_new_job(self.job_type_3, {}, self.trigger_event_1)
        Queue.objects.queue_new_job(self.job_type_3, {}, self.trigger_event_1)
        Queue.objects.queue_new_job(self.job_type_3, {}, self.trigger_event_1)
        Queue.objects.queue_new_job(self.job_type_3, {}, self.trigger_event_1)
        Queue.objects.queue_new_job(self.job_type_3, {}, self.trigger_event_1)
        Queue.objects.queue_new_job(self.job_type_3, {}, self.trigger_event_1)
        Queue.objects.queue_new_job(self.job_type_3, {}, self.trigger_event_1)
        Queue.objects.queue_new_job(self.job_type_4, {}, self.trigger_event_1)
        Queue.objects.queue_new_job(self.job_type_5, {}, self.trigger_event_1)

        dict_tuple = Queue.objects.get_current_queue_depth()

        # Check depth by job type
        self.assertDictEqual(dict_tuple[0], {self.job_type_1.id: 3, self.job_type_2.id: 2, self.job_type_3.id: 7,
                                             self.job_type_4.id: 1, self.job_type_5.id: 1})

        # Check depth by priority
        self.assertDictEqual(dict_tuple[1], {1: 5, 3: 7, 4: 2})

    def test_successful_with_empty_queue(self):
        '''Tests QueueManager.get_current_queue_depth() successfully with an empty queue.'''

        dict_tuple = Queue.objects.get_current_queue_depth()

        # Check depth by job type
        self.assertDictEqual(dict_tuple[0], {})

        # Check depth by priority
        self.assertDictEqual(dict_tuple[1], {})


# TODO: Remove this once the UI migrates to /load
class TestQueueManagerGetHistoricalQueueDepth(TestCase):

    def setUp(self):
        django.setup()

        self.job_type_1 = job_test_utils.create_job_type(priority=1)
        self.job_type_2 = job_test_utils.create_job_type(priority=1)
        self.job_type_3 = job_test_utils.create_job_type(priority=3)
        self.job_type_4 = job_test_utils.create_job_type(priority=4)
        self.job_type_5 = job_test_utils.create_job_type(priority=4)

        self.time_1 = now()
        self.time_2 = self.time_1 + timedelta(hours=1)
        self.time_3 = self.time_2 + timedelta(hours=1)

        # Set up queue depth entries
        QueueDepthByJobType.objects.create(job_type=self.job_type_1, depth_time=self.time_1, depth=5)
        QueueDepthByJobType.objects.create(job_type=self.job_type_2, depth_time=self.time_1, depth=7)
        QueueDepthByJobType.objects.create(job_type=self.job_type_3, depth_time=self.time_1, depth=3)
        QueueDepthByJobType.objects.create(job_type=self.job_type_4, depth_time=self.time_1, depth=1)
        QueueDepthByJobType.objects.create(job_type=self.job_type_1, depth_time=self.time_2, depth=25)
        QueueDepthByJobType.objects.create(job_type=self.job_type_2, depth_time=self.time_2, depth=19)
        QueueDepthByJobType.objects.create(job_type=self.job_type_4, depth_time=self.time_2, depth=10)
        QueueDepthByJobType.objects.create(job_type=self.job_type_1, depth_time=self.time_3, depth=0)

        QueueDepthByPriority.objects.create(priority=1, depth_time=self.time_1, depth=12)
        QueueDepthByPriority.objects.create(priority=3, depth_time=self.time_1, depth=3)
        QueueDepthByPriority.objects.create(priority=4, depth_time=self.time_1, depth=1)
        QueueDepthByPriority.objects.create(priority=1, depth_time=self.time_2, depth=44)
        QueueDepthByPriority.objects.create(priority=4, depth_time=self.time_2, depth=10)
        QueueDepthByPriority.objects.create(priority=1, depth_time=self.time_3, depth=0)

    def test_successful_with_nonempty_range(self):
        '''Tests QueueManager.get_historical_queue_depth() successfully with a non-empty time range.'''

        results = Queue.objects.get_historical_queue_depth(self.time_1, self.time_3)

        # Check job types list
        expected_job_type_list = [
            {'id': self.job_type_1.id, 'name': self.job_type_1.name, 'version': self.job_type_1.version},
            {'id': self.job_type_2.id, 'name': self.job_type_2.name, 'version': self.job_type_2.version},
            {'id': self.job_type_3.id, 'name': self.job_type_3.name, 'version': self.job_type_3.version},
            {'id': self.job_type_4.id, 'name': self.job_type_4.name, 'version': self.job_type_4.version},
        ]
        self.assertItemsEqual(expected_job_type_list, results['job_types'])

        # Check priorities list
        expected_priorities_list = [{'priority': 1}, {'priority': 3}, {'priority': 4}]
        self.assertItemsEqual(expected_priorities_list, results['priorities'])

        # Check time point 1
        time_1_dict = results['queue_depths'][0]
        self.assertEqual(self.time_1, time_1_dict['time'])
        self.assertEqual(16, time_1_dict['total_depth'])
        self.assertItemsEqual([5, 7, 3, 1], time_1_dict['depth_per_job_type'])
        self.assertItemsEqual([12, 3, 1], time_1_dict['depth_per_priority'])

        # Check time point 2
        time_2_dict = results['queue_depths'][1]
        self.assertEqual(self.time_2, time_2_dict['time'])
        self.assertEqual(54, time_2_dict['total_depth'])
        self.assertItemsEqual([25, 19, 10, 0], time_2_dict['depth_per_job_type'])
        self.assertItemsEqual([44, 10, 0], time_2_dict['depth_per_priority'])

        # Check time point 3
        time_3_dict = results['queue_depths'][2]
        self.assertEqual(self.time_3, time_3_dict['time'])
        self.assertEqual(0, time_3_dict['total_depth'])
        self.assertItemsEqual([0, 0, 0, 0], time_3_dict['depth_per_job_type'])
        self.assertItemsEqual([0, 0, 0], time_3_dict['depth_per_priority'])

    def test_successful_with_empty_range(self):
        '''Tests QueueManager.get_historical_queue_depth() successfully with an empty time range (no time points).'''

        results = Queue.objects.get_historical_queue_depth(self.time_1 - timedelta(hours=2),
                                                           self.time_1 - timedelta(hours=1))

        # Check results
        self.assertDictEqual({'job_types': [], 'priorities': [], 'queue_depths': []}, results)

    def test_successful_with_zero_point(self):
        '''Tests QueueManager.get_historical_queue_depth() successfully with a single time point with zero depth'''

        results = Queue.objects.get_historical_queue_depth(self.time_3 - timedelta(minutes=5),
                                                           self.time_3 + timedelta(minutes=5))

        # Check results
        expected = {
            'job_types': [],
            'priorities': [],
            'queue_depths': [{
                'time': self.time_3,
                'total_depth': 0,
                'depth_per_job_type': [],
                'depth_per_priority': [],
            }]
        }
        self.assertDictEqual(expected, results)


class TestQueueManagerHandleJobCancellation(TransactionTestCase):

    def setUp(self):
        django.setup()

    def test_successful_with_pending_job(self):
        '''Tests calling QueueManager.handle_job_cancellation() successfully with a pending job.'''

        # Create the job
        job = job_test_utils.create_job(status='PENDING')

        # Call method to test
        Queue.objects.handle_job_cancellation(job.id, now())

        # Make sure job is canceled (there should be no job executions)
        final_job = Job.objects.get(pk=job.id)
        self.assertEqual(final_job.status, 'CANCELED')
        self.assertEqual(JobExecution.objects.filter(job_id=job.id).count(), 0)

    def test_successful_with_blocked_job(self):
        '''Tests calling QueueManager.handle_job_cancellation() successfully with a blocked job.'''

        # Create the job
        job = job_test_utils.create_job(status='BLOCKED')

        # Call method to test
        Queue.objects.handle_job_cancellation(job.id, now())

        # Make sure job is canceled (there should be no job executions)
        final_job = Job.objects.get(pk=job.id)
        self.assertEqual(final_job.status, 'CANCELED')
        self.assertEqual(JobExecution.objects.filter(job_id=job.id).count(), 0)

    def test_successful_with_queued_job(self):
        '''Tests calling QueueManager.handle_job_cancellation() successfully with a queued job.'''

        # Queue the job
        job = job_test_utils.create_job()
        job_exe_id = Queue.objects.queue_existing_job(job, {})

        # Call method to test
        Queue.objects.handle_job_cancellation(job.id, now())

        # Make sure job is canceled and queue model is gone
        final_job = Job.objects.get(pk=job.id)
        final_job_exe = JobExecution.objects.get(pk=job_exe_id)
        self.assertEqual(final_job.status, 'CANCELED')
        self.assertEqual(final_job_exe.status, 'CANCELED')
        self.assertEqual(Queue.objects.filter(job_exe_id=job_exe_id).count(), 0)

    def test_successful_with_running_job(self):
        '''Tests calling QueueManager.handle_job_cancellation() successfully with a running job.'''

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
        '''Tests calling QueueManager.handle_job_cancellation() successfully with a failed job.'''

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
        '''Tests calling QueueManager.handle_job_cancellation() with a completed job that results in an exception.'''

        # Create the completed job
        job = job_test_utils.create_job(status='COMPLETED')
        job_exe_1 = job_test_utils.create_job_exe(job=job, status='FAILED')
        time.sleep(0.001)
        job_exe_2 = job_test_utils.create_job_exe(job=job, status='COMPLETED')

        # Call method to test
        self.assertRaises(Exception, Queue.objects.handle_job_cancellation, job.id, now())

    def test_exception_with_canceled_job(self):
        '''Tests calling QueueManager.handle_job_cancellation() with a canceled job that results in an exception.'''

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
        '''Tests calling QueueManager.handle_job_completion() successfully with a job in a recipe.'''

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
        '''Tests calling QueueManager.handle_job_completion() successfully with all jobs in a recipe.'''

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
        '''Tests calling QueueManager.queue_new_recipe() successfully.'''

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
        '''Tests rejecting requeue of existing job with an incorrect status.'''
        job = job_test_utils.create_job(job_type=self.job_type, status='RUNNING')

        self.assertRaises(StatusError, Queue.objects.requeue_existing_job, job.id)

    def test_successful(self):
        '''Tests calling QueueManager.requeue_existing_job() successfully.'''
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


# TODO: Remove this once the UI migrates to /load
class TestQueueDepthByJobTypeManagerSaveDepths(TestCase):

    def setUp(self):
        django.setup()

    def test_successful_with_nonempty_queue(self):
        '''Tests calling QueueDepthByJobTypeManager.save_depths() successfully with a non-empty queue.'''

        when = now()
        QueueDepthByJobType.objects.save_depths(when, {1: 10, 2: 20})

        depths = QueueDepthByJobType.objects.filter(depth_time=when).order_by('job_type_id')

        self.assertEqual(depths.count(), 2)
        self.assertEqual(depths[0].job_type_id, 1)
        self.assertEqual(depths[0].depth, 10)
        self.assertEqual(depths[1].job_type_id, 2)
        self.assertEqual(depths[1].depth, 20)

    def test_successful_with_empty_queue(self):
        '''Tests calling QueueDepthByJobTypeManager.save_depths() successfully with an empty queue.'''

        when = now()
        QueueDepthByJobType.objects.save_depths(when, {})

        depths = QueueDepthByJobType.objects.filter(depth_time=when)

        # Make sure there is a single model with a count of 0
        self.assertEqual(depths.count(), 1)
        self.assertEqual(depths[0].depth, 0)


# TODO: Remove this once the UI migrates to /load
class TestQueueDepthByPriorityManagerSaveDepths(TestCase):

    def setUp(self):
        django.setup()

    def test_successful_with_nonempty_queue(self):
        '''Tests calling QueueDepthByPriorityManager.save_depths() successfully with a non-empty queue.'''

        when = now()
        QueueDepthByPriority.objects.save_depths(when, {1: 10, 2: 20})

        depths = QueueDepthByPriority.objects.filter(depth_time=when).order_by('priority')

        self.assertEqual(depths.count(), 2)
        self.assertEqual(depths[0].priority, 1)
        self.assertEqual(depths[0].depth, 10)
        self.assertEqual(depths[1].priority, 2)
        self.assertEqual(depths[1].depth, 20)

    def test_successful_with_empty_queue(self):
        '''Tests calling QueueDepthByPriorityManager.save_depths() successfully with an empty queue.'''

        when = now()
        QueueDepthByPriority.objects.save_depths(when, {})

        depths = QueueDepthByPriority.objects.filter(depth_time=when)

        # Make sure there is a single model with a count of 0
        self.assertEqual(depths.count(), 1)
        self.assertEqual(depths[0].depth, 0)
