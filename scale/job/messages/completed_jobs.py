"""Defines a command message that sets COMPLETED status for job models"""
from __future__ import unicode_literals

import logging
from collections import namedtuple

from django.db import transaction
from django.utils.timezone import now

from job.models import Job, JobExecution
from messaging.messages.message import CommandMessage
from util.parse import datetime_to_string, parse_datetime

# This is the maximum number of job models that can fit in one message. This maximum ensures that every message of this
# type is less than 25 KiB long.
MAX_NUM = 100


CompletedJob = namedtuple('CompletedJob', ['job_id', 'exe_num'])


logger = logging.getLogger(__name__)


def create_completed_jobs_messages(completed_jobs, when):
    """Creates messages to complete the given jobs

    :param completed_jobs: The completed jobs
    :type completed_jobs: list
    :param when: When the jobs completed
    :type when: :class:`datetime.datetime`
    :return: The list of messages
    :rtype: list
    """

    messages = []

    message = None
    for completed_job in completed_jobs:
        if not message:
            message = CompletedJobs()
            message.ended = when
        elif not message.can_fit_more():
            messages.append(message)
            message = CompletedJobs()
            message.ended = when
        message.add_completed_job(completed_job)
    if message:
        messages.append(message)

    return messages


class CompletedJobs(CommandMessage):
    """Command message that sets COMPLETED status for job models
    """

    def __init__(self):
        """Constructor
        """

        super(CompletedJobs, self).__init__('completed_jobs')

        self._completed_jobs = []
        self.ended = None

    def add_completed_job(self, completed_job):
        """Adds the given completed job to this message

        :param completed_job: The completed job
        :type completed_job: :class:`job.messages.completed_jobs.CompletedJob`
        """

        self._completed_jobs.append(completed_job)

    def can_fit_more(self):
        """Indicates whether more completed jobs can fit in this message

        :return: True if more completed jobs can fit, False otherwise
        :rtype: bool
        """

        return len(self._completed_jobs) < MAX_NUM

    def to_json(self):
        """See :meth:`messaging.messages.message.CommandMessage.to_json`
        """

        jobs_list = []
        for completed_job in self._completed_jobs:
            jobs_list.append({'id': completed_job.job_id, 'exe_num': completed_job.exe_num})

        return {'ended': datetime_to_string(self.ended), 'jobs': jobs_list}

    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`
        """

        message = CompletedJobs()
        message.ended = parse_datetime(json_dict['ended'])

        for job_dict in json_dict['jobs']:
            job_id = job_dict['id']
            exe_num = job_dict['exe_num']
            message.add_completed_job(CompletedJob(job_id, exe_num))

        return message

    def execute(self):
        """See :meth:`messaging.messages.message.CommandMessage.execute`
        """

        when = now()
        job_ids = [job.job_id for job in self._completed_jobs]

        with transaction.atomic():
            # Retrieve locked job models
            job_models = {}
            for job_model in Job.objects.get_locked_jobs(job_ids):
                job_models[job_model.id] = job_model

            jobs_to_complete = []
            for completed_job in self._completed_jobs:
                job_model = job_models[completed_job.job_id]
                # If execution number does not match, then this update is obsolete
                if job_model.num_exes != completed_job.exe_num:
                    # Ignore this job
                    continue
                jobs_to_complete.append(job_model)

            # Update jobs to completed
            completed_job_ids = []
            if jobs_to_complete:
                completed_job_ids = Job.objects.update_jobs_to_completed(jobs_to_complete, self.ended)
                logger.info('Set %d job(s) to COMPLETED status', len(completed_job_ids))

            # Process job output to find jobs that are both COMPLETED and have output
            if jobs_to_complete:
                job_ids = [job.id for job in jobs_to_complete]
                jobs_with_output = Job.objects.process_job_output(job_ids, when)
                # Jobs that are COMPLETED and have output should update their recipes
                if jobs_with_output:
                    logger.info('Found %d COMPLETED job(s) with output, ready to update recipe(s)',
                                len(jobs_with_output))
                    self._create_update_recipes_messages(jobs_with_output)

            # TODO: this needs to be improved to be more efficient and not perform batch model locking
            for job_id in completed_job_ids:
                job_model = job_models[job_id]
                # Publish this job's products
                from product.models import ProductFile
                # TODO: product publishing needs to be moved to its own message(s) that fire after process_job_output()
                job_exe = JobExecution.objects.get(job_id=job_id, exe_num=job_model.num_exes)
                ProductFile.objects.publish_products(job_exe.id, job_model, self.ended)
                # Update completed job count if part of a batch
                from batch.models import Batch, BatchJob
                try:
                    batch_job = BatchJob.objects.get(job_id=job_id)
                    Batch.objects.count_completed_job(batch_job.batch.id)
                except BatchJob.DoesNotExist:
                    pass

        return True

    def _create_update_recipes_messages(self, job_ids):
        """Creates messages to update the the recipes for the given jobs that are both COMPLETED and have output

        :param job_ids: The job IDs
        :type job_ids: list
        """

        from recipe.messages.update_recipes import create_update_recipes_messages
        from recipe.models import Recipe

        recipe_ids = Recipe.objects.get_latest_recipe_ids_for_jobs(job_ids)
        self.new_messages.extend(create_update_recipes_messages(recipe_ids))
