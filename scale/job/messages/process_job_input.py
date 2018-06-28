"""Defines a command message that processes the input for a job"""
from __future__ import unicode_literals

import logging

from django.db import transaction

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

    message = None
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
        from recipe.models import RecipeNode

        job = Job.objects.get_job_with_interfaces(self.job_id)

        if job.has_input():
            input_data = job.get_input_data()
        else:
            if not job.recipe:
                logger.error('Job %d has no input and is not in a recipe. Message will not re-run.', self.job_id)
                return True
            # Get job input from dependencies in the recipe
            recipe_input_data = job.recipe.get_input_data()
            node_outputs = RecipeNode.objects.get_recipe_node_outputs(job.recipe_id)
            # TODO: create recipe definition method that takes node_name, recipe input, and job outputs and creates job input data
            # TODO: validate job input data


        # TODO: In a transaction, lock job models and bulk create job input file models
        # TODO: In same transaction, create file ancestry link models
        # TODO: Update job input data and input summary fields (check for legacy vs Seed and save correct input data)



        # TODO: remove old code
        with transaction.atomic():
            # Retrieve locked job models
            job_models = Job.objects.get_locked_jobs(self._job_ids)

            # Process job inputs
            Job.objects.process_job_input(job_models)

        # Create messages to queue the jobs
        jobs_to_queue = []
        for job_model in job_models:
            if job_model.num_exes == 0:
                jobs_to_queue.append(QueuedJob(job_model.id, 0))
        if jobs_to_queue:
            logger.info('Processed job inputs, %d job(s) will be queued', len(jobs_to_queue))
            self.new_messages.extend(create_queued_jobs_messages(jobs_to_queue, requeue=False))

        return True
