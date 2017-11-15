"""Defines a command message that sets QUEUED status for job models"""
from __future__ import unicode_literals

import logging
from collections import namedtuple

from django.db import transaction

from job.models import Job
from messaging.messages.message import CommandMessage
from queue.models import Queue

# This is the maximum number of job models that can fit in one message. This maximum ensures that every message of this
# type is less than 25 KiB long.
MAX_NUM = 100


QueuedJob = namedtuple('QueuedJob', ['job_id', 'exe_num'])


logger = logging.getLogger(__name__)


class QueuedJobs(CommandMessage):
    """Command message that sets QUEUED status for job models
    """

    def __init__(self):
        """Constructor
        """

        super(QueuedJobs, self).__init__('queued_jobs')

        self.priority = None
        self._queued_jobs = []

    def add_job(self, job_id, exe_num):
        """Adds the given job to this message

        :param job_id: The job ID
        :type job_id: int
        :param exe_num: The job's execution number (0 if the job has never been queued)
        :type exe_num: int
        """

        queued_job = QueuedJob(job_id, exe_num)
        self._queued_jobs.append(queued_job)

    def can_fit_more(self):
        """Indicates whether more jobs can fit in this message

        :return: True if more jobs can fit, False otherwise
        :rtype: bool
        """

        return len(self._queued_jobs) < MAX_NUM

    def to_json(self):
        """See :meth:`messaging.messages.message.CommandMessage.to_json`
        """

        job_list = []
        for queued_job in self._queued_jobs:
            job_list.append({'id': queued_job.job_id, 'exe_num': queued_job.exe_num})
        cmd_dict = {'jobs': job_list}

        if self.priority is not None:
            cmd_dict['priority'] = self.priority

        return cmd_dict

    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`
        """

        message = QueuedJobs()

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

        job_ids = []
        for queued_job in self._queued_jobs:
            job_ids.append(queued_job.job_id)

        with transaction.atomic():
            # Retrieve locked job models
            job_models = {}
            for job in Job.objects.get_locked_jobs(job_ids):
                job_models[job.id] = job

            jobs_to_queue = []
            for queued_job in self._queued_jobs:
                job_model = job_models[queued_job.job_id]

                # If execution number does not match, then this update is obsolete
                if job_model.num_exes != queued_job.exe_num:
                    # Ignore this job
                    continue

                jobs_to_queue.append(job_model)

            # Queue jobs
            if jobs_to_queue:
                queued_job_ids = Queue.objects.queue_jobs(jobs_to_queue, self.priority)
                logger.info('Queued %d job(s)', len(queued_job_ids))

        return True
