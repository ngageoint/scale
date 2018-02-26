"""Defines a command message that uncancels job models"""
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


def create_uncancel_jobs_messages(job_ids, when):
    """Creates messages to uncancel the given job IDs

    :param job_ids: The job IDs
    :type job_ids: list
    :param when: The time the jobs were uncanceled
    :type when: :class:`datetime.datetime`
    :return: The list of messages
    :rtype: list
    """

    messages = []

    message = None
    for job_id in job_ids:
        if not message:
            message = UncancelJobs()
            message.when = when
        elif not message.can_fit_more():
            messages.append(message)
            message = UncancelJobs()
            message.when = when
        message.add_job(job_id)
    if message:
        messages.append(message)

    return messages


class UncancelJobs(CommandMessage):
    """Command message that sets uncancels job models (jobs that have never been queued before)
    """

    def __init__(self):
        """Constructor
        """

        super(UncancelJobs, self).__init__('uncancel_jobs')

        self._job_ids = []
        self.when = None

    def add_job(self, job_id):
        """Adds the given job ID to this message

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

        return {'when': datetime_to_string(self.when), 'job_ids': self._job_ids}

    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`
        """

        when = parse_datetime(json_dict['when'])

        message = UncancelJobs()
        message.when = when
        for job_id in json_dict['job_ids']:
            message.add_job(job_id)

        return message

    def execute(self):
        """See :meth:`messaging.messages.message.CommandMessage.execute`
        """

        with transaction.atomic():
            jobs_to_pending = []
            # Retrieve locked job models
            for job_model in Job.objects.get_locked_jobs(self._job_ids):
                if job_model.can_be_uncanceled():
                    jobs_to_pending.append(job_model)

            # Uncancel jobs by setting them to PENDING
            if jobs_to_pending:
                job_ids = Job.objects.update_jobs_to_pending(jobs_to_pending, self.when)
                logger.info('Set %d job(s) to PENDING status', len(job_ids))

        # Create messages to update recipes
        from recipe.messages.update_recipes import create_update_recipes_messages_from_jobs
        self.new_messages.extend(create_update_recipes_messages_from_jobs(self._job_ids))

        return True
