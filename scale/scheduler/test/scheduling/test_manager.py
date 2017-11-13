from __future__ import absolute_import
from __future__ import unicode_literals

import django
from django.test import TestCase
from django.utils.timezone import now
from mock import MagicMock, patch

from error.models import reset_error_cache
from job.execution.manager import job_exe_mgr
from job.models import JobExecution
from job.test import utils as job_test_utils
from node.resources.node_resources import NodeResources
from node.resources.resource import Cpus, Disk, Mem
from queue.models import Queue
from queue.test import utils as queue_test_utils
from scheduler.manager import scheduler_mgr
from scheduler.models import Scheduler
from scheduler.node.agent import Agent
from scheduler.node.manager import node_mgr
from scheduler.resources.manager import resource_mgr
from scheduler.resources.offer import ResourceOffer
from scheduler.scheduling.manager import SchedulingManager
from scheduler.sync.job_type_manager import job_type_mgr
from scheduler.tasks.manager import system_task_mgr


class TestSchedulingManager(TestCase):

    fixtures = ['basic_job_errors.json']

    def setUp(self):
        django.setup()

        reset_error_cache()

        self.framework_id = '1234'
        Scheduler.objects.initialize_scheduler()
        Scheduler.objects.update(num_message_handlers=0)  # Prevent message handler tasks from scheduling
        self._driver = MagicMock()

        scheduler_mgr.sync_with_database()
        scheduler_mgr.update_from_mesos(framework_id=self.framework_id)
        resource_mgr.clear()
        job_exe_mgr.clear()

        self.agent_1 = Agent('agent_1', 'host_1')
        self.agent_2 = Agent('agent_2', 'host_2')
        self.agent_3 = Agent('agent_3', 'host_2')
        node_mgr.clear()
        node_mgr.register_agents([self.agent_1, self.agent_2])
        node_mgr.sync_with_database(scheduler_mgr.config)
        # Ignore initial cleanup, health check, and image pull tasks
        for node in node_mgr.get_nodes():
            node._last_heath_task = now()
            node._initial_cleanup_completed()
            node._is_image_pulled = True
            node._update_state()
        # Ignore system tasks
        system_task_mgr._is_db_update_completed = True

        self.queue_1 = queue_test_utils.create_queue(cpus_required=4.0, mem_required=1024.0, disk_in_required=100.0,
                                                     disk_out_required=200.0, disk_total_required=300.0)
        self.queue_2 = queue_test_utils.create_queue(cpus_required=8.0, mem_required=512.0, disk_in_required=400.0,
                                                     disk_out_required=45.0, disk_total_required=445.0)
        job_type_mgr.sync_with_database()

    @patch('mesos_api.tasks.mesos_pb2.TaskInfo')
    def test_successful_schedule(self, mock_taskinfo):
        """Tests successfully calling perform_scheduling()"""
        mock_taskinfo.return_value = MagicMock()

        offer_1 = ResourceOffer('offer_1', self.agent_1.agent_id, self.framework_id,
                                NodeResources([Cpus(2.0), Mem(1024.0), Disk(1024.0)]), now())
        offer_2 = ResourceOffer('offer_2', self.agent_2.agent_id, self.framework_id,
                                NodeResources([Cpus(25.0), Mem(2048.0), Disk(2048.0)]), now())
        resource_mgr.add_new_offers([offer_1, offer_2])

        scheduling_manager = SchedulingManager()

        num_tasks = scheduling_manager.perform_scheduling(self._driver, now())
        self.assertEqual(num_tasks, 2)  # Schedule both queued job executions
        # Ensure job execution models are created and queue models are deleted
        self.assertEqual(JobExecution.objects.filter(job_id=self.queue_1.job_id).count(), 1)
        self.assertEqual(JobExecution.objects.filter(job_id=self.queue_2.job_id).count(), 1)
        self.assertEqual(Queue.objects.filter(id__in=[self.queue_1.id, self.queue_2.id]).count(), 0)

    @patch('mesos_api.tasks.mesos_pb2.TaskInfo')
    def test_node_with_new_agent_id(self, mock_taskinfo):
        """Tests successfully calling perform_scheduling() when a node get a new agent ID"""
        mock_taskinfo.return_value = MagicMock()

        # Host 2 gets new agent ID of agent_3
        node_mgr.lost_node(self.agent_2)
        node_mgr.register_agents([self.agent_3])
        node_mgr.sync_with_database(scheduler_mgr.config)

        offer = ResourceOffer('offer', self.agent_3.agent_id, self.framework_id,
                              NodeResources([Cpus(25.0), Mem(2048.0), Disk(2048.0)]), now())
        resource_mgr.add_new_offers([offer])

        scheduling_manager = SchedulingManager()
        num_tasks = scheduling_manager.perform_scheduling(self._driver, now())
        self.assertEqual(num_tasks, 2)  # Schedule both queued job executions
        # Check that created tasks have the correct agent ID
        calls = self._driver.method_calls
        self.assertEqual(1, len(calls))
        mesos_tasks = calls[0][1][1]
        for mesos_task in mesos_tasks:
            self.assertEqual(self.agent_3.agent_id, mesos_task.slave_id.value)

    @patch('mesos_api.tasks.mesos_pb2.TaskInfo')
    def test_paused_scheduler(self, mock_taskinfo):
        """Tests calling perform_scheduling() with a paused scheduler"""
        mock_taskinfo.return_value = MagicMock()

        offer_1 = ResourceOffer('offer_1', self.agent_1.agent_id, self.framework_id,
                                NodeResources([Cpus(2.0), Mem(1024.0), Disk(1024.0)]), now())
        offer_2 = ResourceOffer('offer_2', self.agent_2.agent_id, self.framework_id,
                                NodeResources([Cpus(25.0), Mem(2048.0), Disk(2048.0)]), now())
        resource_mgr.add_new_offers([offer_1, offer_2])
        Scheduler.objects.update(is_paused=True)
        scheduler_mgr.sync_with_database()
        node_mgr.sync_with_database(scheduler_mgr.config)  # Updates nodes with paused scheduler
        system_task_mgr._is_db_update_completed = False  # Make sure system tasks don't get scheduled

        scheduling_manager = SchedulingManager()
        num_tasks = scheduling_manager.perform_scheduling(self._driver, now())
        self.assertEqual(num_tasks, 0)
        self.assertEqual(JobExecution.objects.filter(job_id=self.queue_1.job_id).count(), 0)
        self.assertEqual(JobExecution.objects.filter(job_id=self.queue_2.job_id).count(), 0)
        self.assertEqual(Queue.objects.filter(id__in=[self.queue_1.id, self.queue_2.id]).count(), 2)

    @patch('mesos_api.tasks.mesos_pb2.TaskInfo')
    def test_missing_job_types(self, mock_taskinfo):
        """Tests calling perform_scheduling() when a queued job type has not been synced to the scheduler"""
        mock_taskinfo.return_value = MagicMock()

        offer_1 = ResourceOffer('offer_1', self.agent_1.agent_id, self.framework_id,
                                NodeResources([Cpus(2.0), Mem(1024.0), Disk(1024.0)]), now())
        offer_2 = ResourceOffer('offer_2', self.agent_2.agent_id, self.framework_id,
                                NodeResources([Cpus(25.0), Mem(2048.0), Disk(2048.0)]), now())
        resource_mgr.add_new_offers([offer_1, offer_2])

        scheduling_manager = SchedulingManager()

        # Clear out job type manager for scheduling
        with patch('scheduler.scheduling.manager.job_type_mgr.get_job_types') as mock_get_job_types:
            mock_get_job_types.return_value = {}
            num_tasks = scheduling_manager.perform_scheduling(self._driver, now())

        # Nothing should be scheduled
        self.assertEqual(num_tasks, 0)
        self.assertEqual(JobExecution.objects.filter(job_id=self.queue_1.job_id).count(), 0)
        self.assertEqual(JobExecution.objects.filter(job_id=self.queue_2.job_id).count(), 0)
        self.assertEqual(Queue.objects.filter(id__in=[self.queue_1.id, self.queue_2.id]).count(), 2)

    @patch('mesos_api.tasks.mesos_pb2.TaskInfo')
    def test_missing_workspace(self, mock_taskinfo):
        """Tests calling perform_scheduling() when a queued job's workspace has not been synced to the scheduler"""
        mock_taskinfo.return_value = MagicMock()

        offer_1 = ResourceOffer('offer_1', self.agent_1.agent_id, self.framework_id,
                                NodeResources([Cpus(2.0), Mem(1024.0), Disk(1024.0)]), now())
        offer_2 = ResourceOffer('offer_2', self.agent_2.agent_id, self.framework_id,
                                NodeResources([Cpus(25.0), Mem(2048.0), Disk(2048.0)]), now())
        resource_mgr.add_new_offers([offer_1, offer_2])

        # Add workspaces to the queued jobs
        queue_1 = Queue.objects.get(id=self.queue_1.id)
        config = queue_1.get_execution_configuration()
        config.set_output_workspaces({'my_output': 'my_workspace'})
        queue_1.configuration = config.get_dict()
        queue_1.save()
        queue_2 = Queue.objects.get(id=self.queue_2.id)
        config = queue_2.get_execution_configuration()
        config.set_output_workspaces({'my_output': 'my_workspace'})
        queue_2.configuration = config.get_dict()
        queue_2.save()

        scheduling_manager = SchedulingManager()

        # Clear out workspace manager for scheduling
        with patch('scheduler.scheduling.manager.workspace_mgr.get_workspaces') as mock_get_workspaces:
            mock_get_workspaces.return_value = {}
            num_tasks = scheduling_manager.perform_scheduling(self._driver, now())

        # Nothing should be scheduled
        self.assertEqual(num_tasks, 0)
        self.assertEqual(JobExecution.objects.filter(job_id=self.queue_1.job_id).count(), 0)
        self.assertEqual(JobExecution.objects.filter(job_id=self.queue_2.job_id).count(), 0)
        self.assertEqual(Queue.objects.filter(id__in=[self.queue_1.id, self.queue_2.id]).count(), 2)

    @patch('mesos_api.tasks.mesos_pb2.TaskInfo')
    def test_paused_job_type(self, mock_taskinfo):
        """Tests calling perform_scheduling() when a job type is paused"""
        mock_taskinfo.return_value = MagicMock()

        offer_1 = ResourceOffer('offer_1', self.agent_1.agent_id, self.framework_id,
                                NodeResources([Cpus(2.0), Mem(1024.0), Disk(1024.0)]), now())
        offer_2 = ResourceOffer('offer_2', self.agent_2.agent_id, self.framework_id,
                                NodeResources([Cpus(25.0), Mem(2048.0), Disk(2048.0)]), now())
        resource_mgr.add_new_offers([offer_1, offer_2])
        self.queue_1.job_type.is_paused = True
        self.queue_1.job_type.save()
        job_type_mgr.sync_with_database()

        scheduling_manager = SchedulingManager()
        num_tasks = scheduling_manager.perform_scheduling(self._driver, now())
        self.assertEqual(num_tasks, 1)  # Schedule queued job execution that is not paused
        self.assertEqual(JobExecution.objects.filter(job_id=self.queue_1.job_id).count(), 0)
        self.assertEqual(JobExecution.objects.filter(job_id=self.queue_2.job_id).count(), 1)
        self.assertEqual(Queue.objects.filter(id__in=[self.queue_1.id, self.queue_2.id]).count(), 1)

    @patch('mesos_api.tasks.mesos_pb2.TaskInfo')
    def test_job_type_limit(self, mock_taskinfo):
        """Tests calling perform_scheduling() with a job type limit"""
        mock_taskinfo.return_value = MagicMock()

        Queue.objects.all().delete()
        job_type_with_limit = job_test_utils.create_job_type()
        job_type_with_limit.max_scheduled = 4
        job_type_with_limit.save()
        running_job_exe_1 = job_test_utils.create_running_job_exe(agent_id=self.agent_1.agent_id,
                                                                  job_type=job_type_with_limit)
        queue_test_utils.create_queue(job_type=job_type_with_limit)
        queue_test_utils.create_queue(job_type=job_type_with_limit)
        queue_test_utils.create_queue(job_type=job_type_with_limit)
        queue_test_utils.create_queue(job_type=job_type_with_limit)
        queue_test_utils.create_queue(job_type=job_type_with_limit)
        queue_test_utils.create_queue(job_type=job_type_with_limit)
        job_type_mgr.sync_with_database()
        # One job of this type is already running
        job_exe_mgr.schedule_job_exes([running_job_exe_1], [])

        offer_1 = ResourceOffer('offer_1', self.agent_1.agent_id, self.framework_id,
                                NodeResources([Cpus(2.0), Mem(1024.0), Disk(1024.0)]), now())
        offer_2 = ResourceOffer('offer_2', self.agent_2.agent_id, self.framework_id,
                                NodeResources([Cpus(25.0), Mem(2048.0), Disk(2048.0)]), now())
        resource_mgr.add_new_offers([offer_1, offer_2])

        scheduling_manager = SchedulingManager()
        num_tasks = scheduling_manager.perform_scheduling(self._driver, now())
        self.assertEqual(num_tasks, 3)  # One is already running, should only be able to schedule 3 more

    @patch('mesos_api.tasks.mesos_pb2.TaskInfo')
    def test_canceled_queue_model(self, mock_taskinfo):
        """Tests successfully calling perform_scheduling() when a queue model has been canceled"""
        mock_taskinfo.return_value = MagicMock()

        offer_1 = ResourceOffer('offer_1', self.agent_1.agent_id, self.framework_id,
                                NodeResources([Cpus(2.0), Mem(1024.0), Disk(1024.0)]), now())
        offer_2 = ResourceOffer('offer_2', self.agent_2.agent_id, self.framework_id,
                                NodeResources([Cpus(25.0), Mem(2048.0), Disk(2048.0)]), now())
        resource_mgr.add_new_offers([offer_1, offer_2])
        self.queue_1.is_canceled = True
        self.queue_1.save()

        scheduling_manager = SchedulingManager()
        num_tasks = scheduling_manager.perform_scheduling(self._driver, now())
        self.assertEqual(num_tasks, 1)  # Scheduled non-canceled queued job execution
        # queue_1 should be canceled, queue_2 should be running, queue should be empty now
        self.assertEqual(JobExecution.objects.filter(job_id=self.queue_1.job_id).count(), 1)
        self.assertEqual(JobExecution.objects.filter(job_id=self.queue_2.job_id).count(), 1)
        self.assertEqual(Queue.objects.filter(id__in=[self.queue_1.id, self.queue_2.id]).count(), 0)
        # Job execution manager should have a message for the canceled job execution
        messages = job_exe_mgr.get_messages()
        found_job_exe_end_message = False
        for message in messages:
            if message.type == 'create_job_exe_ends':
                found_job_exe_end_message = True
        self.assertTrue(found_job_exe_end_message)

    @patch('mesos_api.tasks.mesos_pb2.TaskInfo')
    def test_schedule_system_tasks(self, mock_taskinfo):
        """Tests successfully calling perform_scheduling() when scheduling system tasks"""
        mock_taskinfo.return_value = MagicMock()

        offer_1 = ResourceOffer('offer_1', self.agent_1.agent_id, self.framework_id,
                                NodeResources([Cpus(2.0), Mem(1024.0), Disk(1024.0)]), now())
        offer_2 = ResourceOffer('offer_2', self.agent_2.agent_id, self.framework_id,
                                NodeResources([Cpus(25.0), Mem(2048.0), Disk(2048.0)]), now())
        resource_mgr.add_new_offers([offer_1, offer_2])

        # Clear the queue
        Queue.objects.all().delete()
        # Set us up to schedule a database update task
        system_task_mgr._is_db_update_completed = False
        # Set us up to schedule 2 message handler tasks
        Scheduler.objects.update(num_message_handlers=2)
        scheduler_mgr.sync_with_database()

        scheduling_manager = SchedulingManager()

        num_tasks = scheduling_manager.perform_scheduling(self._driver, now())
        self.assertEqual(num_tasks, 3)  # Schedule database update task and 2 message handler tasks
