from __future__ import unicode_literals
from __future__ import absolute_import

from django.test import TransactionTestCase

import job.test.utils as job_test_utils
from node.models import Node
from node.test import utils as node_test_utils


class TestNodeManager(TransactionTestCase):

    def test_get_nodes_running_jobs(self):
        """Tests calling NodeManager.get_nodes_running_jobs()"""

        # Create nodes
        node_1 = node_test_utils.create_node(hostname='node_1')
        node_2 = node_test_utils.create_node(hostname='node_2')
        node_3 = node_test_utils.create_node(hostname='node_3')

        # No running jobs; should be empty
        nodes_w_jobs = Node.objects.get_nodes_running_jobs()
        self.assertEqual(nodes_w_jobs, [])

        job_test_utils.create_job_exe(node=node_3, status='COMPLETED')
        job_test_utils.create_job_exe(node=node_3, status='FAILED')
        job_test_utils.create_job_exe(node=node_3, status='CANCELED')

        # 0 running jobs
        self.assertEqual(Node.objects.get_nodes_running_jobs(), [])
        
        # Create a running job_exe
        job = job_test_utils.create_job(status='RUNNING', node=node_1)
        job_test_utils.create_running_job_exe(job=job, node=node_1)

        # 1 running job on node_1
        nodes_w_jobs = Node.objects.get_nodes_running_jobs()
        self.assertEqual(len(nodes_w_jobs), 1)
        self.assertEqual(nodes_w_jobs[0], node_1.id)

        # Create another running job_exe (using a different way to create running job_exe for testing completeness)
        job = job_test_utils.create_job(status='RUNNING', node=node_2)
        job_test_utils.create_job_exe(job=job, node=node_2, status='RUNNING')

        # 2 running job_exes
        nodes_w_jobs = Node.objects.get_nodes_running_jobs()
        self.assertEqual(len(nodes_w_jobs), 2)
        self.assertIn(node_1.id, nodes_w_jobs)
        self.assertIn(node_2.id, nodes_w_jobs)