'''Defines utility methods for testing queues'''
import django.utils.timezone as timezone

import job.test.utils as job_test_utils
from queue.models import JobLoad


def create_job_load(job_type=None, measured=None, pending_count=0, queued_count=0, running_count=0):
    '''Creates a job load model for unit testing

    :returns: The job load model
    :rtype: :class:`queue.models.JobLoad`
    '''

    if not job_type:
        job_type = job_test_utils.create_job_type()

    if not measured:
        measured = timezone.now()

    return JobLoad.objects.create(job_type=job_type, measured=measured, pending_count=pending_count,
                                  queued_count=queued_count, running_count=running_count,
                                  total_count=pending_count + queued_count + running_count)
