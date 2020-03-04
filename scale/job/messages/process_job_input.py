"""Defines a command message that processes the input for a job"""
from __future__ import unicode_literals

import logging

from django.db import transaction
from django.utils.timezone import now

from data.data.exceptions import InvalidData
from job.messages.cancel_jobs import create_cancel_jobs_messages
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
        # self.tries = 0

    def to_json(self):
        """See :meth:`messaging.messages.message.CommandMessage.to_json`
        """

        return {'job_id': self.job_id} #, 'tries': self.tries}

    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`
        """

        message = ProcessJobInput()
        message.job_id = json_dict['job_id']
        # message.tries = json_dict['tries']
        return message

    def execute(self):
        """See :meth:`messaging.messages.message.CommandMessage.execute`
        """

        from queue.messages.queued_jobs import create_queued_jobs_messages, QueuedJob
        try:
            job = Job.objects.get_job_with_interfaces(self.job_id)
        except Job.DoesNotExist:
            logger.exception('Failed to get job %d - job does not exist. Message will not re-run.', self.job_id)
            return True
        
        if job.status not in ['PENDING', 'BLOCKED']:
            logger.warning('Job %d input has already been processed. Message will not re-run', self.job_id)
            return True

        if not job.has_input():
            if not job.recipe:
                logger.error('Job %d has no input and is not in a recipe. Message will not re-run.', self.job_id)
                return True

            try:
                self._generate_input_data_from_recipe(job)
            except InvalidData:
                logger.exception('Recipe created invalid input data for job %d. Message will not re-run. Cancelling job that cannot be queued.', self.job_id)
                self.new_messages.extend(create_cancel_jobs_messages([self.job_id], now()))
                return True

        # Lock job model and process job's input data
        with transaction.atomic():
            job = Job.objects.get_locked_job(self.job_id)
            Job.objects.process_job_input(job)

        # Create message to queue the job
        if job.num_exes == 0:
            logger.info('Processed input for job %d, sending message to queue job', self.job_id)
            self.new_messages.extend(create_queued_jobs_messages([QueuedJob(job.id, 0)], requeue=False))

        return True

    def _generate_input_data_from_recipe(self, job):
        """Generates the job's input data from its recipe dependencies and validates and sets the input data on the job

        :param job: The job with related job_type_rev and recipe__recipe_type_rev models
        :type job: :class:`job.models.Job`

        :raises :class:`data.data.exceptions.InvalidData`: If the data is invalid
        """

        from recipe.models import RecipeNode
        node_name = None
        # Get job input from dependencies in the recipe
        recipe_input_data = job.recipe.get_input_data()
        nodes = RecipeNode.objects.get_recipe_jobs(job.recipe_id)
        node_outputs = RecipeNode.objects.get_recipe_node_outputs(job.recipe_id)
        for node_output in node_outputs.values():
            if node_output.node_type == 'job' and node_output.id == job.recipe_node.id:
                #get the node name of this job, for forked jobs it will be <base_definition_node_name>-file_id
                node_name = node_output.node_name
                break

        definition = job.recipe.get_definition()
        # need to add connections somehow inserted in definition for each individual file output from fork job
        if node_name:
            input_data = definition.generate_node_input_data(node_name, recipe_input_data, node_outputs, self._get_optional_outputs(nodes))
            if len(input_data) != 1:
                raise InvalidData('FORKING_ERROR', 'Expected one data object, received %d' % len(input_data))
            Job.objects.set_job_input_data_v6(job, input_data[0])

    def _get_optional_outputs(self, nodes):
        """get list of optional outputs within the recipe

        :param nodes: The nodes of the recipe
        :type nodes: :class:`dict`
        """

        optional_output_names = []

        for current_job in nodes.values():
            job_interface = current_job.get_job_interface()
            output_interface = job_interface.get_output_interface()
            for current_output in output_interface.parameters.values():
                if current_output.required == False:
                    optional_output_names.append(current_output.name)

        return optional_output_names