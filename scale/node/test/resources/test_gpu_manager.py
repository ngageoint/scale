import django
from django.test import TestCase

from node.resources.gpu_manager import GPUManager

class test_GPUManager(TestCase):
    
    def setUp(self):
        GPUManager.reset_gpu_dict()
    
    def test_add_new_node_gpus(self):
        node_id = 1
        gpu_count = 3
        GPUManager.define_node_gpus(node_id,gpu_count)
        self.assertEqual(GPUManager.get_gpu_count_for_node(node_id), gpu_count)
        
    def test_add_less_gpu(self):
        node_id = 2
        gpu_count = 3
        GPUManager.define_node_gpus(node_id,gpu_count)
        self.assertEqual(GPUManager.get_gpu_count_for_node(node_id), 3)
        
        gpu_count = 1
        GPUManager.define_node_gpus(node_id,gpu_count)
        self.assertEqual(GPUManager.get_gpu_count_for_node(node_id), 3)
        
        
    def test_add_additional_GPU(self):
        node_id = 3
        gpu_count = 4
        GPUManager.define_node_gpus(node_id,gpu_count)
        self.assertEqual(GPUManager.get_gpu_count_for_node(node_id), 4)
        
    def test_reserve_gpu(self):
        node_id = 4
        gpu_count = 2
        required_gpus = 2
        GPUManager.define_node_gpus(node_id,gpu_count)
        self.assertTrue(GPUManager.reserve_gpus_for_job(node_id, required_gpus))
        
        job_id = 11
        self.assertFalse(GPUManager.reserve_gpus_for_job(node_id, required_gpus))
        
        gpu_count = 4
        GPUManager.define_node_gpus(node_id,gpu_count)
        self.assertTrue(GPUManager.reserve_gpus_for_job(node_id, required_gpus))
        
    def test_assign_gpus(self):
        node_id = 5
        job_id = 10
        gpu_count = 2
        required_gpus = 2
        GPUManager.define_node_gpus(node_id,gpu_count)
        GPUManager.reserve_gpus_for_job(node_id, required_gpus)
        self.assertTrue(GPUManager.assign_gpus_for_job(node_id, job_id, required_gpus))
        
        job_id = 11
        self.assertFalse(GPUManager.reserve_gpus_for_job(node_id, required_gpus)) # shouldnt have enough GPUs
        
        gpu_count = 4
        GPUManager.define_node_gpus(node_id,gpu_count)
        GPUManager.reserve_gpus_for_job(node_id, required_gpus)
        self.assertTrue(GPUManager.assign_gpus_for_job(node_id, job_id, required_gpus))
    
    def test_get_nvidia_label(self):
        node_id = 6
        job_id = 10
        gpu_count = 2
        required_gpus = 2
        GPUManager.define_node_gpus(node_id,gpu_count)
        GPUManager.reserve_gpus_for_job(node_id, required_gpus)
        GPUManager.assign_gpus_for_job(node_id, job_id, required_gpus)
        nvidia_label = GPUManager.get_nvidia_docker_label(node_id, job_id)
        self.assertEqual(nvidia_label, "0,1")
        
        gpu_count = 4
        job_id = 11
        GPUManager.define_node_gpus(node_id, gpu_count)
        GPUManager.reserve_gpus_for_job(node_id, required_gpus)
        GPUManager.assign_gpus_for_job(node_id, job_id, required_gpus)
        nvidia_label = GPUManager.get_nvidia_docker_label(node_id, job_id)
        self.assertEqual(nvidia_label, "2,3")
        
    def test_release_gpu(self):
        node_id = 7
        job_id = 10
        gpu_count = 2
        required_gpus = 2
        GPUManager.define_node_gpus(node_id,gpu_count)
        GPUManager.reserve_gpus_for_job(node_id, required_gpus)
        self.assertTrue(GPUManager.assign_gpus_for_job(node_id, job_id, required_gpus))
        
        job_id = 11

        self.assertFalse(GPUManager.reserve_gpus_for_job(node_id, required_gpus)) # shouldnt have enough GPUs
        
        GPUManager.release_gpus(node_id, 10)
        self.assertTrue(GPUManager.reserve_gpus_for_job(node_id, required_gpus)) #gpus should be avail again
        self.assertTrue(GPUManager.assign_gpus_for_job(node_id, job_id, required_gpus)) #gpus should be avail again
        nvidia_label = GPUManager.get_nvidia_docker_label(node_id, job_id)
        self.assertEqual(nvidia_label, "0,1")