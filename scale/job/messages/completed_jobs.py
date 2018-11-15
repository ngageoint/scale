"""Defines a command message that sets COMPLETED status for job models"""
from __future__ import unicode_literals

import logging
from collections import namedtuple

from django.db import transaction
from django.utils.timezone import now

from job.messages.publish_job import create_publish_job_message
from job.models import Job
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


def process_completed_jobs_with_output(job_ids, when):
    """Processes the given job IDs to determine if any of the jobs have both COMPLETED and received their output.
    Messages will be created and returned for completed jobs that have their output populated. Caller must have obtained
    model locks on the given jobs.

    :param job_ids: The job IDs
    :type job_ids: list
    :param when: The current time
    :type when: :class:`datetime.datetime`
    :return: The list of created messages
    :rtype: list
    """

    messages = []

    # Find jobs that are COMPLETED and have output
    completed_job_ids_with_output = Job.objects.process_job_output(job_ids, when)
    if completed_job_ids_with_output:
        logger.info('Found %d COMPLETED job(s) with output', len(completed_job_ids_with_output))

        # Create messages to update recipes
        from recipe.messages.update_recipe import create_update_recipe_messages_from_node
        root_recipe_ids = set()
        for job in Job.objects.filter(id__in=completed_job_ids_with_output):
            if job.root_recipe_id:
                root_recipe_ids.add(job.root_recipe_id)
        messages.extend(create_update_recipe_messages_from_node(root_recipe_ids))

        # Create messages to publish each job
        for job_id in completed_job_ids_with_output:
            messages.append(create_publish_job_message(job_id))

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
            job_ids_to_complete = [job.id for job in jobs_to_complete]

            # Update jobs to completed
            completed_job_ids = []
            if jobs_to_complete:
                completed_job_ids = Job.objects.update_jobs_to_completed(jobs_to_complete, self.ended)
                logger.info('Set %d job(s) to COMPLETED status', len(completed_job_ids))

            # Create messages for jobs that are both COMPLETED and have output
            if job_ids_to_complete:
                msgs = process_completed_jobs_with_output(job_ids_to_complete, when)
                self.new_messages.extend(msgs)

        # Send messages to update recipe metrics
        from recipe.messages.update_recipe_metrics import create_update_recipe_metrics_messages_from_jobs
        self.new_messages.extend(create_update_recipe_metrics_messages_from_jobs(job_ids))

        return True
