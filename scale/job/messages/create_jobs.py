"""Defines a command message that creates job models"""
from __future__ import unicode_literals

import logging

from django.db import transaction

from data.data.json.data_v6 import DataV6
from data.data.exceptions import InvalidData
from job.messages.process_job_input import create_process_job_input_messages
from job.models import Job, JobTypeRevision
from messaging.messages.message import CommandMessage


logger = logging.getLogger(__name__)


def create_jobs_message(job_type_name, job_type_version, job_type_rev_num, event_id, count=1, input_data_dict=None):
    """Creates a message to create job(s) of the given type

    :param job_type_name: The job type name
    :type job_type_name: string
    :param job_type_version: The job type version
    :type job_type_version: string
    :param job_type_rev_num: The job type revision number
    :type job_type_rev_num: string
    :param event_id: The event ID
    :type event_id: int
    :param count: The number of jobs to create
    :type count: int
    :param input_data_dict: The optional JSON dict of the input data for the job(s)
    :type input_data_dict: dict
    :return: The message for creating the job(s)
    :rtype: :class:`job.messages.create_jobs.CreateJobs`
    """

    message = CreateJobs()
    message.count = count
    message.job_type_name = job_type_name
    message.job_type_version = job_type_version
    message.job_type_rev_num = job_type_rev_num
    message.event_id = event_id
    message.input_data = input_data_dict

    return message


def create_jobs_message_for_recipe(recipe, node_name, job_type_name, job_type_version, job_type_rev_num, count=1,
                                   process_input=False):
    """Creates a message to create job(s) of the given type for the given recipe

    :param recipe: The recipe
    :type recipe: :class:`recipe.models.Recipe`
    :param node_name: The node name for the job(s) within the recipe
    :type node_name: string
    :param job_type_name: The job type name
    :type job_type_name: string
    :param job_type_version: The job type version
    :type job_type_version: string
    :param job_type_rev_num: The job type revision number
    :type job_type_rev_num: string
    :param count: The number of jobs to create
    :type count: int
    :return: The message for creating the job(s)
    :rtype: :class:`job.messages.create_jobs.CreateJobs`
    """

    message = create_jobs_message(job_type_name, job_type_version, job_type_rev_num, recipe.event_id, count=count)

    message.root_recipe_id = recipe.root_superseded_recipe_id
    message.superseded_recipe_id = recipe.superseded_recipe_id
    message.recipe_id = recipe.id
    message.recipe_node_name = node_name
    message.batch_id = recipe.batch_id
    message.process_input = process_input

    return message


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

    def to_json(self):
        """See :meth:`messaging.messages.message.CommandMessage.to_json`
        """

        json_dict = {'count': self.count, 'job_type_name': self.job_type_name,
                     'job_type_version': self.job_type_version, 'job_type_rev_num': self.job_type_rev_num,
                     'event_id': self.event_id, 'process_input': self.process_input}

        if self.input_data:
            json_dict['input_data'] = self.input_data
        if self.root_recipe_id:
            json_dict['root_recipe_id'] = self.root_recipe_id
        if self.superseded_recipe_id:
            json_dict['superseded_recipe_id'] = self.superseded_recipe_id
        if self.recipe_id:
            json_dict['recipe_id'] = self.recipe_id
        if self.recipe_node_name:
            json_dict['recipe_node_name'] = self.recipe_node_name
        if self.batch_id:
            json_dict['batch_id'] = self.batch_id

        return json_dict

    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`
        """

        message = CreateJobs()
        message.count = json_dict['count']
        message.job_type_name = json_dict['job_type_name']
        message.job_type_version = json_dict['job_type_version']
        message.job_type_rev_num = json_dict['job_type_rev_num']
        message.event_id = json_dict['event_id']
        message.process_input = json_dict['process_input']

        if 'input_data' in json_dict:
            message.input_data = json_dict['input_data']
        if 'root_recipe_id' in json_dict:
            message.root_recipe_id = json_dict['root_recipe_id']
        if 'superseded_recipe_id' in json_dict:
            message.superseded_recipe_id = json_dict['superseded_recipe_id']
        if 'recipe_id' in json_dict:
            message.recipe_id = json_dict['recipe_id']
        if 'recipe_node_name' in json_dict:
            message.recipe_node_name = json_dict['recipe_node_name']
        if 'batch_id' in json_dict:
            message.batch_id = json_dict['batch_id']

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

        from recipe.models import RecipeNode

        jobs = []

        # If this new job(s) is in a recipe that supersedes another recipe, find the corresponding superseded job(s)
        superseded_job = None
        if self.superseded_recipe_id:
            superseded_jobs = RecipeNode.objects.get_superseded_recipe_jobs(self.superseded_recipe_id,
                                                                            self.recipe_node_name)
            if len(superseded_jobs) == 1:
                superseded_job = superseded_jobs[0]

        try:
            with transaction.atomic():
                # Bulk create jobs
                for _ in xrange(self.count):
                    input_data = DataV6(self.input_data, do_validate=True).get_data() if self.input_data else None
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
            jobs = [recipe_node.job for recipe_node in qry]
        else:
            jobs = list(Job.objects.filter(job_type_rev_id=job_type_rev.id, event_id=self.event_id))

        return jobs
