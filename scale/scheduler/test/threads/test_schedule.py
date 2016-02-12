from __future__ import unicode_literals

import django
from django.test import TransactionTestCase
from mock import MagicMock, patch

from job.execution.running.manager import RunningJobExecutionManager
from job.resources import NodeResources
from mesos_api.api import SlaveInfo
from node.test import utils as node_test_utils
from queue.test import utils as queue_test_utils
from scheduler.models import Scheduler
from scheduler.offer.manager import OfferManager
from scheduler.offer.offer import ResourceOffer
from scheduler.sync.job_type_manager import JobTypeManager
from scheduler.sync.node_manager import NodeManager
from scheduler.sync.scheduler_manager import SchedulerManager
from scheduler.threads.schedule import SchedulingThread


class TestSchedulingThread(TransactionTestCase):

    fixtures = ['scheduler.json']

    def setUp(self):
        django.setup()

        self._driver = MagicMock()
        self._job_exe_manager = RunningJobExecutionManager()
        self._job_type_manager = JobTypeManager()
        self._node_manager = NodeManager()
        self._offer_manager = OfferManager()
        self._scheduler_manager = SchedulerManager(None)

        self._scheduler_manager.sync_with_database()

        self.node_agent_1 = 'agent_1'
        self.node_agent_2 = 'agent_2'
        self.node_1 = node_test_utils.create_node(hostname='host_1', slave_id=self.node_agent_1)
        self.node_2 = node_test_utils.create_node(hostname='host_2', slave_id=self.node_agent_2)
        self.slave_infos = [SlaveInfo('host_1', slave_id=self.node_agent_1),
                            SlaveInfo('host_2', slave_id=self.node_agent_2)]
        self._node_manager.add_agent_ids([self.node_agent_1, self.node_agent_2])
        with patch('scheduler.sync.node_manager.api.get_slaves') as mock_get_slaves:
            mock_get_slaves.return_value = self.slave_infos
            self._node_manager.sync_with_database('master_host', 5050)

        self.queue_1 = queue_test_utils.create_queue(cpus_required=4.0, mem_required=1024.0, disk_in_required=100.0,
                                                     disk_out_required=200.0, disk_total_required=300.0)
        self.queue_2 = queue_test_utils.create_queue(cpus_required=8.0, mem_required=512.0, disk_in_required=400.0,
                                                     disk_out_required=45.0, disk_total_required=445.0)
        self._job_type_manager.sync_with_database()

        self._scheduling_thread = SchedulingThread(self._driver, self._job_exe_manager, self._job_type_manager,
                                                   self._node_manager, self._offer_manager, self._scheduler_manager)

    @patch('scheduler.scale_job_exe.mesos_pb2.TaskInfo')
    def test_successful_schedule(self, mock_taskinfo):
        """Tests successfully scheduling tasks"""
        mock_taskinfo.return_value = MagicMock()

        offer_1 = ResourceOffer('offer_1',  self.node_agent_1, NodeResources(cpus=2.0, mem=1024.0, disk=1024.0))
        offer_2 = ResourceOffer('offer_2',  self.node_agent_2, NodeResources(cpus=25.0, mem=2048.0, disk=2048.0))
        self._offer_manager.add_new_offers([offer_1, offer_2])

        num_tasks = self._scheduling_thread._perform_scheduling()
        self.assertEqual(num_tasks, 2)

    @patch('scheduler.scale_job_exe.mesos_pb2.TaskInfo')
    def test_paused_scheduler(self, mock_taskinfo):
        """Tests running the scheduling thread with a paused scheduler"""
        mock_taskinfo.return_value = MagicMock()

        offer_1 = ResourceOffer('offer_1',  self.node_agent_1, NodeResources(cpus=2.0, mem=1024.0, disk=1024.0))
        offer_2 = ResourceOffer('offer_2',  self.node_agent_2, NodeResources(cpus=25.0, mem=2048.0, disk=2048.0))
        self._offer_manager.add_new_offers([offer_1, offer_2])
        Scheduler.objects.update(is_paused=True)
        self._scheduler_manager.sync_with_database()

        num_tasks = self._scheduling_thread._perform_scheduling()
        self.assertEqual(num_tasks, 0)
