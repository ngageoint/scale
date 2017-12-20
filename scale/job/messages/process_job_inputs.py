"""Defines a command message that processes the inputs for a list of jobs"""
from __future__ import unicode_literals

import logging

from django.db import transaction

from job.models import Job
from messaging.messages.message import CommandMessage

# This is the maximum number of job models that can fit in one message. This maximum ensures that every message of this
# type is less than 25 KiB long and that each message can be processed quickly.
MAX_NUM = 100


logger = logging.getLogger(__name__)


def create_process_job_inputs_messages(job_ids):
    """Creates messages to process the inputs for the given jobs

    :param job_ids: The job IDs
    :type job_ids: list
    :return: The list of messages
    :rtype: list
    """

    messages = []

    message = None
    for job_id in job_ids:
        if not message:
            message = ProcessJobInputs()
        elif not message.can_fit_more():
            messages.append(message)
            message = ProcessJobInputs()
        message.add_job(job_id)
    if message:
        messages.append(message)

    return messages


class ProcessJobInputs(CommandMessage):
    """Command message that processes the inputs for a list of jobs
    """

    def __init__(self):
        """Constructor
        """

        super(ProcessJobInputs, self).__init__('process_job_input')

        self._count = 0
        self._job_ids = []

    def add_job(self, job_id):
        """Adds the given job ID to this message

        :param job_id: The job ID
        :type job_id: int
        """

        self._count += 1
        self._job_ids.append(job_id)

    def can_fit_more(self):
        """Indicates whether more jobs can fit in this message

        :return: True if more jobs can fit, False otherwise
        :rtype: bool
        """

        return self._count < MAX_NUM

    def to_json(self):
        """See :meth:`messaging.messages.message.CommandMessage.to_json`
        """

        return {'job_ids': self._job_ids}

    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`
        """

        message = ProcessJobInputs()
        for job_id in json_dict['job_ids']:
            message.add_job(job_id)

        return message

    def execute(self):
        """See :meth:`messaging.messages.message.CommandMessage.execute`
        """

        from queue.messages.queued_jobs import create_queued_jobs_messages, QueuedJob

        with transaction.atomic():
            # Retrieve locked job models
            job_models = Job.objects.get_locked_jobs(self._job_ids)

            # Process job inputs
            Job.objects.process_job_input(job_models)

        # Create messages to queue the jobs
        jobs_to_queue = []
        for job_model in job_models:
            if job_model.num_exes == 0:
                jobs_to_queue.append(QueuedJob(job_model.id, 0))
        if jobs_to_queue:
            logger.info('Processed job inputs, %d job(s) will be queued', len(jobs_to_queue))
            self.new_messages.extend(create_queued_jobs_messages(jobs_to_queue))

        return True
