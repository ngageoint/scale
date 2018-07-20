"""Defines a command message that processes the input for a job"""
from __future__ import unicode_literals

import logging

from django.db import transaction

from data.data.exceptions import InvalidData
from job.models import Job
from messaging.messages.message import CommandMessage


logger = logging.getLogger(__name__)


def create_process_job_input_messages(job_ids):
    """Creates messages to process the input for the given jobs

    :param job_ids: The job IDs
    :type job_ids: list
    :return: The list of messages
    :rtype: list
    """

    messages = []

    for job_id in job_ids:
        message = ProcessJobInput()
        message.job_id = job_id
        messages.append(message)

    return messages


class ProcessJobInput(CommandMessage):
    """Command message that processes the input for a job
    """

    def __init__(self):
        """Constructor
        """

        super(ProcessJobInput, self).__init__('process_job_input')

        self.job_id = None

    def to_json(self):
        """See :meth:`messaging.messages.message.CommandMessage.to_json`
        """

        return {'job_id': self.job_id}

    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`
        """

        message = ProcessJobInput()
        message.job_id = json_dict['job_id']
        return message

    def execute(self):
        """See :meth:`messaging.messages.message.CommandMessage.execute`
        """

        from queue.messages.queued_jobs import create_queued_jobs_messages, QueuedJob

        job = Job.objects.get_job_with_interfaces(self.job_id)

        if not job.has_input():
            if not job.recipe:
                logger.error('Job %d has no input and is not in a recipe. Message will not re-run.', self.job_id)
                return True

            try:
                self._generate_input_data_from_recipe(job)
            except InvalidData:
                logger.exception('Recipe created invalid input data for job %d. Message will not re-run.', self.job_id)
                return True

        # Lock job model and process job's input data
        with transaction.atomic():
            job = Job.objects.get_locked_job(self.job_id)
            Job.objects.process_job_input_data(job)

        # Create message to queue the job
        if job.num_exes == 0:
            logger.info('Processed inputs for job %d, sending message to queue job', self.job_id)
            self.new_messages.extend(create_queued_jobs_messages([QueuedJob(job.id, 0)], requeue=False))

        return True

    def _generate_input_data_from_recipe(self, job):
        """Generates the job's input data from its recipe dependencies and validates and sets the input data on the job

        :param job: The job with related job_type_rev and recipe__recipe_type_rev models
        :type job: :class:`job.models.Job`

        :raises :class:`data.data.exceptions.InvalidData`: If the data is invalid
        """

        from recipe.models import RecipeNode

        # TODO: this is a hack to work with old legacy recipe data with workspaces, remove when legacy job types go
        old_recipe_input_dict = dict(job.recipe.input)

        # Get job input from dependencies in the recipe
        recipe_input_data = job.recipe.get_input_data()
        node_outputs = RecipeNode.objects.get_recipe_node_outputs(job.recipe_id)
        for node_output in node_outputs.values():
            if node_output.node_type == 'job' and node_output.id == job.id:
                node_name = node_output.node_name
                break

        # TODO: this is a hack to work with old legacy recipe data with workspaces, remove when legacy job types go
        job.recipe.input = old_recipe_input_dict

        definition = job.recipe.recipe_type_rev.get_definition()
        input_data = definition.generate_node_input_data(node_name, recipe_input_data, node_outputs)
        Job.objects.set_job_input_data_v6(job, input_data)
