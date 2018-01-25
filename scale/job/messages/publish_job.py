"""Defines a command message that publishes a job"""
from __future__ import unicode_literals

import logging

from django.db import transaction
from django.utils.timezone import now

from job.models import JobExecution
from messaging.messages.message import CommandMessage


logger = logging.getLogger(__name__)


def create_publish_job_message(job_id):
    """Creates a publish job message

    :param job_id: The job ID
    :type job_id: int
    :return: The publish job message
    :rtype: :class:`job.messages.publish_job.PublishJob`
    """

    message = PublishJob()
    message.job_id = job_id
    return message


class PublishJob(CommandMessage):
    """Command message that publishes a completed job
    """

    def __init__(self):
        """Constructor
        """

        super(PublishJob, self).__init__('publish_job')

        self.job_id = None

    def to_json(self):
        """See :meth:`messaging.messages.message.CommandMessage.to_json`
        """

        return {'job_id': self.job_id}

    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`
        """

        message = PublishJob()
        message.job_id = json_dict['job_id']
        return message

    def execute(self):
        """See :meth:`messaging.messages.message.CommandMessage.execute`
        """

        when_published = now()

        with transaction.atomic():
            # Retrieve job and job_exe models
            job_exe = JobExecution.objects.get_latest_execution(self.job_id)
            job = job_exe.job

            # Publish this job's products
            from product.models import ProductFile
            ProductFile.objects.publish_products(job_exe.id, job, when_published)

        return True
