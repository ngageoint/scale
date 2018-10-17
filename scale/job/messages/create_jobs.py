"""Defines a command message that creates job models"""
from __future__ import unicode_literals

import logging
from collections import namedtuple

from django.db import transaction

from data.data.json.data_v6 import convert_data_to_v6_json, DataV6
from data.data.exceptions import InvalidData
from job.messages.process_job_input import create_process_job_input_messages
from job.models import Job, JobTypeRevision
from messaging.messages.message import CommandMessage
from trigger.models import TriggerEvent


INPUT_DATA_TYPE = 'input_data'  # Message type for creating a single job with the given input data
RECIPE_TYPE = 'recipe'  # Message type for creating jobs for a recipe


# This is the maximum number of jobs models that can fit in one message. This maximum ensures that every message of this
# type is less than 25 KiB long and that each message can be processed quickly.
MAX_NUM = 100


# Tuple for specifying each job to create for RECIPE_TYPE messages
RecipeJob = namedtuple('RecipeJob', ['job_type_name', 'job_type_version', 'job_type_rev_num', 'node_name',
                                     'process_input'])


logger = logging.getLogger(__name__)


def create_jobs_message(job_type_name, job_type_version, job_type_rev_num, event_id, input_data):
    """Creates a message to create a job of the given type

    :param job_type_name: The job type name
    :type job_type_name: string
    :param job_type_version: The job type version
    :type job_type_version: string
    :param job_type_rev_num: The job type revision number
    :type job_type_rev_num: string
    :param event_id: The event ID
    :type event_id: int
    :param input_data: The input data for the job
    :type input_data: :class:`data.data.data.Data`
    :return: The message for creating the job
    :rtype: :class:`job.messages.create_jobs.CreateJobs`
    """

    message = CreateJobs()
    message.create_jobs_type = INPUT_DATA_TYPE
    message.job_type_name = job_type_name
    message.job_type_version = job_type_version
    message.job_type_rev_num = job_type_rev_num
    message.event_id = event_id
    message.input_data = input_data

    return message


