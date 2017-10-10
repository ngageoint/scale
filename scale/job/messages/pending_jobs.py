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
            job_ids_for_status_update = []
            # Retrieve locked job models
            for job_model in Job.objects.get_locked_jobs(self._pending_job_ids):
                if job_model.has_been_queued():
                    continue  # Jobs that have already been queued cannot go back to PENDING state, ignore job
                if job_model.status == 'PENDING':
                    continue  # Job is already PENDING, so ignore
                if job_model.last_status_change < self.status_change:
                    # Status update is not old, so perform the update
                    job_ids_for_status_update.append(job_model.id)

            # Update jobs that need status set to PENDING
            if job_ids_for_status_update:
                logger.info('Setting %d job(s) to PENDING status', len(job_ids_for_status_update))
                Job.objects.update_jobs_to_pending(job_ids_for_status_update, self.status_change)

        return True
