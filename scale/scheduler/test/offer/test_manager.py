from __future__ import unicode_literals

import django
from django.test import TestCase

from job.execution.running.job_exe import RunningJobExecution
from job.resources import NodeResources
from job.test import utils as job_test_utils
from node.test import utils as node_test_utils
from queue.job_exe import QueuedJobExecution
from queue.test import utils as queue_test_utils
from scheduler.offer.manager import OfferManager
from scheduler.offer.offer import ResourceOffer


class TestOfferManager(TestCase):

    def setUp(self):
        django.setup()

        self.node_agent = 'agent_1'
        self.node_agent_paused = 'agent_paused'
        self.node = node_test_utils.create_node(slave_id=self.node_agent)
        self.paused_node = node_test_utils.create_node(slave_id=self.node_agent_paused)
        self.paused_node.is_paused = True

        self.running_job_exe_1 = job_test_utils.create_job_exe(status='RUNNING', node=self.paused_node)
        self.running_job_exe_1.cpus_scheduled = 2.0
        self.running_job_exe_1.mem_scheduled = 512.0
        self.running_job_exe_1.disk_in_scheduled = 100.0
        self.running_job_exe_1.disk_out_scheduled = 200.0
        self.running_job_exe_1.disk_total_scheduled = 300.0
        self.running_job_exe_2 = job_test_utils.create_job_exe(status='RUNNING', node=self.node)
        self.running_job_exe_2.cpus_scheduled = 2.0
        self.running_job_exe_2.mem_scheduled = 512.0
        self.running_job_exe_2.disk_in_scheduled = 100.0
        self.running_job_exe_2.disk_out_scheduled = 200.0
        self.running_job_exe_2.disk_total_scheduled = 300.0

        self.queue_1 = queue_test_utils.create_queue(cpus_required=4.0, mem_required=1024.0, disk_in_required=100.0,
                                                     disk_out_required=200.0, disk_total_required=300.0)
        self.queue_2 = queue_test_utils.create_queue(cpus_required=8.0, mem_required=512.0, disk_in_required=400.0,
                                                     disk_out_required=45.0, disk_total_required=445.0)
        self.queue_high_cpus = queue_test_utils.create_queue(cpus_required=200.0, mem_required=1024.0,
                                                             disk_in_required=100.0, disk_out_required=200.0,
                                                             disk_total_required=300.0)
        self.queue_high_mem = queue_test_utils.create_queue(cpus_required=2.0, mem_required=10240.0,
                                                            disk_in_required=100.0, disk_out_required=200.0,
                                                            disk_total_required=300.0)
        self.queue_high_disk = queue_test_utils.create_queue(cpus_required=2.0, mem_required=1024.0,
                                                             disk_in_required=10000.0, disk_out_required=20000.0,
                                                             disk_total_required=30000.0)

    def test_no_ready_offers(self):
        """Tests considering job executions when no offers are ready"""

        offer_1 = ResourceOffer('offer_1',  self.node_agent_paused, NodeResources(cpus=2.0, mem=1024.0, disk=1024.0))
        offer_2 = ResourceOffer('offer_2',  self.node_agent, NodeResources(cpus=25.0, mem=2048.0, disk=2048.0))

        manager = OfferManager()
        manager.add_new_offers([offer_1, offer_2])

        job_exe_1 = QueuedJobExecution(self.queue_1)
        result = manager.consider_new_job_exe(job_exe_1)
        self.assertEqual(result, OfferManager.NO_NODES_AVAILABLE)

        job_exe_2 = RunningJobExecution(self.running_job_exe_1)
        result = manager.consider_next_task(job_exe_2)
        self.assertEqual(result, OfferManager.NODE_OFFLINE)

    def test_offers_with_no_nodes(self):
        """Tests considering job executions when offers cannot be readied due to no nodes updated"""

        offer_1 = ResourceOffer('offer_1',  self.node_agent_paused, NodeResources(cpus=2.0, mem=1024.0, disk=1024.0))
        offer_2 = ResourceOffer('offer_2',  self.node_agent, NodeResources(cpus=25.0, mem=2048.0, disk=2048.0))

        manager = OfferManager()
        manager.add_new_offers([offer_1, offer_2])
        manager.ready_new_offers()

        job_exe_1 = QueuedJobExecution(self.queue_1)
        result = manager.consider_new_job_exe(job_exe_1)
        self.assertEqual(result, OfferManager.NO_NODES_AVAILABLE)

        job_exe_2 = RunningJobExecution(self.running_job_exe_1)
        result = manager.consider_next_task(job_exe_2)
        self.assertEqual(result, OfferManager.NODE_OFFLINE)

    def test_accepted(self):
        """Tests accepting a running and queued job execution and returning the node offers"""

        offer_1 = ResourceOffer('offer_1',  self.node_agent_paused, NodeResources(cpus=2.0, mem=1024.0, disk=1024.0))
        offer_2 = ResourceOffer('offer_2',  self.node_agent, NodeResources(cpus=25.0, mem=2048.0, disk=2048.0))

        manager = OfferManager()
        manager.add_new_offers([offer_1, offer_2])
        manager.update_nodes([self.node, self.paused_node])
        manager.ready_new_offers()

        job_exe_1 = QueuedJobExecution(self.queue_1)
        result = manager.consider_new_job_exe(job_exe_1)
        self.assertEqual(result, OfferManager.ACCEPTED)

        job_exe_2 = RunningJobExecution(self.running_job_exe_1)
        result = manager.consider_next_task(job_exe_2)
        self.assertEqual(result, OfferManager.ACCEPTED)

        node_offers = manager.pop_offers_with_accepted_job_exes()
        self.assertEqual(len(node_offers), 2)

    def test_remove_offers(self):
        """Tests accepting a running and queued job execution and then removing all offers"""

        offer_1 = ResourceOffer('offer_1',  self.node_agent_paused, NodeResources(cpus=2.0, mem=1024.0, disk=1024.0))
        offer_2 = ResourceOffer('offer_2',  self.node_agent, NodeResources(cpus=25.0, mem=2048.0, disk=2048.0))

        manager = OfferManager()
        manager.add_new_offers([offer_1, offer_2])
        manager.update_nodes([self.node, self.paused_node])
        manager.ready_new_offers()

        job_exe_1 = QueuedJobExecution(self.queue_1)
        result = manager.consider_new_job_exe(job_exe_1)
        self.assertEqual(result, OfferManager.ACCEPTED)

        job_exe_2 = RunningJobExecution(self.running_job_exe_1)
        result = manager.consider_next_task(job_exe_2)
        self.assertEqual(result, OfferManager.ACCEPTED)

        manager.remove_offers([offer_2.id, offer_1.id])
        node_offers = manager.pop_offers_with_accepted_job_exes()
        self.assertEqual(len(node_offers), 0)

    def test_lost_node(self):
        """Tests accepting a running and queued job execution and then the node being lost"""

        offer_1 = ResourceOffer('offer_1',  self.node_agent, NodeResources(cpus=2.0, mem=1024.0, disk=1024.0))
        offer_2 = ResourceOffer('offer_2',  self.node_agent, NodeResources(cpus=25.0, mem=2048.0, disk=2048.0))

        manager = OfferManager()
        manager.add_new_offers([offer_1, offer_2])
        manager.update_nodes([self.node, self.paused_node])
        manager.ready_new_offers()

        job_exe_1 = QueuedJobExecution(self.queue_1)
        result = manager.consider_new_job_exe(job_exe_1)
        self.assertEqual(result, OfferManager.ACCEPTED)

        job_exe_2 = RunningJobExecution(self.running_job_exe_2)
        result = manager.consider_next_task(job_exe_2)
        self.assertEqual(result, OfferManager.ACCEPTED)

        manager.lost_node(self.node_agent)
        node_offers = manager.pop_offers_with_accepted_job_exes()
        self.assertEqual(len(node_offers), 0)

    def test_all_offers_paused(self):
        """Tests rejecting a queued job execution due to all nodes being paused"""

        offer_1 = ResourceOffer('offer_1',  self.node_agent_paused, NodeResources(cpus=2.0, mem=1024.0, disk=1024.0))
        offer_2 = ResourceOffer('offer_2',  self.node_agent_paused, NodeResources(cpus=25.0, mem=2048.0, disk=2048.0))

        manager = OfferManager()
        manager.add_new_offers([offer_1, offer_2])
        manager.update_nodes([self.paused_node])
        manager.ready_new_offers()

        job_exe_1 = QueuedJobExecution(self.queue_1)
        result = manager.consider_new_job_exe(job_exe_1)
        self.assertEqual(result, OfferManager.NO_NODES_AVAILABLE)

        node_offers = manager.pop_offers_with_accepted_job_exes()
        self.assertEqual(len(node_offers), 0)

    def test_high_cpus(self):
        """Tests rejecting a queued job execution due to too many CPUs required"""

        offer_1 = ResourceOffer('offer_1',  self.node_agent_paused, NodeResources(cpus=2.0, mem=1024.0, disk=1024.0))
        offer_2 = ResourceOffer('offer_2',  self.node_agent, NodeResources(cpus=25.0, mem=2048.0, disk=2048.0))

        manager = OfferManager()
        manager.add_new_offers([offer_1, offer_2])
        manager.update_nodes([self.node, self.paused_node])
        manager.ready_new_offers()

        job_exe_1 = QueuedJobExecution(self.queue_high_cpus)
        result = manager.consider_new_job_exe(job_exe_1)
        self.assertEqual(result, OfferManager.NOT_ENOUGH_CPUS)

        node_offers = manager.pop_offers_with_accepted_job_exes()
        self.assertEqual(len(node_offers), 0)

    def test_high_mem(self):
        """Tests rejecting a queued job execution due to too much memory required"""

        offer_1 = ResourceOffer('offer_1',  self.node_agent_paused, NodeResources(cpus=2.0, mem=1024.0, disk=1024.0))
        offer_2 = ResourceOffer('offer_2',  self.node_agent, NodeResources(cpus=25.0, mem=2048.0, disk=2048.0))

        manager = OfferManager()
        manager.add_new_offers([offer_1, offer_2])
        manager.update_nodes([self.node, self.paused_node])
        manager.ready_new_offers()

        job_exe_1 = QueuedJobExecution(self.queue_high_mem)
        result = manager.consider_new_job_exe(job_exe_1)
        self.assertEqual(result, OfferManager.NOT_ENOUGH_MEM)

        node_offers = manager.pop_offers_with_accepted_job_exes()
        self.assertEqual(len(node_offers), 0)

    def test_high_disk(self):
        """Tests rejecting a queued job execution due to too much disk required"""

        offer_1 = ResourceOffer('offer_1',  self.node_agent_paused, NodeResources(cpus=2.0, mem=1024.0, disk=1024.0))
        offer_2 = ResourceOffer('offer_2',  self.node_agent, NodeResources(cpus=25.0, mem=2048.0, disk=2048.0))

        manager = OfferManager()
        manager.add_new_offers([offer_1, offer_2])
        manager.update_nodes([self.node, self.paused_node])
        manager.ready_new_offers()

        job_exe_1 = QueuedJobExecution(self.queue_high_disk)
        result = manager.consider_new_job_exe(job_exe_1)
        self.assertEqual(result, OfferManager.NOT_ENOUGH_DISK)

        node_offers = manager.pop_offers_with_accepted_job_exes()
        self.assertEqual(len(node_offers), 0)
