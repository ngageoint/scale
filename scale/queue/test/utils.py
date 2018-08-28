"""Defines utility methods for testing queues"""
import django.utils.timezone as timezone

import job.test.utils as job_test_utils
from job.execution.configuration.json.exe_config import ExecutionConfiguration
from queue.models import JobLoad, Queue
from node.resources.node_resources import NodeResources
from node.resources.resource import Cpus, Disk, Mem, Gpus


def create_job_load(job_type=None, measured=None, pending_count=0, queued_count=0, running_count=0):
    """Creates a job load model for unit testing

    :returns: The job load model
    :rtype: :class:`queue.models.JobLoad`
    """

    if not job_type:
        job_type = job_test_utils.create_job_type()

    if not measured:
        measured = timezone.now()

    return JobLoad.objects.create(job_type=job_type, measured=measured, pending_count=pending_count,
                                  queued_count=queued_count, running_count=running_count,
                                  total_count=pending_count + queued_count + running_count)


def create_queue(job_type=None, priority=1, timeout=3600, cpus_required=1.0, mem_required=512.0, disk_in_required=200.0,
                 disk_out_required=100.0, disk_total_required=300.0, gpus_required=0, queued=timezone.now()):
    """Creates a queue model for unit testing

    :param job_type: The job type
    :type job_type: :class:`job.models.JobType`
    :param priority: The priority
    :type priority: int
    :param timeout: The timeout
    :type timeout: int
    :param cpus_required: The number of CPUs required
    :type cpus_required: float
    :param mem_required: The memory required in MiB
    :type mem_required: float
    :param disk_in_required: The input disk space required in MiB
    :type disk_in_required: float
    :param disk_out_required: The output disk space required in MiB
    :type disk_out_required: float
    :param disk_total_required: The total disk space required in MiB
    :type disk_total_required: float
    :param gpus_required: The number of GPUs required
    :type gpus_required: float
    :param queued: The time the execution was queued
    :type queued: :class:`datetime.datetime`
    """

    job = job_test_utils.create_job(job_type=job_type, status='QUEUED')
    resources = NodeResources([Cpus(cpus_required), Mem(mem_required), Disk(disk_total_required), Gpus(gpus_required)])

    return Queue.objects.create(job_type=job.job_type, job=job, exe_num=job.num_exes, priority=priority,
                                timeout=timeout, input_file_size=disk_in_required,
                                interface=job.get_job_interface().get_dict(),
                                configuration=ExecutionConfiguration().get_dict(),
                                resources=resources.get_json().get_dict(), queued=queued)
