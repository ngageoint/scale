from __future__ import unicode_literals

import django
from django.test import TestCase
from django.utils.timezone import now
from mock import MagicMock, patch

from job.execution.job_exe import RunningJobExecution
from job.execution.manager import job_exe_mgr
from job.test import utils as job_test_utils
from mesos_api.api import SlaveInfo
from node.resources.node_resources import NodeResources
from node.resources.resource import Cpus, Disk, Mem
from queue.models import Queue
from queue.test import utils as queue_test_utils
from scheduler.models import Scheduler
from scheduler.node.manager import node_mgr
from scheduler.resources.manager import resource_mgr
from scheduler.resources.offer import ResourceOffer
from scheduler.scheduling.manager import SchedulingManager
from scheduler.sync.job_type_manager import job_type_mgr
from scheduler.sync.scheduler_manager import scheduler_mgr


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

        self.node_agent_1 = 'agent_1'
        self.node_agent_2 = 'agent_2'
        self.slave_infos = [SlaveInfo('host_1', slave_id=self.node_agent_1),
                            SlaveInfo('host_2', slave_id=self.node_agent_2)]
        node_mgr.clear()
        node_mgr.register_agent_ids([self.node_agent_1, self.node_agent_2])
        with patch('scheduler.node.manager.api.get_slaves') as mock_get_slaves:
            mock_get_slaves.return_value = self.slave_infos
            node_mgr.sync_with_database('master_host', 5050, scheduler_mgr.scheduler)
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

        offer_1 = ResourceOffer('offer_1', self.node_agent_1, self.framework_id,
                                NodeResources([Cpus(2.0), Mem(1024.0), Disk(1024.0)]), now())
        offer_2 = ResourceOffer('offer_2', self.node_agent_2, self.framework_id,
                                NodeResources([Cpus(25.0), Mem(2048.0), Disk(2048.0)]), now())
        resource_mgr.add_new_offers([offer_1, offer_2])

        scheduling_manager = SchedulingManager()
        num_tasks = scheduling_manager.perform_scheduling(self._driver, now())
        self.assertEqual(num_tasks, 2)  # Schedule both queued job executions

    @patch('mesos_api.tasks.mesos_pb2.TaskInfo')
    def test_paused_scheduler(self, mock_taskinfo):
        """Tests calling perform_scheduling() with a paused scheduler"""
        mock_taskinfo.return_value = MagicMock()

        offer_1 = ResourceOffer('offer_1', self.node_agent_1, self.framework_id,
                                NodeResources([Cpus(2.0), Mem(1024.0), Disk(1024.0)]), now())
        offer_2 = ResourceOffer('offer_2', self.node_agent_2, self.framework_id,
                                NodeResources([Cpus(25.0), Mem(2048.0), Disk(2048.0)]), now())
        resource_mgr.add_new_offers([offer_1, offer_2])
        Scheduler.objects.update(is_paused=True)
        scheduler_mgr.sync_with_database()
        with patch('scheduler.node.manager.api.get_slaves') as mock_get_slaves:
            mock_get_slaves.return_value = self.slave_infos
            node_mgr.sync_with_database('master_host', 5050, scheduler_mgr.scheduler)

        scheduling_manager = SchedulingManager()
        num_tasks = scheduling_manager.perform_scheduling(self._driver, now())
        self.assertEqual(num_tasks, 0)

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
        job_exe_mgr.schedule_job_exes([RunningJobExecution(job_exe_1)])

        offer_1 = ResourceOffer('offer_1', self.node_agent_1, self.framework_id,
                                NodeResources([Cpus(2.0), Mem(1024.0), Disk(1024.0)]), now())
        offer_2 = ResourceOffer('offer_2', self.node_agent_2, self.framework_id,
                                NodeResources([Cpus(25.0), Mem(2048.0), Disk(2048.0)]), now())
        resource_mgr.add_new_offers([offer_1, offer_2])

        scheduling_manager = SchedulingManager()
        num_tasks = scheduling_manager.perform_scheduling(self._driver, now())
        self.assertEqual(num_tasks, 3)  # One is already running, should only be able to schedule 3 more
