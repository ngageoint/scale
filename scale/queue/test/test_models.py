from __future__ import unicode_literals

import datetime
import time

import django
from django.utils.timezone import now
from django.test import TestCase, TransactionTestCase
from mock import patch

import ingest.test.utils as ingest_test_utils
import job.test.utils as job_test_utils
import queue.test.utils as queue_test_utils
import recipe.test.utils as recipe_test_utils
import storage.test.utils as storage_test_utils
import source.test.utils as source_test_utils
import trigger.test.utils as trigger_test_utils
from error.models import reset_error_cache
from data.data.data import Data
from data.data.json.data_v6 import convert_data_to_v6_json
from data.data.value import FileValue
from data.data.json.data_v6 import DataV6
from job.configuration.data.job_data import JobData
from job.data.job_data import JobData as JobDataV6
from job.models import Job
from queue.models import JobLoad, Queue, QUEUE_ORDER_FIFO, QUEUE_ORDER_LIFO
from recipe.definition.definition import RecipeDefinition
from recipe.models import Recipe
from recipe.configuration.json.recipe_config_v6 import RecipeConfigurationV6
from recipe.exceptions import InactiveRecipeType


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

        job_type = job_test_utils.create_seed_job_type()
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

        job_type1 = job_test_utils.create_seed_job_type()
        job_test_utils.create_job(job_type=job_type1, status='PENDING')

        job_type2 = job_test_utils.create_seed_job_type()
        job_test_utils.create_job(job_type=job_type2, status='QUEUED')
        job_test_utils.create_job(job_type=job_type2, status='QUEUED')

        job_type3 = job_test_utils.create_seed_job_type()
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


class TestQueueManagerQueueNewJob(TransactionTestCase):

    def setUp(self):
        django.setup()

    @patch('queue.models.CommandMessageManager')
    def test_successful(self, mock_msg_mgr):
        """Tests calling QueueManager.queue_new_job_v6() successfully with a Seed job type"""

        workspace = storage_test_utils.create_workspace()
        source_file = source_test_utils.create_source(workspace=workspace)
        event = trigger_test_utils.create_trigger_event()

        manifest = {
            'seedVersion': '1.0.0',
            'job': {
                'name': 'test-job',
                'jobVersion': '1.0.0',
                'packageVersion': '1.0.0',
                'title': 'Test Job',
                'description': 'This is a test job',
                'maintainer': {
                    'name': 'John Doe',
                    'email': 'jdoe@example.com'
                },
                'timeout': 10,
                'interface': {
                    'command': '',
                    'inputs': {
                        'files': [{'name': 'input_a'}]
                    },
                    'outputs': {
                        'files': [{'name': 'output_a', 'multiple': True, 'pattern': '*.png'}]
                    }
                }
            }
        }
        job_type = job_test_utils.create_seed_job_type(manifest=manifest)

        data_dict = {
            'version': '1.0',
            'input_data': [{
                'name': 'input_a',
                'file_id': source_file.id
            }],
            'output_data': [{
                'name': 'output_a',
                'workspace_id': workspace.id
            }]
        }
        data = JobDataV6(data_dict)

        job = Queue.objects.queue_new_job_v6(job_type, data._new_data, event)
        self.assertEqual(job.status, 'QUEUED')


