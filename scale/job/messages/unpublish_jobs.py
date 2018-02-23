"""Defines a command message that unpublishes a list of jobs"""
from __future__ import unicode_literals

import logging

from messaging.messages.message import CommandMessage
from product.models import ProductFile
from util.parse import datetime_to_string, parse_datetime

# This is the maximum number of job models that can fit in one message. This maximum ensures that every message of this
# type is less than 25 KiB long and that each message can be processed quickly.
MAX_NUM = 100


logger = logging.getLogger(__name__)


def create_unpublish_jobs_messages(job_ids, when):
    """Creates messages to unpublish the given jobs

    :param job_ids: The job IDs to unpublish
    :type job_ids: list
    :param when: When the jobs were unpublished
    :type when: :class:`datetime.datetime`
    :return: The list of messages
    :rtype: list
    """

    messages = []

    message = None
    for job_id in job_ids:
        if not message:
            message = UnpublishJobs()
            message.when = when
        elif not message.can_fit_more():
            messages.append(message)
            message = UnpublishJobs()
            message.when = when
        message.add_job(job_id)
    if message:
        messages.append(message)

    return messages


class UnpublishJobs(CommandMessage):
    """Command message that punpublishes a list of jobs
    """

    def __init__(self):
        """Constructor
        """

        super(UnpublishJobs, self).__init__('unpublish_jobs')

        self._count = 0
        self._job_ids = []
        self.when = None

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

        return {'job_ids': self._job_ids, 'when': datetime_to_string(self.when)}

    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`
        """

        message = UnpublishJobs()
        message.when = parse_datetime(json_dict['when'])
        for job_id in json_dict['job_ids']:
            message.add_job(job_id)
        return message

    def execute(self):
        """See :meth:`messaging.messages.message.CommandMessage.execute`
        """

        ProductFile.objects.unpublish_products(self._job_ids, self.when)
        return True
