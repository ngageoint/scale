"""Defines the class for handling recipes"""
from __future__ import unicode_literals


class RecipeHandler(object):
    """This class handles the logic for a recipe"""

    BLOCKING_STATUSES = ['BLOCKED', 'FAILED', 'CANCELED']

    def __init__(self, recipe, recipe_jobs):
        """Constructor

        :param recipe: The recipe model with related recipe_type and recipe_type_rev models
        :type recipe: :class:`recipe.models.Recipe`
        :param recipe_jobs: The list of recipe_job models with related job and job_type models
        :type recipe_jobs: [:class:`recipe.models.RecipeJob`]
        """

        self._recipe = recipe
        self._data = recipe.get_recipe_data()
        self._graph = recipe.get_recipe_definition().get_graph()
        self._jobs_by_id = {}  # {Job ID: Recipe Job}
        self._jobs_by_name = {}  # {Job Name: Recipe Job}

        for recipe_job in recipe_jobs:
            self._jobs_by_id[recipe_job.job_id] = recipe_job
            self._jobs_by_name[recipe_job.job_name] = recipe_job

    @property
    def recipe_id(self):
        """Returns the ID of the recipe for this handler

        :returns: The recipe ID
        :rtype: int
        """

        return self._recipe.id

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
