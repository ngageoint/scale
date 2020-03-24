"""Defines a command message that purges jobs"""
from __future__ import unicode_literals

import logging

from django.db import transaction
from django.db.models import F

from job.models import Job, JobExecution, JobExecutionEnd, JobExecutionOutput, JobInputFile, TaskUpdate
from messaging.messages.message import CommandMessage
from product.models import FileAncestryLink
from queue.models import Queue
from recipe.models import RecipeNode
from recipe.messages.purge_recipe import create_purge_recipe_message
from source.messages.purge_source_file import create_purge_source_file_message
from storage.models import PurgeResults

# This is the maximum number of job models that can fit in one message. This maximum ensures that every message of this
# type is less than 25 KiB long.
MAX_NUM = 100


logger = logging.getLogger(__name__)


def create_purge_jobs_messages(purge_job_ids, trigger_id, source_file_id):
    """Creates messages to remove the given job IDs

    :param purge_job_ids: The job IDs
    :type purge_job_ids: :func:`list`
    :param trigger_id: The trigger event id for the purge operation
    :type trigger_id: int
    :param source_file_id: The source file id for the original file being purged
    :type source_file_id: int
    :return: The list of messages
    :rtype: :func:`list`
    """

    messages = []

    message = None
    for job_id in purge_job_ids:
        if not message:
            message = PurgeJobs()
        elif not message.can_fit_more():
            messages.append(message)
            message = PurgeJobs()
        message.add_job(job_id)
        message.trigger_id = trigger_id
        message.source_file_id = source_file_id
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
        self.trigger_id = None
        self.source_file_id = None

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

        return {'job_ids': self._purge_job_ids, 'trigger_id': self.trigger_id, 'source_file_id': self.source_file_id}

    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`
        """

        message = PurgeJobs()
        message.trigger_id = json_dict['trigger_id']
        message.source_file_id = json_dict['source_file_id']
        for job_id in json_dict['job_ids']:
            message.add_job(job_id)

        return message

    def execute(self):
        """See :meth:`messaging.messages.message.CommandMessage.execute`
        """

        # Check to see if a force stop was placed on this purge process
        results = PurgeResults.objects.get(trigger_event=self.trigger_id)
        if results.force_stop_purge:
            return True

        # Kick off purge_source_file for the source file input
        self.new_messages.append(create_purge_source_file_message(source_file_id=self.source_file_id,
                                                                  trigger_id=self.trigger_id))

        # Kick off purge_recipe for recipe with node job
        parent_recipes = RecipeNode.objects.filter(job__in=self._purge_job_ids, is_original=True)
        for recipe_node in parent_recipes:
            self.new_messages.append(create_purge_recipe_message(recipe_id=recipe_node.recipe.id,
                                                                 trigger_id=self.trigger_id,
                                                                 source_file_id=self.source_file_id))

        with transaction.atomic():
            job_exe_queryset = JobExecution.objects.filter(job__in=self._purge_job_ids)
            TaskUpdate.objects.filter(job_exe__in=job_exe_queryset).delete()
            JobExecutionOutput.objects.filter(job_exe__in=job_exe_queryset).delete()
            JobExecutionEnd.objects.filter(job_exe__in=job_exe_queryset).delete()
            FileAncestryLink.objects.filter(job__in=self._purge_job_ids).delete()
            job_exe_queryset.delete()
            RecipeNode.objects.filter(job__in=self._purge_job_ids).delete()
            JobInputFile.objects.filter(job__in=self._purge_job_ids).delete()
            Queue.objects.filter(job__in=self._purge_job_ids).delete()
            Job.objects.filter(id__in=self._purge_job_ids).delete()

            # Update results
            PurgeResults.objects.filter(trigger_event=self.trigger_id).update(
                num_jobs_deleted = F('num_jobs_deleted') + len(self._purge_job_ids))

        return True
