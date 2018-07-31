"""Defines a command message that creates job models"""
from __future__ import unicode_literals

import logging

from django.db import transaction

from data.data.json.data_v6 import DataV6
from data.data.exceptions import InvalidData
from job.messages.process_job_input import create_process_job_input_messages
from job.models import Job, JobTypeRevision
from messaging.messages.message import CommandMessage
from util.parse import datetime_to_string, parse_datetime


logger = logging.getLogger(__name__)


# TODO: update/implement
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


class CreateJobs(CommandMessage):
    """Command message that creates job models
    """

    def __init__(self):
        """Constructor
        """

        super(CreateJobs, self).__init__('create_jobs')

        self.count = 1
        self.job_type_name = None
        self.job_type_version = None
        self.job_type_rev_num = None
        self.event_id = None
        self.input_data = None
        self.root_recipe_id = None
        self.superseded_recipe_id = None
        self.recipe_id = None
        self.recipe_node_name = None
        self.batch_id = None
        self.process_input = False

    # TODO: implement
    def to_json(self):
        """See :meth:`messaging.messages.message.CommandMessage.to_json`
        """

        jobs_list = []
        for completed_job in self._completed_jobs:
            jobs_list.append({'id': completed_job.job_id, 'exe_num': completed_job.exe_num})

        return {'ended': datetime_to_string(self.ended), 'jobs': jobs_list}

    # TODO: implement
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

        job_type_rev = JobTypeRevision.objects.get_revision(self.job_type_name, self.job_type_version,
                                                            self.job_type_rev_num)

        # Check to see if jobs were already created so that message is idempotent
        jobs = self._find_existing_jobs(job_type_rev)
        if not jobs:
            jobs = self._create_jobs(job_type_rev)

        # If the jobs already have their input data or process_input flag is set (recipe is ready to pass input), send
        # messages to process job input
        if jobs and (self.input_data or self.process_input):
            job_ids = [job.id for job in jobs]
            self.new_messages.extend(create_process_job_input_messages(job_ids))

        return True

    def _create_jobs(self, job_type_rev):
        """Creates the job models for the message

        :param job_type_rev: The job type revision with populated job_type model
        :type job_type_rev: :class:`job.models.JobTypeRevision`
        :returns: The list of job models created
        :rtype: list
        """

        jobs = []

        # If this job is in a recipe that supersedes another recipe, find the corresponding superseded job
        superseded_job = None
        if self.superseded_recipe_id:
            from recipe.models import RecipeNode
            superseded_jobs = RecipeNode.objects.get_superseded_recipe_jobs(self.superseded_recipe_id,
                                                                            self.recipe_node_name)
            if len(superseded_jobs) == 1:
                superseded_job = superseded_jobs[0]

        try:
            with transaction.atomic():
                # Bulk create jobs
                for _ in xrange(self.count):
                    input_data = DataV6(self.input_data, do_validate=True) if self.input_data else None
                    job = Job.objects.create_job_v6(job_type_rev, self.event_id, input_data=input_data,
                                                    root_recipe_id=self.root_recipe_id, recipe_id=self.recipe_id,
                                                    batch_id=self.batch_id, superseded_job=superseded_job)
                    jobs.append(job)
                Job.objects.bulk_create(jobs)

                if self.recipe_id:
                    # Bulk create recipe nodes
                    node_models = RecipeNode.objects.create_recipe_job_nodes(self.recipe_id, self.recipe_node_name,
                                                                             jobs)
                    RecipeNode.objects.bulk_create(node_models)
        except InvalidData:
            msg = 'Job of type (%s, %s, %d) was given invalid input data. Message will not re-run.'
            logger.exception(msg, self.job_type_name, self.job_type_version, self.job_type_rev_num)
            jobs = []

        return jobs

    def _find_existing_jobs(self, job_type_rev):
        """Searches to determine if this message already ran and the jobs already exist

        :param job_type_rev: The job type revision with populated job_type model
        :type job_type_rev: :class:`job.models.JobTypeRevision`
        :returns: The list of job models found
        :rtype: list
        """

        from recipe.models import RecipeNode

        if self.recipe_id:
            qry = RecipeNode.objects.filter(recipe_id=self.recipe_id, node_name=self.recipe_node_name)
            qry = qry.filter(job__job_type_rev_id=job_type_rev.id, job__event_id=self.event_id)
        else:
            qry = Job.objects.filter(job_type_rev_id=job_type_rev.id, event_id=self.event_id)

        return qry
