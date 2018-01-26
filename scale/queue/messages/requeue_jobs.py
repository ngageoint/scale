"""Defines a command message that re-queues job models"""
from __future__ import unicode_literals

import logging

from django.utils.timezone import now

from job.models import Job
from messaging.messages.message import CommandMessage
from queue.messages.queued_jobs import create_queued_jobs_messages, QueuedJob

# This is the maximum number of job models that can fit in one message. This maximum ensures that every message of this
# type is less than 25 KiB long.
MAX_NUM = 100


logger = logging.getLogger(__name__)


def create_requeue_jobs_messages(jobs, priority=None):
    """Creates messages to requeue the given jobs

    :param jobs: The jobs to requeue
    :type jobs: list
    :param priority: Optional priority to set on the re-queued jobs
    :type priority: int
    :return: The list of messages
    :rtype: list
    """

    messages = []

    message = None
    for job in jobs:
        if not message:
            message = RequeueJobs()
            message.priority = priority
        elif not message.can_fit_more():
            messages.append(message)
            message = RequeueJobs()
            message.priority = priority
        message.add_job(job.job_id, job.exe_num)
    if message:
        messages.append(message)

    return messages


class RequeueJobs(CommandMessage):
    """Command message that re-queues job models
    """

    def __init__(self):
        """Constructor
        """

        super(RequeueJobs, self).__init__('requeue_jobs')

        self.priority = None
        self._requeue_jobs = []

    def add_job(self, job_id, exe_num):
        """Adds the given job to this message

        :param job_id: The job ID
        :type job_id: int
        :param exe_num: The job's execution number
        :type exe_num: int
        """

        requeue_job = QueuedJob(job_id, exe_num)
        self._requeue_jobs.append(requeue_job)

    def can_fit_more(self):
        """Indicates whether more jobs can fit in this message

        :return: True if more jobs can fit, False otherwise
        :rtype: bool
        """

        return len(self._requeue_jobs) < MAX_NUM

    def to_json(self):
        """See :meth:`messaging.messages.message.CommandMessage.to_json`
        """

        job_list = []
        for requeue_job in self._requeue_jobs:
            job_list.append({'id': requeue_job.job_id, 'exe_num': requeue_job.exe_num})
        cmd_dict = {'jobs': job_list}

        if self.priority is not None:
            cmd_dict['priority'] = self.priority

        return cmd_dict

    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`
        """

        message = RequeueJobs()

        if 'priority' in json_dict:
            message.priority = json_dict['priority']

        for job_dict in json_dict['jobs']:
            job_id = job_dict['id']
            exe_num = job_dict['exe_num']
            message.add_job(job_id, exe_num)

        return message

    def execute(self):
        """See :meth:`messaging.messages.message.CommandMessage.execute`
        """

        job_ids = [requeue_job.job_id for requeue_job in self._requeue_jobs]
        jobs_to_requeue = []

        # Find jobs that can be re-queued and have valid exe_num
        job_models = {job.id: job for job in Job.objects.get_basic_jobs(job_ids)}
        for requeue_job in self._requeue_jobs:
            job_model = job_models[requeue_job.job_id]
            if job_model.can_be_queued() and job_model.has_been_queued() and job_model.num_exes == requeue_job.exe_num:
                jobs_to_requeue.append(job_model)
        job_ids_to_requeue = [job.id for job in jobs_to_requeue]
        logger.info('There are %d job(s) to re-queue, increasing max tries', len(job_ids_to_requeue))

        # Reset max_tries for jobs that will be re-queued
        Job.objects.increment_max_tries(job_ids_to_requeue, now())

        # Create message to queue the jobs
        self.new_messages.extend(create_queued_jobs_messages(jobs_to_requeue, priority=self.priority))

        return True
