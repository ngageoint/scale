"""Defines a command message that sets PENDING status for job models"""
from __future__ import unicode_literals

import logging

from django.db import transaction

from job.models import Job
from messaging.messages.message import CommandMessage
from util.parse import datetime_to_string, parse_datetime

# This is the maximum number of job models that can fit in one message. This maximum ensures that every message of this
# type is less than 25 KiB long.
MAX_NUM = 1000


logger = logging.getLogger(__name__)


def create_pending_jobs_messages(pending_job_ids, when):
    """Creates messages to update the given job IDs to PENDING

    :param pending_job_ids: The job IDs
    :type pending_job_ids: list
    :param when: The current time
    :type when: :class:`datetime.datetime`
    :return: The list of messages
    :rtype: list
    """

    messages = []

    message = None
    for job_id in pending_job_ids:
        if not message:
            message = PendingJobs()
            message.status_change = when
        elif not message.can_fit_more():
            messages.append(message)
            message = PendingJobs()
            message.status_change = when
        message.add_job(job_id)
    if message:
        messages.append(message)

    return messages


class PendingJobs(CommandMessage):
    """Command message that sets PENDING status for job models
    """

    def __init__(self):
        """Constructor
        """

        super(PendingJobs, self).__init__('pending_jobs')

        self._count = 0
        self._pending_job_ids = []
        self.status_change = None

    def add_job(self, job_id):
        """Adds the given job ID to this message

        :param job_id: The job ID
        :type job_id: int
        """

        self._count += 1
        self._pending_job_ids.append(job_id)

    def can_fit_more(self):
        """Indicates whether more jobs can fit in this message

        :return: True if more jobs can fit, False otherwise
        :rtype: bool
        """

        return self._count < MAX_NUM

    def to_json(self):
        """See :meth:`messaging.messages.message.CommandMessage.to_json`
        """

        return {'status_change': datetime_to_string(self.status_change), 'job_ids': self._pending_job_ids}

    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`
        """

        status_change = parse_datetime(json_dict['status_change'])

        message = PendingJobs()
        message.status_change = status_change
        for job_id in json_dict['job_ids']:
            message.add_job(job_id)

        return message

    def execute(self):
        """See :meth:`messaging.messages.message.CommandMessage.execute`
        """

        with transaction.atomic():
            jobs_to_pending = []
            # Retrieve locked job models
            for job_model in Job.objects.get_locked_jobs(self._pending_job_ids):
                if not job_model.last_status_change or job_model.last_status_change < self.status_change:
                    # Status update is not old, so perform the update
                    jobs_to_pending.append(job_model)

            # Update jobs that need status set to PENDING
            if jobs_to_pending:
                job_ids = Job.objects.update_jobs_to_pending(jobs_to_pending, self.status_change)
                logger.info('Set %d job(s) to PENDING status', len(job_ids))

        # Send messages to update recipe metrics
        from recipe.messages.update_recipe_metrics import create_update_recipe_metrics_messages_from_jobs
        self.new_messages.extend(create_update_recipe_metrics_messages_from_jobs(self._pending_job_ids))

        return True