class TestQueueManagerQueueNewRecipe(TransactionTestCase):

    fixtures = ['basic_system_job_types.json', 'ingest_job_types.json']

    def setUp(self):
        django.setup()

        workspace = storage_test_utils.create_workspace()
        source_file = source_test_utils.create_source(workspace=workspace)
        self.event = trigger_test_utils.create_trigger_event()

        interface_1 = {
            'command': 'test_command',
            'inputs': {
                'files': [{
                    'name': 'Test_Input_1',
                    'mediaTypes': ['text/plain'],
                }]
            },
            'outputs': {
                'files': [{
                    'name': 'Test_Output_1',
                    'pattern': 'outfile*.png',
                    'mediaType': 'image/png',
                }]
            }
        }
        self.job_type_1 = job_test_utils.create_seed_job_type(interface=interface_1)

        interface_2 = {
            'command': 'test_command',
            'inputs': {
                'files': [{
                    'name': 'Test_Input_2',
                    'mediaTypes': ['image/png', 'image/tiff'],
                }]
            },
            'outputs': {
                'files': [{
                    'name': 'Test_Output_2',
                    'pattern': 'outfile*.png',
                    'mediaType': 'image/png'
                }]
            }
        }
        self.job_type_2 = job_test_utils.create_seed_job_type(interface=interface_2)

        definition = {
            'version': '6',
            'input': {'files': [{'name': 'Recipe_Input', 'media_types': ['text/plain']}]},
            'nodes': {
                'job-1': {
                    'dependencies': [],
                    'input': { 'Test_Input_1': {'type': 'recipe', 'input': 'Recipe_Input'}},
                    'node_type': {
                        'node_type': 'job',
                        'job_type_name': self.job_type_1.name,
                        'job_type_version': self.job_type_1.version,
                        'job_type_revision': self.job_type_1.revision_num
                    }
                },
                'job-2': {
                    'dependencies': [{'name': 'job-1'}],
                    'input': { 'Test_Input_2': {'type': 'dependency', 'node': 'job-1', 'output': 'Test_Output_1'}},
                    'node_type': {
                        'node_type': 'job',
                        'job_type_name': self.job_type_2.name,
                        'job_type_version': self.job_type_2.version,
                        'job_type_revision': self.job_type_2.revision_num
                    }
                }
            }
        }
        definition = {
            'version': '6',
            'input': {'files': [{'name': 'Recipe_Input', 'media_types': ['text/plain']}]},
            'nodes': {
                'job-1': {
                    'dependencies': [],
                    'input': { 'Test_Input_1': {'type': 'recipe', 'input': 'Recipe_Input'}},
                    'node_type': {
                        'node_type': 'job',
                        'job_type_name': self.job_type_1.name,
                        'job_type_version': self.job_type_1.version,
                        'job_type_revision': self.job_type_1.revision_num
                    }
                },
                'job-2': {
                    'dependencies': [{'name': 'job-1'}],
                    'input': { 'Test_Input_2': {'type': 'dependency', 'node': 'job-1', 'output': 'Test_Output_1'}},
                    'node_type': {
                        'node_type': 'job',
                        'job_type_name': self.job_type_2.name,
                        'job_type_version': self.job_type_2.version,
                        'job_type_revision': self.job_type_2.revision_num
                    }
                }
            }
        }
        definition = {
            'version': '6',
            'input': {'files': [{'name': 'Recipe_Input', 'media_types': ['text/plain']}]},
            'nodes': {
                'job-1': {
                    'dependencies': [],
                    'input': { 'Test_Input_1': {'type': 'recipe', 'input': 'Recipe_Input'}},
                    'node_type': {
                        'node_type': 'job',
                        'job_type_name': self.job_type_1.name,
                        'job_type_version': self.job_type_1.version,
                        'job_type_revision': self.job_type_1.revision_num
                    }
                },
                'job-2': {
                    'dependencies': [{'name': 'job-1'}],
                    'input': { 'Test_Input_2': {'type': 'dependency', 'node': 'job-1', 'output': 'Test_Output_1'}},
                    'node_type': {
                        'node_type': 'job',
                        'job_type_name': self.job_type_2.name,
                        'job_type_version': self.job_type_2.version,
                        'job_type_revision': self.job_type_2.revision_num
                    }
                }
            }
        }
        definition = {
            'version': '6',
            'input': {'files': [{'name': 'Recipe_Input', 'media_types': ['text/plain']}]},
            'nodes': {
                'job-1': {
                    'dependencies': [],
                    'input': { 'Test_Input_1': {'type': 'recipe', 'input': 'Recipe_Input'}},
                    'node_type': {
                        'node_type': 'job',
                        'job_type_name': self.job_type_1.name,
                        'job_type_version': self.job_type_1.version,
                        'job_type_revision': self.job_type_1.revision_num
                    }
                },
                'job-2': {
                    'dependencies': [{'name': 'job-1'}],
                    'input': { 'Test_Input_2': {'type': 'dependency', 'node': 'job-1', 'output': 'Test_Output_1'}},
                    'node_type': {
                        'node_type': 'job',
                        'job_type_name': self.job_type_2.name,
                        'job_type_version': self.job_type_2.version,
                        'job_type_revision': self.job_type_2.revision_num
                    }
                }
            }
        }

        recipe_definition = RecipeDefinition(definition)

        self.recipe_type = recipe_test_utils.create_recipe_type_v6(definition=definition)

        workspace = storage_test_utils.create_workspace()
        strike_source_file = source_test_utils.create_source(workspace=workspace)
        scan_source_file = source_test_utils.create_source(workspace=workspace)

        data_dict = {
            'version': '1.0',
            'input_data': [{
                'name': 'INPUT_IMAGE',
                'file_id': strike_source_file.id,
            }],
            'output_data': [{
                'name': 'output_a',
                'workspace_id': workspace.id
            }]
        }
        self.data = JobDataV6(data_dict)

    @patch('queue.models.CommandMessageManager')
    def test_successful(self, mock_msg_mgr):
        workspace = storage_test_utils.create_workspace()
        strike_source_file = source_test_utils.create_source(workspace=workspace)
        scan_source_file = source_test_utils.create_source(workspace=workspace)
        event = trigger_test_utils.create_trigger_event()
        recipetype1 = recipe_test_utils.create_recipe_type_v6()

        data = Data()
        data.add_value(FileValue('input_a', [123]))

        config_dict = {'version': '7',
                       'output_workspaces': {'default': workspace.name},
                       'priority': 999}
        config = RecipeConfigurationV6(config_dict).get_configuration()

        created_recipe = Queue.objects.queue_new_recipe_v6(recipetype1, data, event, recipe_config=config)
        self.assertDictEqual(created_recipe.configuration, config_dict)

    @patch('queue.models.CommandMessageManager')
    def test_inactive(self, mock_msg_mgr):
        workspace = storage_test_utils.create_workspace()
        event = trigger_test_utils.create_trigger_event()
        recipetype1 = recipe_test_utils.create_recipe_type_v6(is_active=False)

        data = Data()
        data.add_value(FileValue('input_a', [123]))

        config_dict = {'version': '6',
                       'output_workspaces': {'default': workspace.name},
                       'priority': 999}
        config = RecipeConfigurationV6(config_dict).get_configuration()

        self.assertRaises(InactiveRecipeType, Queue.objects.queue_new_recipe_v6, recipetype1, data, event, recipe_config=config)

    @patch('queue.models.CommandMessageManager')
    def test_successful_ingest(self, mock_msg_mgr):
        workspace = storage_test_utils.create_workspace()
        strike_source_file = source_test_utils.create_source(workspace=workspace)
        strike_event = ingest_test_utils.create_strike_ingest_event(source_file=strike_source_file)
        scan_source_file = source_test_utils.create_source(workspace=workspace)
        scan_event = ingest_test_utils.create_scan_ingest_event(source_file=scan_source_file)

        recipetype1 = recipe_test_utils.create_recipe_type_v6()
        data_dict = {
            'version': '1.0',
            'input_data': [{
                'name': 'INPUT_IMAGE',
                'file_id': strike_source_file.id,
            }],
            'output_data': [{
                'name': 'output_a',
                'workspace_id': workspace.id
            }]
        }
        data = JobDataV6(data_dict)

        config_dict = {'version': '7',
                       'output_workspaces': {'default': workspace.name},
                       'priority': 999}
        config = RecipeConfigurationV6(config_dict).get_configuration()

        created_strike_recipe = Queue.objects.queue_new_recipe_v6(recipetype1, data._new_data, None, strike_event, recipe_config=config)

        self.assertDictEqual(created_strike_recipe.configuration, config_dict)

        data_dict = {
            'version': '1.0',
            'input_data': [{
                'name': 'INPUT_IMAGE',
                'file_id': scan_source_file.id,
            }],
            'output_data': [{
                'name': 'output_a',
                'workspace_id': workspace.id
            }]
        }
        data = JobDataV6(data_dict)
        created_scan_recipe = Queue.objects.queue_new_recipe_v6(recipetype1, data._new_data, None, scan_event, recipe_config=config)

        self.assertDictEqual(created_scan_recipe.configuration, config_dict)

