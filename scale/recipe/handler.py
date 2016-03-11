"""Defines the class that handles recipe logic"""
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
        self._definition = recipe.get_recipe_definition()
        self._nodes_by_id = {}  # {Job ID: Recipe Node}
        self._nodes_by_name = {}  # {Job name: Recipe Node}
        self._root_nodes = []  # Recipe nodes that have jobs with no dependencies

        for recipe_job in recipe_jobs:
            node = RecipeNode()
            node.recipe_job = recipe_job
            self._nodes_by_id[recipe_job.job.id] = node
            self._nodes_by_name[recipe_job.job_name] = node

        # TODO: refactor the recipe definition class so we don't have to grab its internals
        for job_name in self._definition._jobs_by_name:
            job_dict = self._definition._jobs_by_name[job_name]
            dependent_node = self._nodes_by_name[job_name]
            dependencies = job_dict['dependencies']
            if dependencies:
                for dependency_dict in job_dict['dependencies']:
                    parent_node = self._nodes_by_name[dependency_dict['name']]
                    parent_node.dependent_nodes.append(dependent_node)
                    dependent_node.parent_nodes.append(parent_node)
            else:
                self._root_nodes.append(dependent_node)

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

        blocked_jobs = []
        jobs_by_name = {}

        for job_name in self._nodes_by_name:
            jobs_by_name[job_name] = self._nodes_by_name[job_name].recipe_job.job

        new_job_statuses = self._definition.get_unqueued_job_statuses(jobs_by_name)

        for job_id in new_job_statuses:
            new_status = new_job_statuses[job_id]
            job = self._nodes_by_id[job_id].recipe_job.job
            if new_status == 'BLOCKED' and job.status != new_status:
                blocked_jobs.append(job)

        return blocked_jobs

    def get_dependent_job_ids(self, job_id):
        """Returns the IDs of the jobs that depend upon the job with the given ID

        :param job_id: The job ID
        :type job_id: int
        :returns: The set of job IDs that depend on the given job
        :rtype: {int}
        """

        node = self._nodes_by_id[job_id]
        job_ids = set()
        for dependent_node in node.dependent_nodes:
            dependent_id = dependent_node.recipe_job.job.id
            job_ids.add(dependent_id)
            job_ids.union(self.get_dependent_job_ids(dependent_id))
        return job_ids

    def get_existing_jobs_to_queue(self):
        """Returns all of the existing recipe jobs that are ready to be queued

        :returns: The list of existing jobs that are ready to be queued along with their data
        :rtype: [(:class:`job.models.Job`, :class:`job.configuration.data.job_data.JobData`)]
        """

        unqueued_jobs = {}  # {Job name: Job}
        completed_jobs = {}  # {Job name: Job}

        for job_name in self._nodes_by_name:
            job = self._nodes_by_name[job_name].recipe_job.job
            if job.status == 'PENDING':
                unqueued_jobs[job_name] = job
            elif job.status == 'COMPLETED':
                completed_jobs[job_name] = job

        results = []
        jobs_to_queue = self._definition.get_next_jobs_to_queue(self._data, unqueued_jobs, completed_jobs)
        for job_id in jobs_to_queue:
            job_data = jobs_to_queue[job_id]
            job = self._nodes_by_id[job_id].recipe_job.job
            results.append((job, job_data))
        return results

    def get_pending_jobs(self):
        """Returns the jobs within this recipe that should be updated to PENDING status

        :returns: The list of jobs that should be updated to PENDING
        :rtype: [:class:`job.models.Job`]
        """

        pending_jobs = []
        jobs_by_name = {}

        for job_name in self._nodes_by_name:
            jobs_by_name[job_name] = self._nodes_by_name[job_name].recipe_job.job

        new_job_statuses = self._definition.get_unqueued_job_statuses(jobs_by_name)

        for job_id in new_job_statuses:
            new_status = new_job_statuses[job_id]
            job = self._nodes_by_id[job_id].recipe_job.job
            if new_status == 'PENDING' and job.status != new_status:
                pending_jobs.append(job)

        return pending_jobs

    def is_completed(self):
        """Indicates whether this recipe has been completed

        :returns: True if this recipe has been completed, False otherwise
        :rtype: bool
        """

        for node in self._nodes_by_id.values():
            if node.recipe_job.job.status != 'COMPLETED':
                return False
        return True


class RecipeNode(object):
    """This class represents a node within a recipe. A node contains a job along with links to its parent jobs and
    dependent jobs."""

    def __init__(self):
        """Constructor
        """

        self.dependent_nodes = []
        self.parent_nodes = []
        self.recipe_job = None
