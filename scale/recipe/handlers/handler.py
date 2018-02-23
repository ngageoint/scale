"""Defines the class for handling recipes"""
from __future__ import unicode_literals

import logging

from job.configuration.data.exceptions import InvalidData
from job.models import Job


logger = logging.getLogger(__name__)


class RecipeHandler(object):
    """This class handles the logic for a recipe"""

    BLOCKING_STATUSES = ['BLOCKED', 'FAILED', 'CANCELED']

    def __init__(self, recipe, recipe_jobs):
        """Constructor

        :param recipe: The recipe model with related recipe_type_rev model
        :type recipe: :class:`recipe.models.Recipe`
        :param recipe_jobs: The list of recipe_job models with related job and job_type_rev models
        :type recipe_jobs: list
        """

        self.recipe = recipe
        self.recipe_jobs = []

        self._data = recipe.get_recipe_data()
        self._graph = recipe.get_recipe_definition().get_graph()
        self._jobs_by_id = {}  # {Job ID: Recipe Job}
        self._jobs_by_name = {}  # {Job Name: Recipe Job}

        self.add_jobs(recipe_jobs)

    def add_jobs(self, recipe_jobs):
        """Adds the given jobs to the recipe handler

        :param recipe_jobs: The list of recipe_job models with related job and job_type_rev models
        :type recipe_jobs: list
        """

        self.recipe_jobs.extend(recipe_jobs)

        for recipe_job in recipe_jobs:
            self._jobs_by_id[recipe_job.job_id] = recipe_job
            self._jobs_by_name[recipe_job.job_name] = recipe_job

    def get_blocked_jobs(self):
        """Returns the jobs within this recipe that should be updated to BLOCKED status

        :returns: The list of jobs that should be updated to BLOCKED
        :rtype: [:class:`job.models.Job`]
        """

        statuses = {}  # {Job name: status}
        jobs_to_blocked = []
        for job_name in self._graph.get_topological_order():
            job = self._jobs_by_name[job_name].job
            node = self._graph.get_node(job_name)
            if job.status in ['PENDING', 'BLOCKED']:
                should_be_blocked = False
                for parent_node in node.parents:
                    if statuses[parent_node.job_name] in RecipeHandler.BLOCKING_STATUSES:
                        should_be_blocked = True
                        break
                if should_be_blocked:
                    statuses[job_name] = 'BLOCKED'
                    if job.status != 'BLOCKED':
                        jobs_to_blocked.append(job)
                else:
                    statuses[job_name] = 'PENDING'
            else:
                statuses[job_name] = job.status

        return jobs_to_blocked

    def get_dependent_job_ids(self, job_id):
        """Returns the IDs of the jobs that depend upon the job with the given ID

        :param job_id: The job ID
        :type job_id: int
        :returns: The set of job IDs that depend on the given job
        :rtype: {int}
        """

        job_name = self._jobs_by_id[job_id].job_name
        node = self._graph.get_node(job_name)
        job_ids = set()
        for child_node in node.children:
            child_id = self._jobs_by_name[child_node.job_name].job_id
            job_ids.add(child_id)
            job_ids |= self.get_dependent_job_ids(child_id)  # Set union with the children of the child node
        return job_ids

    # TODO: remove this after no longer used, should be after entire REST API is migrated to messaging backend
    def get_existing_jobs_to_queue(self):
        """Returns all of the existing recipe jobs that are ready to be queued

        :returns: The list of existing jobs that are ready to be queued along with their data
        :rtype: [(:class:`job.models.Job`, :class:`job.configuration.data.job_data.JobData`)]
        """

        jobs_to_queue = []

        for job_name in self._graph.get_topological_order():
            job = self._jobs_by_name[job_name].job
            if job.status != 'PENDING':
                continue  # Only PENDING jobs are able to be queued
            node = self._graph.get_node(job_name)
            all_parents_completed = True
            parent_results = {}  # {Job name: Job results}
            for parent_node in node.parents:
                parent_job = self._jobs_by_name[parent_node.job_name].job
                if parent_job.status == 'COMPLETED':
                    parent_results[parent_node.job_name] = parent_job.get_job_results()
                else:
                    all_parents_completed = False
                    break
            if not all_parents_completed:
                continue  # Only queue jobs whose parents have completed

            job_data = node.create_job_data(job.get_job_interface(), self._data, parent_results)
            jobs_to_queue.append((job, job_data))

        return jobs_to_queue

    def get_jobs_ready_for_input(self):
        """Returns the models for each job in the recipe that is ready for its input. The new inputs have been set on
        each model, but not saved in the database.

        :returns: The list of jobs with their input
        :rtype: list
        """

        # Compile all of the job outputs in the recipe
        job_outputs = {}  # {Job name: Job results}
        for job_name in self._graph.get_topological_order():
            job = self._jobs_by_name[job_name].job
            if job.has_output():
                job_outputs[job_name] = job.get_job_results()

        # Find jobs without input yet that have parents ready to pass on outputs
        jobs_with_new_inputs = []
        for job_name in self._graph.get_topological_order():
            job = self._jobs_by_name[job_name].job
            node = self._graph.get_node(job_name)
            if job.has_input():
                continue  # Job already has its input
            all_parents_ready = True
            for parent_node in node.parents:
                parent_job = self._jobs_by_name[parent_node.job_name].job
                if not parent_job.is_ready_for_children():
                    all_parents_ready = False
                    break
            if not all_parents_ready:
                continue  # Job must have all parents ready in order to get its input

            try:
                job_input = node.create_job_data(job.get_job_interface(), self._data, job_outputs)
                job.set_input(job_input)
                jobs_with_new_inputs.append(job)
            except InvalidData:
                logger.exception('Invalid job input')

        return jobs_with_new_inputs

    def get_jobs_ready_for_first_queue(self):
        """Returns the models for each job in the recipe that is ready to be queued for the first time

        :returns: The list of jobs ready to be queued
        :rtype: list
        """

        jobs_to_queue = []

        for job_name in self._graph.get_topological_order():
            job = self._jobs_by_name[job_name].job
            if not job.has_been_queued() and job.can_be_queued():
                jobs_to_queue.append(job)

        return jobs_to_queue

    def get_jobs_to_create(self):
        """Returns a dict where recipe job_name maps to a list of job models that need to be created

        :returns: Dict where job_name maps to list of job models
        :rtype: dict
        """

        job_models = {}

        event_id = self.recipe.event_id
        root_recipe_id = self.recipe.root_superseded_recipe_id
        batch_id = self.recipe.batch_id
        for job_tuple in self.recipe.get_recipe_definition().get_jobs_to_create():
            job_name = job_tuple[0]
            job_type = job_tuple[1]
            if job_name in self._jobs_by_name:
                continue  # Skip jobs that are already created
            job = Job.objects.create_job(job_type, event_id, root_recipe_id=root_recipe_id, recipe_id=self.recipe.id,
                                         batch_id=batch_id)
            if self.recipe.batch and self.recipe.batch.priority is not None:
                job.priority = self.recipe.batch.priority
            job_models[job_name] = [job]

        return job_models

    def get_pending_jobs(self):
        """Returns the jobs within this recipe that should be updated to PENDING status

        :returns: The list of jobs that should be updated to PENDING
        :rtype: [:class:`job.models.Job`]
        """

        statuses = {}  # {Job name: status}
        jobs_to_pending = []
        for job_name in self._graph.get_topological_order():
            job = self._jobs_by_name[job_name].job
            node = self._graph.get_node(job_name)
            if job.status in ['PENDING', 'BLOCKED']:
                should_be_blocked = False
                for parent_node in node.parents:
                    if statuses[parent_node.job_name] in RecipeHandler.BLOCKING_STATUSES:
                        should_be_blocked = True
                        break
                if should_be_blocked:
                    statuses[job_name] = 'BLOCKED'
                else:
                    statuses[job_name] = 'PENDING'
                    if job.status != 'PENDING':
                        jobs_to_pending.append(job)
            else:
                statuses[job_name] = job.status

        return jobs_to_pending

    def is_completed(self):
        """Indicates whether this recipe has been completed

        :returns: True if this recipe has been completed, False otherwise
        :rtype: bool
        """

        for recipe_job in self._jobs_by_name.values():
            if recipe_job.job.status != 'COMPLETED':
                return False
        return True
