"""Defines a command message that cancels job models"""
from __future__ import unicode_literals

import logging

from django.db import transaction
from django.utils.timezone import now

from job.models import Job
from messaging.messages.message import CommandMessage
from util.parse import datetime_to_string, parse_datetime

# This is the maximum number of job models that can fit in one message. This maximum ensures that every message of this
# type is less than 25 KiB long.
MAX_NUM = 100


logger = logging.getLogger(__name__)


def create_cancel_jobs_messages(job_ids, when):
    """Creates messages to cancel the given jobs

    :param job_ids: The job IDs to cancel
    :type job_ids: list
    :param when: The cancel time
    :type when: :class:`datetime.datetime`
    :return: The list of messages
    :rtype: list
    """

    messages = []

    message = None
    for job_id in job_ids:
        if not message:
            message = CancelJobs()
            message.when = when
        elif not message.can_fit_more():
            messages.append(message)
            message = CancelJobs()
            message.when = when
        message.add_job(job_id)
    if message:
        messages.append(message)

    return messages


class CancelJobs(CommandMessage):
    """Command message that cancels job models
    """

    def __init__(self):
        """Constructor
        """

        super(CancelJobs, self).__init__('cancel_jobs')

        self._job_ids = []
        self.when = None

    def add_job(self, job_id):
        """Adds the given job to this message

        :param job_id: The job ID
        :type job_id: int
        """

        self._job_ids.append(job_id)

    def can_fit_more(self):
        """Indicates whether more jobs can fit in this message

        :return: True if more jobs can fit, False otherwise
        :rtype: bool
        """

        return len(self._job_ids) < MAX_NUM

    def to_json(self):
        """See :meth:`messaging.messages.message.CommandMessage.to_json`
        """

        return {'job_ids': self._job_ids, 'when': datetime_to_string(self.when)}

    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`
        """

        message = CancelJobs()
        message.when = parse_datetime(json_dict['when'])
        for job_id in json_dict['job_ids']:
            message.add_job(job_id)
        return message

    def execute(self):
        """See :meth:`messaging.messages.message.CommandMessage.execute`
        """

        with transaction.atomic():
            jobs_to_canceled = []
            # Retrieve locked job models
            for job_model in Job.objects.get_locked_jobs(self._job_ids):
                if job_model.can_be_canceled():
                    jobs_to_canceled.append(job_model)

            # Update jobs that need status set to CANCELED
            if jobs_to_canceled:
                job_ids = Job.objects.update_jobs_to_canceled(jobs_to_canceled, self.when)
                from queue.models import Queue
                Queue.objects.cancel_queued_jobs(job_ids)
                logger.info('Set %d job(s) to CANCELED status', len(job_ids))

        # Need to update recipes of canceled jobs so that dependent jobs are BLOCKED
        from recipe.messages.update_recipes import create_update_recipes_messages_from_jobs
        msgs = create_update_recipes_messages_from_jobs(self._job_ids)
        self.new_messages.extend(msgs)

        return True