def create_jobs_messages_for_recipe(recipe, recipe_jobs):
    """Creates messages to create jobs with a recipe

    :param recipe: The recipe model
    :type recipe: :class:`recipe.models.Recipe`
    :param recipe_jobs: The list of RecipeJob tuples describing the jobs to create
    :type recipe_jobs: list
    :return: The list of messages
    :rtype: list
    """

    messages = []

    message = None
    for recipe_job in recipe_jobs:
        if not message:
            message = CreateJobs()
            message.create_jobs_type = RECIPE_TYPE
            message.recipe_id = recipe.id
            message.root_recipe_id = recipe.root_superseded_recipe_id
            message.event_id = recipe.event_id
            message.superseded_recipe_id = recipe.superseded_recipe_id
            message.batch_id = recipe.batch_id
        elif not message.can_fit_more():
            messages.append(message)
            message = CreateJobs()
            message.create_jobs_type = RECIPE_TYPE
            message.recipe_id = recipe.id
            message.root_recipe_id = recipe.root_superseded_recipe_id
            message.event_id = recipe.event_id
            message.superseded_recipe_id = recipe.superseded_recipe_id
            message.batch_id = recipe.batch_id
        message.add_recipe_job(recipe_job)
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

        # Fields applicable to all message types
        self.event_id = None

        # The message type for how to create the jobs
        self.create_jobs_type = None

        # Fields applicable for single job created from input data
        self.job_type_name = None
        self.job_type_version = None
        self.job_type_rev_num = None
        self.input_data = None

        # Fields applicable for recipe jobs
        self.batch_id = None
        self.recipe_id = None
        self.root_recipe_id = None
        self.superseded_recipe_id = None
        self.recipe_jobs = []
        self._process_input = {}  # process_input flags stored by new job ID

    def add_recipe_job(self, recipe_job):
        """Adds the given recipe job to this message to be created

        :param recipe_job: The recipe job
        :type recipe_job: :class:`job.messages.create_jobs.RecipeJob`
        """

        if self.create_jobs_type == RECIPE_TYPE:
            self.recipe_jobs.append(recipe_job)

    def can_fit_more(self):
        """Indicates whether more jobs can fit in this message

        :return: True if more jobs can fit, False otherwise
        :rtype: bool
        """

        if self.create_jobs_type == INPUT_DATA_TYPE:
            return False
        elif self.create_jobs_type == RECIPE_TYPE:
            return len(self.recipe_jobs) < MAX_NUM

    def to_json(self):
        """See :meth:`messaging.messages.message.CommandMessage.to_json`
        """

        json_dict = {'event_id': self.event_id, 'create_jobs_type': self.create_jobs_type}

        if self.create_jobs_type == INPUT_DATA_TYPE:
            json_dict['job_type_name'] = self.job_type_name
            json_dict['job_type_version'] = self.job_type_version
            json_dict['job_type_rev_num'] = self.job_type_rev_num
            json_dict['input_data'] = convert_data_to_v6_json(self.input_data).get_dict()
        elif self.create_jobs_type == RECIPE_TYPE:
            json_dict['recipe_id'] = self.recipe_id
            if self.root_recipe_id:
                json_dict['root_recipe_id'] = self.root_recipe_id
            if self.superseded_recipe_id:
                json_dict['superseded_recipe_id'] = self.superseded_recipe_id
            if self.batch_id:
                json_dict['batch_id'] = self.batch_id
            recipe_jobs = []
            for recipe_job in self.recipe_jobs:
                recipe_jobs.append({'job_type_name': recipe_job.job_type_name,
                                    'job_type_version': recipe_job.job_type_version,
                                    'job_type_rev_num': recipe_job.job_type_rev_num, 'node_name': recipe_job.node_name,
                                    'process_input': recipe_job.process_input})
            json_dict['recipe_jobs'] = recipe_jobs

        return json_dict

    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`
        """

        message = CreateJobs()
        message.event_id = json_dict['event_id']
        message.create_jobs_type = json_dict['create_jobs_type']

        if message.create_jobs_type == INPUT_DATA_TYPE:
            message.job_type_name = json_dict['job_type_name']
            message.job_type_version = json_dict['job_type_version']
            message.job_type_rev_num = json_dict['job_type_rev_num']
            message.input_data = DataV6(json_dict['input_data']).get_data()
        elif message.create_jobs_type == RECIPE_TYPE:
            message.recipe_id = json_dict['recipe_id']
            if 'root_recipe_id' in json_dict:
                message.root_recipe_id = json_dict['root_recipe_id']
            if 'superseded_recipe_id' in json_dict:
                message.superseded_recipe_id = json_dict['superseded_recipe_id']
            if 'batch_id' in json_dict:
                message.batch_id = json_dict['batch_id']
            for job_dict in json_dict['recipe_jobs']:
                recipe_job = RecipeJob(job_dict['job_type_name'], job_dict['job_type_version'],
                                       job_dict['job_type_rev_num'], job_dict['node_name'], job_dict['process_input'])
                message.add_recipe_job(recipe_job)

        return message

    def execute(self):
        """See :meth:`messaging.messages.message.CommandMessage.execute`
        """

        with transaction.atomic():
            self._perform_locking()
            jobs = self._find_existing_jobs()
            if not jobs:
                jobs = self._create_jobs()

        process_input_job_ids = []
        for job in jobs:
            # process_input indicates if job is in a recipe and ready to get its input from its dependencies
            process_input = self.recipe_id and self._process_input.get(job.id, False)
            if job.has_input() or process_input:
                # This new job is all ready to have its input processed
                process_input_job_ids.append(job.id)
        self.new_messages.extend(create_process_job_input_messages(process_input_job_ids))

        if self.recipe_id:
            # If these jobs belong to a recipe, update its metrics now that the jobs are created
            from recipe.messages.update_recipe_metrics import create_update_recipe_metrics_messages
            self.new_messages.extend(create_update_recipe_metrics_messages([self.recipe_id]))

        return True

    def _create_job_from_input_data(self):
        """Creates the job model for the input data

        :returns: The created job model
        :rtype: :class:`job.models.Job`
        """

        job_type_rev = JobTypeRevision.objects.get_revision(self.job_type_name, self.job_type_version,
                                                            self.job_type_rev_num)

        try:
            job = Job.objects.create_job_v6(job_type_rev, self.event_id, input_data=self.input_data)
            job.save()
        except InvalidData:
            msg = 'Job of type (%s, %s, %d) was given invalid input data. Message will not re-run.'
            logger.exception(msg, self.job_type_name, self.job_type_version, self.job_type_rev_num)
            job = None

        return job

    def _create_jobs(self):
        """Creates the job models for the message

        :returns: The list of job models created
        :rtype: list
        """

        jobs = []

        if self.create_jobs_type == INPUT_DATA_TYPE:
            job = self._create_job_from_input_data()
            if job:
                jobs.append(job)
        elif self.create_jobs_type == RECIPE_TYPE:
            jobs = self._create_jobs_for_recipe()

        return jobs

    def _create_jobs_for_recipe(self):
        """Creates the job models for a recipe

        :returns: The list of job models created
        :rtype: list
        """

        from recipe.models import RecipeNode

        recipe_jobs = {}  # {Node name: job model}

        superseded_jobs = {}
        # Get superseded jobs from superseded recipe
        if self.superseded_recipe_id:
            superseded_jobs = RecipeNode.objects.get_recipe_jobs(self.superseded_recipe_id)

        # Get job type revisions
        revision_tuples = [(j.job_type_name, j.job_type_version, j.job_type_rev_num) for j in self.recipe_jobs]
        revs_by_id = JobTypeRevision.objects.get_revisions(revision_tuples)
        revs_by_tuple = {(j.job_type.name, j.job_type.version, j.revision_num): j for j in revs_by_id.values()}

        # Create new job models
        process_input_by_node = {}
        for recipe_job in self.recipe_jobs:
            node_name = recipe_job.node_name
            process_input_by_node[node_name] = recipe_job.process_input
            tup = (recipe_job.job_type_name, recipe_job.job_type_version, recipe_job.job_type_rev_num)
            revision = revs_by_tuple[tup]
            superseded_job = superseded_jobs[node_name] if node_name in superseded_jobs else None
            job = Job.objects.create_job_v6(revision, self.event_id, root_recipe_id=self.root_recipe_id,
                                            recipe_id=self.recipe_id, batch_id=self.batch_id,
                                            superseded_job=superseded_job)
            recipe_jobs[node_name] = job

        Job.objects.bulk_create(recipe_jobs.values())
        logger.info('Created %d job(s)', len(recipe_jobs))

        # Create recipe nodes
        recipe_nodes = RecipeNode.objects.create_recipe_job_nodes(self.recipe_id, recipe_jobs)
        RecipeNode.objects.bulk_create(recipe_nodes)

        # Set up process input dict
        for recipe_job in self.recipe_jobs:
            job = recipe_jobs[recipe_job.node_name]
            self._process_input[job.id] = recipe_job.process_input

        return recipe_jobs.values()

    def _find_existing_jobs(self):
        """Searches to determine if this message already ran and the jobs already exist

        :returns: The list of job models found
        :rtype: list
        """

        if self.create_jobs_type == INPUT_DATA_TYPE:
            jobs = Job.objects.filter(job_type__name=self.job_type_name, job_type__version=self.job_type_version,
                                      job_type_rev__revision_num=self.job_type_rev_num, event_id=self.event_id,
                                      input=convert_data_to_v6_json(self.input_data).get_dict())
        elif self.create_jobs_type == RECIPE_TYPE:
            from recipe.models import RecipeNode

            node_names = [recipe_job.node_name for recipe_job in self.recipe_jobs]
            qry = RecipeNode.objects.select_related('job')
            qry = qry.filter(recipe_id=self.recipe_id, node_name__in=node_names, job__event_id=self.event_id)
            jobs_by_node = {recipe_node.node_name: recipe_node.job for recipe_node in qry}
            jobs = jobs_by_node.values()

            if jobs_by_node:
                # Set up process input dict
                for recipe_job in self.recipe_jobs:
                    job = jobs_by_node[recipe_job.node_name]
                    self._process_input[job.id] = recipe_job.process_input

        return jobs

    def _perform_locking(self):
        """Performs locking so that multiple messages don't interfere with each other. The caller must be within an
        atomic transaction.
        """

        if self.create_jobs_type == INPUT_DATA_TYPE:
            TriggerEvent.objects.get_locked_event(self.event_id)
        elif self.create_jobs_type == RECIPE_TYPE:
            from recipe.models import Recipe
            Recipe.objects.get_locked_recipe(self.recipe_id)