class TestQueueManagerRequeueJobs(TransactionTestCase):

    def setUp(self):
        django.setup()

        data_dict = convert_data_to_v6_json(Data()).get_dict()
        self.new_priority = 200
        self.standalone_queued_job = job_test_utils.create_job(status='QUEUED', input=data_dict, num_exes=3,
                                                               priority=100)
        Queue.objects.queue_jobs([self.standalone_queued_job], requeue=True)
        self.standalone_failed_job = job_test_utils.create_job(status='FAILED', input=data_dict, num_exes=3,
                                                               priority=100)

        self.standalone_superseded_job = job_test_utils.create_job(status='FAILED', input=data_dict, num_exes=1)
        self.standalone_canceled_job = job_test_utils.create_job(status='CANCELED', input=data_dict, num_exes=1,
                                                                 priority=100)
        self.standalone_completed_job = job_test_utils.create_job(status='COMPLETED', input=data_dict,)
        Job.objects.supersede_jobs([self.standalone_superseded_job.id], now())

        # Create recipe for re-queueing a job that should now be PENDING (and its dependencies)
        job_type_a_1 = job_test_utils.create_seed_job_type()
        job_type_a_2 = job_test_utils.create_seed_job_type()
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
        recipe_type_a = recipe_test_utils.create_recipe_type_v6(definition=definition_a)
        data_a = {
            'version': '1.0',
            'input_data': [],
            'workspace_id': 1,
        }
        recipe_a = recipe_test_utils.create_recipe(recipe_type=recipe_type_a, input=data_a)
        self.job_a_1 = job_test_utils.create_job(job_type=job_type_a_1, status='FAILED', input=data_dict, num_exes=1,
                                                 recipe=recipe_a)
        self.job_a_2 = job_test_utils.create_job(job_type=job_type_a_2, status='BLOCKED', recipe=recipe_a)
        recipe_test_utils.create_recipe_job(recipe=recipe_a, job_name='Job 1', job=self.job_a_1)
        recipe_test_utils.create_recipe_job(recipe=recipe_a, job_name='Job 2', job=self.job_a_2)

        # Create recipe for re-queueing a job that should now be BLOCKED (and its dependencies)
        job_type_b_1 = job_test_utils.create_seed_job_type()
        job_type_b_2 = job_test_utils.create_seed_job_type()
        job_type_b_3 = job_test_utils.create_seed_job_type()
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
        recipe_type_b = recipe_test_utils.create_recipe_type_v6(definition=definition_b)
        data_b = {
            'version': '1.0',
            'input_data': [],
            'workspace_id': 1,
        }
        recipe_b = recipe_test_utils.create_recipe(recipe_type=recipe_type_b, input=data_b)
        self.job_b_1 = job_test_utils.create_job(job_type=job_type_b_1, status='FAILED', input=data_dict,
                                                 recipe=recipe_b)
        self.job_b_2 = job_test_utils.create_job(job_type=job_type_b_2, status='CANCELED', num_exes=0, recipe=recipe_b)
        self.job_b_3 = job_test_utils.create_job(job_type=job_type_b_3, status='BLOCKED', num_exes=0, recipe=recipe_b)

        recipe_test_utils.create_recipe_job(recipe=recipe_b, job_name='Job 1', job=self.job_b_1)
        recipe_test_utils.create_recipe_job(recipe=recipe_b, job_name='Job 2', job=self.job_b_2)
        recipe_test_utils.create_recipe_job(recipe=recipe_b, job_name='Job 3', job=self.job_b_3)

        # Job IDs to re-queue
        self.job_ids = [self.standalone_failed_job.id, self.standalone_canceled_job.id,
                        self.standalone_completed_job.id, self.job_a_1.id, self.job_b_2.id,
                        self.standalone_queued_job.id]


    @patch('queue.models.CommandMessageManager')
    def test_successful(self, mock_msg_mgr):
        """Tests calling QueueManager.requeue_jobs() successfully"""

        status = Queue.objects.get_queue_status()
        self.assertEqual(status[0].count, 1)

        from queue.messages.requeue_jobs_bulk import create_requeue_jobs_bulk_message
        messages = []
        messages.append(create_requeue_jobs_bulk_message(job_ids=self.job_ids))
        while messages:
            msg = messages.pop(0)
            result = msg.execute()
            if not result:
                self.fail('Requeue failed on message type \'%s\'' % msg.type)
            messages.extend(msg.new_messages)

        standalone_failed_job = Job.objects.get(id=self.standalone_failed_job.id)
        self.assertEqual(standalone_failed_job.status, 'QUEUED')
        self.assertEqual(standalone_failed_job.max_tries, 6)

        standalone_canceled_job = Job.objects.get(id=self.standalone_canceled_job.id)
        self.assertEqual(standalone_canceled_job.status, 'QUEUED')
        self.assertEqual(standalone_canceled_job.max_tries, 4)

        # Superseded job should not be re-queued
        standalone_superseded_job = Job.objects.get(id=self.standalone_superseded_job.id)
        self.assertEqual(standalone_superseded_job.status, 'FAILED')

        # Completed job should not be re-queued
        standalone_completed_job = Job.objects.get(id=self.standalone_completed_job.id)
        self.assertEqual(standalone_completed_job.status, 'COMPLETED')

        job_a_1 = Job.objects.get(id=self.job_a_1.id)
        self.assertEqual(job_a_1.status, 'QUEUED')
        job_a_2 = Job.objects.get(id=self.job_a_2.id)
        self.assertEqual(job_a_2.status, 'BLOCKED')

        job_b_1 = Job.objects.get(id=self.job_b_1.id)
        self.assertEqual(job_b_1.status, 'FAILED')
        job_b_2 = Job.objects.get(id=self.job_b_2.id)
        self.assertEqual(job_b_2.status, 'BLOCKED')
        job_b_3 = Job.objects.get(id=self.job_b_3.id)
        self.assertEqual(job_b_3.status, 'BLOCKED')

        # check queue status
        status = Queue.objects.get_queue_status()
        sum = 0
        for s in status:
            sum += s.count
        self.assertEqual(sum, 5)

        canceled = Queue.objects.filter(is_canceled=True)
        self.assertEqual(len(canceled), 1)