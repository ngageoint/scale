from __future__ import unicode_literals

import django
from django.test import TestCase

from job.execution.running.job_exe import RunningJobExecution
from job.resources import NodeResources
from job.test import utils as job_test_utils
from node.test import utils as node_test_utils
from queue.job_exe import QueuedJobExecution
from queue.test import utils as queue_test_utils
from scheduler.models import Scheduler
from scheduler.offer.node import NodeOffers
from scheduler.offer.offer import ResourceOffer


class TestNodeOffers(TestCase):

    def setUp(self):
        django.setup()

        Scheduler.objects.initialize_scheduler()

        self.node_agent = 'agent_1'
        self.node_agent_paused = 'agent_paused'
        self.node = node_test_utils.create_node(slave_id=self.node_agent)
        self.paused_node = node_test_utils.create_node(slave_id=self.node_agent_paused)
        self.paused_node.is_paused = True

        self.running_job_exe_1 = job_test_utils.create_job_exe(status='RUNNING')
        self.running_job_exe_1.cpus_scheduled = 2.0
        self.running_job_exe_1.mem_scheduled = 512.0
        self.running_job_exe_1.disk_in_scheduled = 100.0
        self.running_job_exe_1.disk_out_scheduled = 200.0
        self.running_job_exe_1.disk_total_scheduled = 300.0
        self.running_job_exe_2 = job_test_utils.create_job_exe(status='RUNNING')
        self.running_job_exe_2.cpus_scheduled = 4.0
        self.running_job_exe_2.mem_scheduled = 1024.0
        self.running_job_exe_2.disk_in_scheduled = 500.0
        self.running_job_exe_2.disk_out_scheduled = 50.0
        self.running_job_exe_2.disk_total_scheduled = 550.0
        self.running_job_exe_high_cpus = job_test_utils.create_job_exe(status='RUNNING')
        self.running_job_exe_high_cpus.cpus_scheduled = 200.0
        self.running_job_exe_high_cpus.mem_scheduled = 512.0
        self.running_job_exe_high_cpus.disk_in_scheduled = 100.0
        self.running_job_exe_high_cpus.disk_out_scheduled = 200.0
        self.running_job_exe_high_cpus.disk_total_scheduled = 300.0
        self.running_job_exe_high_mem = job_test_utils.create_job_exe(status='RUNNING')
        self.running_job_exe_high_mem.cpus_scheduled = 2.0
        self.running_job_exe_high_mem.mem_scheduled = 1048576.0
        self.running_job_exe_high_mem.disk_in_scheduled = 100.0
        self.running_job_exe_high_mem.disk_out_scheduled = 200.0
        self.running_job_exe_high_mem.disk_total_scheduled = 300.0
        self.running_job_exe_high_disk = job_test_utils.create_job_exe(status='RUNNING')
        self.running_job_exe_high_disk.cpus_scheduled = 2.0
        self.running_job_exe_high_disk.mem_scheduled = 512.0
        self.running_job_exe_high_disk.disk_in_scheduled = 10000.0
        self.running_job_exe_high_disk.disk_out_scheduled = 20000.0
        self.running_job_exe_high_disk.disk_total_scheduled = 30000.0

        self.queue_1 = queue_test_utils.create_queue(cpus_required=2.0, mem_required=1024.0, disk_in_required=100.0,
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

    def test_adding_offers(self):
        """Tests adding offer and checking the results"""

        node_offers = NodeOffers(self.node)

        offer_1 = ResourceOffer('offer_1',  self.node_agent, NodeResources(cpus=2.0, mem=1024.0, disk=1024.0))
        node_offers.add_offer(offer_1)
        node_offers.add_offer(offer_1)  # Add same offer twice, should ignore

        offer_2 = ResourceOffer('offer_2',  self.node_agent, NodeResources(cpus=5.0, mem=2048.0, disk=2048.0))
        node_offers.add_offer(offer_2)

        offer_3 = ResourceOffer('offer_3',  self.node_agent, NodeResources(cpus=3.0, mem=512.0, disk=1024.0))
        node_offers.add_offer(offer_3)

        offer_4 = ResourceOffer('offer_4', 'bad_agent', NodeResources(cpus=1.0, mem=512.0, disk=1024.0))
        self.assertRaises(Exception, node_offers.add_offer, offer_4)

        self.assertEqual(node_offers._available_cpus, 10.0)
        self.assertEqual(node_offers._available_mem, 3584.0)
        self.assertEqual(node_offers._available_disk, 4096.0)

    def test_consider_new_job_exe(self):
        """Tests consider_new_job_exe() and get_accepted_new_job_exes()"""

        node_offers = NodeOffers(self.node)
        offer_1 = ResourceOffer('offer_1',  self.node_agent, NodeResources(cpus=24.0, mem=1024.0, disk=1024.0))
        node_offers.add_offer(offer_1)
        offer_2 = ResourceOffer('offer_2',  self.node_agent, NodeResources(cpus=50.0, mem=2048.0, disk=2048.0))
        node_offers.add_offer(offer_2)
        self.assertFalse(node_offers.has_accepted_job_exes())
        self.assertListEqual(node_offers.get_accepted_running_job_exes(), [])
        self.assertListEqual(node_offers.get_accepted_new_job_exes(), [])

        job_exe_1 = QueuedJobExecution(self.queue_1)
        result = node_offers.consider_new_job_exe(job_exe_1)
        self.assertEqual(result, NodeOffers.ACCEPTED)
        result = node_offers.consider_new_job_exe(job_exe_1)  # Same job_exe, should have no effect
        self.assertEqual(result, NodeOffers.ACCEPTED)

        job_exe_high_cpus = QueuedJobExecution(self.queue_high_cpus)
        result = node_offers.consider_new_job_exe(job_exe_high_cpus)
        self.assertEqual(result, NodeOffers.NOT_ENOUGH_CPUS)

        job_exe_high_mem = QueuedJobExecution(self.queue_high_mem)
        result = node_offers.consider_new_job_exe(job_exe_high_mem)
        self.assertEqual(result, NodeOffers.NOT_ENOUGH_MEM)

        job_exe_high_disk = QueuedJobExecution(self.queue_high_disk)
        result = node_offers.consider_new_job_exe(job_exe_high_disk)
        self.assertEqual(result, NodeOffers.NOT_ENOUGH_DISK)

        job_exe_2 = QueuedJobExecution(self.queue_2)
        result = node_offers.consider_new_job_exe(job_exe_2)
        self.assertEqual(result, NodeOffers.ACCEPTED)

        self.assertTrue(node_offers.has_accepted_job_exes())
        self.assertEqual(len(node_offers.get_accepted_new_job_exes()), 2)
        self.assertSetEqual(set(node_offers.get_accepted_new_job_exes()), {job_exe_1, job_exe_2})
        self.assertListEqual(node_offers.get_accepted_running_job_exes(), [])

        self.assertEqual(node_offers._available_cpus, 64.0)
        self.assertEqual(node_offers._available_mem, 1536.0)
        self.assertEqual(node_offers._available_disk, 2327.0)

    def test_consider_next_task(self):
        """Tests consider_next_task() and get_accepted_running_job_exes()"""

        node_offers = NodeOffers(self.node)
        offer_1 = ResourceOffer('offer_1',  self.node_agent, NodeResources(cpus=24.0, mem=1024.0, disk=1024.0))
        node_offers.add_offer(offer_1)
        offer_2 = ResourceOffer('offer_2',  self.node_agent, NodeResources(cpus=50.0, mem=2048.0, disk=2048.0))
        node_offers.add_offer(offer_2)
        self.assertFalse(node_offers.has_accepted_job_exes())
        self.assertListEqual(node_offers.get_accepted_running_job_exes(), [])
        self.assertListEqual(node_offers.get_accepted_new_job_exes(), [])

        job_exe_1 = RunningJobExecution(self.running_job_exe_1)
        result = node_offers.consider_next_task(job_exe_1)
        self.assertEqual(result, NodeOffers.ACCEPTED)
        result = node_offers.consider_next_task(job_exe_1)  # Same job_exe, should have no effect
        self.assertEqual(result, NodeOffers.ACCEPTED)

        job_exe_high_cpus = RunningJobExecution(self.running_job_exe_high_cpus)
        result = node_offers.consider_next_task(job_exe_high_cpus)
        self.assertEqual(result, NodeOffers.NOT_ENOUGH_CPUS)

        job_exe_high_mem = RunningJobExecution(self.running_job_exe_high_mem)
        result = node_offers.consider_next_task(job_exe_high_mem)
        self.assertEqual(result, NodeOffers.NOT_ENOUGH_MEM)

        job_exe_high_disk = RunningJobExecution(self.running_job_exe_high_disk)
        result = node_offers.consider_next_task(job_exe_high_disk)
        self.assertEqual(result, NodeOffers.NOT_ENOUGH_DISK)

        job_exe_2 = RunningJobExecution(self.running_job_exe_2)
        result = node_offers.consider_next_task(job_exe_2)
        self.assertEqual(result, NodeOffers.ACCEPTED)

        self.assertTrue(node_offers.has_accepted_job_exes())
        self.assertEqual(len(node_offers.get_accepted_running_job_exes()), 2)
        self.assertSetEqual(set(node_offers.get_accepted_running_job_exes()), {job_exe_1, job_exe_2})
        self.assertListEqual(node_offers.get_accepted_new_job_exes(), [])

        self.assertEqual(node_offers._available_cpus, 68.0)
        self.assertEqual(node_offers._available_mem, 1536.0)
        self.assertEqual(node_offers._available_disk, 2222.0)

    def test_paused_node(self):
        """Tests adding job executions when the node is paused"""

        node_offers = NodeOffers(self.paused_node)
        offer_1 = ResourceOffer('offer_1',  self.node_agent_paused, NodeResources(cpus=24.0, mem=1024.0, disk=1024.0))
        node_offers.add_offer(offer_1)
        offer_2 = ResourceOffer('offer_2',  self.node_agent_paused, NodeResources(cpus=50.0, mem=2048.0, disk=2048.0))
        node_offers.add_offer(offer_2)
        self.assertFalse(node_offers.has_accepted_job_exes())
        self.assertListEqual(node_offers.get_accepted_running_job_exes(), [])
        self.assertListEqual(node_offers.get_accepted_new_job_exes(), [])

        # Ensure it accepts new tasks for already running job executions
        job_exe_1 = RunningJobExecution(self.running_job_exe_1)
        result = node_offers.consider_next_task(job_exe_1)
        self.assertEqual(result, NodeOffers.ACCEPTED)

        job_exe_2 = RunningJobExecution(self.running_job_exe_2)
        result = node_offers.consider_next_task(job_exe_2)
        self.assertEqual(result, NodeOffers.ACCEPTED)

        # Don't accept new job executions while paused
        job_exe_new = QueuedJobExecution(self.queue_1)
        result = node_offers.consider_new_job_exe(job_exe_new)
        self.assertEqual(result, NodeOffers.NODE_PAUSED)

        self.assertTrue(node_offers.has_accepted_job_exes())
        self.assertEqual(len(node_offers.get_accepted_running_job_exes()), 2)
        self.assertSetEqual(set(node_offers.get_accepted_running_job_exes()), {job_exe_1, job_exe_2})
        self.assertListEqual(node_offers.get_accepted_new_job_exes(), [])

        self.assertEqual(node_offers._available_cpus, 68.0)
        self.assertEqual(node_offers._available_mem, 1536.0)
        self.assertEqual(node_offers._available_disk, 2222.0)

    def test_lost_node(self):
        """Tests when the node is lost"""

        node_offers = NodeOffers(self.node)
        offer_1 = ResourceOffer('offer_1',  self.node_agent, NodeResources(cpus=24.0, mem=1024.0, disk=1024.0))
        node_offers.add_offer(offer_1)
        offer_2 = ResourceOffer('offer_2',  self.node_agent, NodeResources(cpus=50.0, mem=2048.0, disk=2048.0))
        node_offers.add_offer(offer_2)
        self.assertFalse(node_offers.has_accepted_job_exes())
        self.assertListEqual(node_offers.get_accepted_running_job_exes(), [])
        self.assertListEqual(node_offers.get_accepted_new_job_exes(), [])

        # Accept a couple job executions
        job_exe_1 = RunningJobExecution(self.running_job_exe_1)
        result = node_offers.consider_next_task(job_exe_1)
        self.assertEqual(result, NodeOffers.ACCEPTED)

        job_exe_2 = QueuedJobExecution(self.queue_1)
        result = node_offers.consider_new_job_exe(job_exe_2)
        self.assertEqual(result, NodeOffers.ACCEPTED)

        self.assertTrue(node_offers.has_accepted_job_exes())
        self.assertGreater(node_offers._available_cpus, 0.0)
        self.assertGreater(node_offers._available_mem, 0.0)
        self.assertGreater(node_offers._available_disk, 0.0)

        # Node is lost
        node_offers.lost_node()
        self.assertFalse(node_offers.has_accepted_job_exes())
        self.assertEqual(node_offers._available_cpus, 0.0)
        self.assertEqual(node_offers._available_mem, 0.0)
        self.assertEqual(node_offers._available_disk, 0.0)

    def test_no_offers(self):
        """Tests adding job executions when there are no offers"""

        node_offers = NodeOffers(self.node)
        self.assertFalse(node_offers.has_accepted_job_exes())
        self.assertListEqual(node_offers.get_accepted_running_job_exes(), [])
        self.assertListEqual(node_offers.get_accepted_new_job_exes(), [])

        job_exe_1 = RunningJobExecution(self.running_job_exe_1)
        result = node_offers.consider_next_task(job_exe_1)
        self.assertEqual(result, NodeOffers.NO_OFFERS)

        job_exe_new = QueuedJobExecution(self.queue_1)
        result = node_offers.consider_new_job_exe(job_exe_new)
        self.assertEqual(result, NodeOffers.NO_OFFERS)

        self.assertFalse(node_offers.has_accepted_job_exes())
        self.assertListEqual(node_offers.get_accepted_running_job_exes(), [])
        self.assertListEqual(node_offers.get_accepted_new_job_exes(), [])

    def test_job_exe_canceled(self):
        """Tests adding a job execution that becomes canceled while scheduling"""

        node_offers = NodeOffers(self.node)
        offer_1 = ResourceOffer('offer_1',  self.node_agent, NodeResources(cpus=24.0, mem=1024.0, disk=1024.0))
        node_offers.add_offer(offer_1)
        offer_2 = ResourceOffer('offer_2',  self.node_agent, NodeResources(cpus=50.0, mem=2048.0, disk=2048.0))
        node_offers.add_offer(offer_2)
        self.assertFalse(node_offers.has_accepted_job_exes())
        self.assertListEqual(node_offers.get_accepted_running_job_exes(), [])
        self.assertListEqual(node_offers.get_accepted_new_job_exes(), [])

        job_exe_1 = RunningJobExecution(self.running_job_exe_1)
        job_exe_1.execution_canceled()
        result = node_offers.consider_next_task(job_exe_1)
        self.assertEqual(result, NodeOffers.TASK_INVALID)

        self.assertFalse(node_offers.has_accepted_job_exes())
        self.assertListEqual(node_offers.get_accepted_running_job_exes(), [])
        self.assertListEqual(node_offers.get_accepted_new_job_exes(), [])

    def test_remove_offer(self):
        """Tests remove_offer()"""

        node_offers = NodeOffers(self.node)
        offer_1 = ResourceOffer('offer_1',  self.node_agent, NodeResources(cpus=24.0, mem=1024.0, disk=1024.0))
        node_offers.add_offer(offer_1)
        offer_2 = ResourceOffer('offer_2',  self.node_agent, NodeResources(cpus=50.0, mem=2048.0, disk=2048.0))
        node_offers.add_offer(offer_2)

        job_exe_1 = QueuedJobExecution(self.queue_1)
        result = node_offers.consider_new_job_exe(job_exe_1)
        self.assertEqual(result, NodeOffers.ACCEPTED)

        # Remove one offer, new job execution should still be accepted
        node_offers.remove_offer(offer_1.id)
        self.assertTrue(node_offers.has_accepted_job_exes())
        self.assertListEqual(node_offers.get_accepted_new_job_exes(), [job_exe_1])

        # Remove second offer, no resources left, all job executions should be removed
        node_offers.remove_offer(offer_2.id)
        self.assertFalse(node_offers.has_accepted_job_exes())
        self.assertListEqual(node_offers.get_accepted_new_job_exes(), [])

        self.assertEqual(node_offers._available_cpus, 0.0)
        self.assertEqual(node_offers._available_mem, 0.0)
        self.assertEqual(node_offers._available_disk, 0.0)
