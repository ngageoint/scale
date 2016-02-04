"""Defines utility methods for testing queues"""
import django.utils.timezone as timezone

import job.test.utils as job_test_utils
from queue.models import JobLoad, Queue


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


def create_queue(priority=1, cpus_required=1.0, mem_required=512.0, disk_in_required=200.0, disk_out_required=100.0,
                 disk_total_required=300.0):
    """Creates a queue model for unit testing

    :param priority: The priority
    :type priority: int
    :param cpus_required: The CPUs required in MiB
    :type cpus_required: float
    :param mem_required: The memory required in MiB
    :type mem_required: float
    :param disk_in_required: The input disk space required in MiB
    :type disk_in_required: float
    :param disk_out_required: The output disk space required in MiB
    :type disk_out_required: float
    :param disk_total_required: The total disk space required in MiB
    :type disk_total_required: float
    """

    job_exe = job_test_utils.create_job_exe(status='QUEUED')

    return Queue.objects.create(job_exe=job_exe, job_type=job_exe.job.job_type, priority=priority,
                                cpus_required=cpus_required, mem_required=mem_required,
                                disk_in_required=disk_in_required, disk_out_required=disk_out_required,
                                disk_total_required=disk_total_required, queued=timezone.now())
