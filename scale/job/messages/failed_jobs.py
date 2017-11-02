"""Defines a command message that sets FAILED status for job models"""
from __future__ import unicode_literals

import logging
from collections import namedtuple

from django.db import transaction

from error.models import get_error
from job.models import Job
from messaging.messages.message import CommandMessage
from util.parse import datetime_to_string, parse_datetime

# This is the maximum number of job models that can fit in one message. This maximum ensures that every message of this
# type is less than 25 KiB long.
MAX_NUM = 100


FailedJob = namedtuple('FailedJob', ['job_id', 'exe_num'])


logger = logging.getLogger(__name__)


class FailedJobs(CommandMessage):
    """Command message that sets FAILED status for job models
    """

    def __init__(self):
        """Constructor
        """

        super(FailedJobs, self).__init__('failed_jobs')

        self._count = 0
        self._failed_jobs = {}  # {Error ID: [FailedJob]}
        self.ended = None

    def add_failed_job(self, job_id, exe_num, error_id):
        """Adds the given failed job to this message

        :param job_id: The failed job ID
        :type job_id: int
        :param exe_num: The failed job's execution number
        :type exe_num: int
        :param error_id: The error ID for the failure
        :type error_id: int
        """

        self._count += 1
        failed_job = FailedJob(job_id, exe_num)
        if error_id in self._failed_jobs:
            self._failed_jobs[error_id].append(failed_job)
        else:
            self._failed_jobs[error_id] = [failed_job]

    def can_fit_more(self):
        """Indicates whether more failed jobs can fit in this message

        :return: True if more failed jobs can fit, False otherwise
        :rtype: bool
        """

        return self._count < MAX_NUM

    def to_json(self):
        """See :meth:`messaging.messages.message.CommandMessage.to_json`
        """

        error_list = []
        for error_id, job_list in self._failed_jobs.items():
            jobs_list = []
            for failed_job in job_list:
                jobs_list.append({'id': failed_job.job_id, 'exe_num': failed_job.exe_num})
            error_list.append({'id': error_id, 'jobs': jobs_list})

        return {'ended': datetime_to_string(self.ended), 'errors': error_list}

    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`
        """

        message = FailedJobs()
        message.ended = parse_datetime(json_dict['ended'])

        for error_dict in json_dict['errors']:
            error_id = error_dict['id']
            for job_dict in error_dict['jobs']:
                job_id = job_dict['id']
                exe_num = job_dict['exe_num']
                message.add_failed_job(job_id, exe_num, error_id)

        return message

    def execute(self):
        """See :meth:`messaging.messages.message.CommandMessage.execute`
        """

        job_ids = []
        for job_list in self._failed_jobs.values():
            for failed_job in job_list:
                job_ids.append(failed_job.job_id)

        with transaction.atomic():
            # Retrieve locked job models
            job_models = {}
            for job in Job.objects.get_locked_jobs(job_ids):
                job_models[job.id] = job

            # Get job models with related fields
            # TODO: once long running job types are gone, the related fields are not needed
            for job in Job.objects.get_jobs_with_related(job_ids):
                job_models[job.id] = job

            jobs_to_retry = []
            all_failed_job_ids = []
            for error_id, job_list in self._failed_jobs.items():
                error = get_error(error_id)
                jobs_to_fail = []
                for failed_job in job_list:
                    job_model = job_models[failed_job.job_id]
                    # If execution number does not match, then this update is obsolete
                    if job_model.num_exes != failed_job.exe_num:
                        # Ignore this job
                        continue

                    # Re-try job if error supports re-try and there are more tries left
                    retry = error.should_be_retried and job_model.num_exes < job_model.max_tries
                    # Also re-try long running jobs
                    retry = retry or job_model.job_type.is_long_running
                    # Do not re-try superseded jobs
                    retry = retry and not job_model.is_superseded

                    if retry:
                        jobs_to_retry.append(job_model)
                    else:
                        jobs_to_fail.append(job_model)

                # Update jobs that failed with this error
                if jobs_to_fail:
                    failed_job_ids = Job.objects.update_jobs_to_failed(jobs_to_fail, error_id, self.ended)
                    logger.info('Set %d job(s) to FAILED status with error %s', len(failed_job_ids), error.name)
                    all_failed_job_ids.extend(failed_job_ids)

            # Need to update recipes of failed jobs so that dependent jobs are BLOCKED
            if all_failed_job_ids:
                self._create_update_recipes_messages(all_failed_job_ids)

            # Place jobs to retry back onto the queue
            if jobs_to_retry:
                self._create_queued_jobs_messages(jobs_to_retry)

        return True

    def _create_queued_jobs_messages(self, jobs):
        """Creates messages to queue the given jobs that should be retried

        :param jobs: The job models to queue
        :type jobs: list
        """

        from queue.messages.queued_jobs import QueuedJobs

        message = None
        for job in jobs:
            if not message:
                message = QueuedJobs()
            elif not message.can_fit_more():
                self.new_messages.append(message)
                message = QueuedJobs()
            message.add_job(job.id, job.num_exes)
        if message:
            self.new_messages.append(message)

    def _create_update_recipes_messages(self, failed_job_ids):
        """Creates messages to update the the recipes for the given failed jobs

        :param failed_job_ids: The job IDs
        :type failed_job_ids: list
        """

        from recipe.messages.update_recipes import UpdateRecipes
        from recipe.models import Recipe
        recipe_ids = Recipe.objects.get_latest_recipe_ids_for_jobs(failed_job_ids)

        message = None
        for recipe_id in recipe_ids:
            if not message:
                message = UpdateRecipes()
            elif not message.can_fit_more():
                self.new_messages.append(message)
                message = UpdateRecipes()
            message.add_recipe(recipe_id)
        if message:
            self.new_messages.append(message)
