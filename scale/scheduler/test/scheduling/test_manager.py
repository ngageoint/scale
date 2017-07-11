from __future__ import absolute_import
from __future__ import unicode_literals

import django
from django.test import TestCase
from django.utils.timezone import now
from mock import MagicMock, patch

from job.execution.job_exe import RunningJobExecution
from job.execution.manager import job_exe_mgr
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


class TestSchedulingManager(TestCase):

    def setUp(self):
        django.setup()

        self.framework_id = '1234'
        Scheduler.objects.initialize_scheduler()
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

        scheduling_manager = SchedulingManager()
        num_tasks = scheduling_manager.perform_scheduling(self._driver, now())
        self.assertEqual(num_tasks, 0)

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

    @patch('mesos_api.tasks.mesos_pb2.TaskInfo')
    def test_job_type_limit(self, mock_taskinfo):
        """Tests calling perform_scheduling() with a job type limit"""
        mock_taskinfo.return_value = MagicMock()

        Queue.objects.all().delete()
        job_type_with_limit = job_test_utils.create_job_type()
        job_type_with_limit.max_scheduled = 4
        job_type_with_limit.save()
        job_exe_1 = job_test_utils.create_job_exe(job_type=job_type_with_limit, status='RUNNING')
        queue_test_utils.create_queue(job_type=job_type_with_limit)
        queue_test_utils.create_queue(job_type=job_type_with_limit)
        queue_test_utils.create_queue(job_type=job_type_with_limit)
        queue_test_utils.create_queue(job_type=job_type_with_limit)
        queue_test_utils.create_queue(job_type=job_type_with_limit)
        queue_test_utils.create_queue(job_type=job_type_with_limit)
        job_type_mgr.sync_with_database()
        # One job of this type is already running
        job_exe_mgr.schedule_job_exes([RunningJobExecution(self.agent_1.agent_id, job_exe_1)])

        offer_1 = ResourceOffer('offer_1', self.agent_1.agent_id, self.framework_id,
                                NodeResources([Cpus(2.0), Mem(1024.0), Disk(1024.0)]), now())
        offer_2 = ResourceOffer('offer_2', self.agent_2.agent_id, self.framework_id,
                                NodeResources([Cpus(25.0), Mem(2048.0), Disk(2048.0)]), now())
        resource_mgr.add_new_offers([offer_1, offer_2])

        scheduling_manager = SchedulingManager()
        num_tasks = scheduling_manager.perform_scheduling(self._driver, now())
        self.assertEqual(num_tasks, 3)  # One is already running, should only be able to schedule 3 more
