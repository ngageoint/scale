#@PydevCodeAnalysisIgnore
import django
from django.test import TestCase

import job.test.utils as job_test_utils
import node.test.utils as node_test_utils
import shared_resource.test.utils as shared_resource_test_utils
from shared_resource.models import SharedResource

RESOURCE_LIMIT = 1000
JOB_TYPE_1_USAGE = 400
JOB_TYPE_1A_USAGE = 200
JOB_TYPE_3_USAGE = 500


class SharedResourceManagerTest(TestCase):

    def setUp(self):
        django.setup()

        self.resource_no_limit = shared_resource_test_utils.create_resource()
        self.resource_1 = shared_resource_test_utils.create_resource(limit=RESOURCE_LIMIT)
        self.resource_2 = shared_resource_test_utils.create_resource(limit=RESOURCE_LIMIT)
        self.resource_restricted = shared_resource_test_utils.create_resource(limit=RESOURCE_LIMIT, is_global=False)

        self.job_type_1 = job_test_utils.create_job_type()
        self.job_type_1a = job_test_utils.create_job_type()
        self.job_type_2 = job_test_utils.create_job_type()
        self.non_global_job = job_test_utils.create_job_type()

        shared_resource_test_utils.create_requirement(job_type=self.job_type_1, shared_resource=self.resource_1,
                                                      usage=JOB_TYPE_1_USAGE)
        shared_resource_test_utils.create_requirement(job_type=self.job_type_1a, shared_resource=self.resource_1,
                                                      usage=JOB_TYPE_1A_USAGE)
        shared_resource_test_utils.create_requirement(job_type=self.non_global_job,
                                                      shared_resource=self.resource_restricted, usage=JOB_TYPE_3_USAGE)

        self.global_job_types = [self.job_type_1, self.job_type_2]
        self.node_without_special_access = node_test_utils.create_node()

        self.node_with_special_access = node_test_utils.create_node()
        self.resource_restricted.nodes.add(self.node_with_special_access)

    def testResourceRemainingNone(self):
        remaining = SharedResource.objects.get_resource_remaining(self.resource_no_limit)

        self.assertIsNone(remaining, u'A resource with no limit should return None Remaining')

    def testResourcesRemainingNoJobs(self):
        '''A resource with no jobs using it should have the limit remaining'''
        remaining = SharedResource.objects.get_resource_remaining(self.resource_1)

        self.assertEqual(remaining, RESOURCE_LIMIT)

    def testResourceRemainingReduceByJob(self):
        job = job_test_utils.create_job(self.job_type_1)
        job_test_utils.create_job_exe(job=job)

        remaining = SharedResource.objects.get_resource_remaining(self.resource_1)

        self.assertEqual(remaining, RESOURCE_LIMIT - JOB_TYPE_1_USAGE)

    def testResourceRemainingUnrelatedJob(self):
        job = job_test_utils.create_job(self.job_type_1)
        job_test_utils.create_job_exe(job=job)

        remaining = SharedResource.objects.get_resource_remaining(self.resource_2)

        self.assertEqual(remaining, RESOURCE_LIMIT)

    def testJobTypesForGlobalOnlyNode(self):
        runnable_job_types = SharedResource.objects.runnable_job_types(self.node_without_special_access)

        for job_type in self.global_job_types:
            self.assertIn(job_type, runnable_job_types)
        self.assertNotIn(self.non_global_job, runnable_job_types)

    def testJobTypesForSpecialAccessNode(self):
        runnable_job_types = SharedResource.objects.runnable_job_types(self.node_with_special_access)

        for job_type in self.global_job_types:
            self.assertIn(job_type, runnable_job_types)
        self.assertIn(self.non_global_job, runnable_job_types)

    def testJobTypesForAcessWithJustEnoughUsage(self):
        job1 = job_test_utils.create_job(self.job_type_1)
        job_test_utils.create_job_exe(job=job1)

        job2 = job_test_utils.create_job(self.job_type_1)
        job_test_utils.create_job_exe(job=job2)

        runnable_job_types = SharedResource.objects.runnable_job_types(self.node_with_special_access)
        self.assertIn(self.job_type_1a, runnable_job_types)
