"""Defines a command message that purges jobs"""
from __future__ import unicode_literals

import logging

from django.db import transaction
from django.utils.timezone import now

from batch.models import BatchJob
from job.models import Job, JobExecution, JobExecutionEnd, JobExecutionOutput, JobInputFile, TaskUpdate
from product.models import FileAncestryLink
from queue.models import Queue
from recipe.models import RecipeNode
from messaging.messages.message import CommandMessage
from util.parse import datetime_to_string, parse_datetime

# This is the maximum number of job models that can fit in one message. This maximum ensures that every message of this
# type is less than 25 KiB long.
MAX_NUM = 100


logger = logging.getLogger(__name__)


def create_purge_jobs_messages(purge_job_ids, when):
    """Creates messages to remove the given job IDs

    :param purge_job_ids: The job IDs
    :type purge_job_ids: list
    :param when: The current time
    :type when: :class:`datetime.datetime`
    :return: The list of messages
    :rtype: list
    """

    messages = []

    message = None
    for job_id in purge_job_ids:
        if not message:
            message = PurgeJobs()
            message.status_change = when
        elif not message.can_fit_more():
            messages.append(message)
            message = PurgeJobs()
            message.status_change = when
        message.add_job(job_id)
    if message:
        messages.append(message)

    return messages


class PurgeJobs(CommandMessage):
    """Command message that removes job models
    """

    def __init__(self):
        """Constructor
        """

        super(PurgeJobs, self).__init__('purge_jobs')

        self._count = 0
        self._purge_job_ids = []
        self.status_change = None

    def add_job(self, job_id):
        """Adds the given job ID to this message

        :param job_id: The job ID
        :type job_id: int
        """

        self._count += 1
        self._purge_job_ids.append(job_id)

    def can_fit_more(self):
        """Indicates whether more jobs can fit in this message

        :return: True if more jobs can fit, False otherwise
        :rtype: bool
        """

        return self._count < MAX_NUM

    def to_json(self):
        """See :meth:`messaging.messages.message.CommandMessage.to_json`
        """

        return {'status_change': datetime_to_string(self.status_change), 'job_ids': self._purge_job_ids}

    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`
        """

        status_change = parse_datetime(json_dict['status_change'])

        message = PurgeJobs()
        message.status_change = status_change
        for job_id in json_dict['job_ids']:
            message.add_job(job_id)

        return message

    def execute(self):
        """See :meth:`messaging.messages.message.CommandMessage.execute`
        """

        with transaction.atomic():
            FileAncestryLink.objects.filter(job__in=self._purge_job_ids).delete()
            TaskUpdate.objects.filter().delete() # sub filter based off job_exe? 
            JobExecutionOutput.objects.filter().delete()
            JobExecutionEnd.objects.filter().delete()
            JobExecution.objects.filter(job__in=self._purge_job_ids).delete()
            BatchJob.filter(job__in=self._purge_job_ids).delete()
            RecipeNode.objects.filter(job__in=self._purge_job_ids).delete()
            JobInputFile.objects.filter(job__in=self._purge_job_ids).delete()
            Queue.objects.filter(job__in=self._purge_job_ids).delete()
            Job.objects.filter(id__in=self._purge_job_ids).delete()

        return True
