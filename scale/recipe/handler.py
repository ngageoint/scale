"""Defines the class that handles recipe logic"""
from __future__ import unicode_literals


class RecipeHandler(object):
    """This class handles the logic for a recipe"""

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
        self._jobs_by_id = {}  # {Job ID: Recipe Job}
        self._jobs_by_name = {}  # {Job name: Recipe Job}

        for recipe_job in recipe_jobs:
            self._jobs_by_id[recipe_job.job.id] = recipe_job
            self._jobs_by_name[recipe_job.job_name] = recipe_job

    def get_blocked_jobs(self):
        """Returns the jobs within this recipe that should be updated to BLOCKED status

        :returns: The list of jobs that should be updated to BLOCKED
        :rtype: [:class:`job.models.Job`]
        """

        blocked_jobs = []
        jobs_by_name = {}

        for job_name in self._jobs_by_name:
            jobs_by_name[job_name] = self._jobs_by_name[job_name].job

        new_job_statuses = self._definition.get_unqueued_job_statuses(jobs_by_name)

        for job_id in new_job_statuses:
            new_status = new_job_statuses[job_id]
            job = self._jobs_by_id[job_id].job
            if new_status == 'BLOCKED' and job.status != new_status:
                blocked_jobs.append(job)

        return blocked_jobs

    def get_existing_jobs_to_queue(self):
        """Returns all of the existing recipe jobs that are ready to be queued

        :returns: The list of existing jobs that are ready to be queued along with their data
        :rtype: [(:class:`job.models.Job`, :class:`job.configuration.data.job_data.JobData`)]
        """

        unqueued_jobs = {}  # {Job name: Job}
        completed_jobs = {}  # {Job name: Job}

        for job_name in self._jobs_by_name:
            job = self._jobs_by_name[job_name].job
            if job.status == 'PENDING':
                unqueued_jobs[job_name] = job
            elif job.status == 'COMPLETED':
                completed_jobs[job_name] = job

        results = []
        jobs_to_queue = self._definition.get_next_jobs_to_queue(self._data, unqueued_jobs, completed_jobs)
        for job_id in jobs_to_queue:
            job_data = jobs_to_queue[job_id]
            job = self._jobs_by_id[job_id].job
            results.append((job, job_data))
        return results

    def get_pending_jobs(self):
        """Returns the jobs within this recipe that should be updated to PENDING status

        :returns: The list of jobs that should be updated to PENDING
        :rtype: [:class:`job.models.Job`]
        """

        pending_jobs = []
        jobs_by_name = {}

        for job_name in self._jobs_by_name:
            jobs_by_name[job_name] = self._jobs_by_name[job_name].job

        new_job_statuses = self._definition.get_unqueued_job_statuses(jobs_by_name)

        for job_id in new_job_statuses:
            new_status = new_job_statuses[job_id]
            job = self._jobs_by_id[job_id].job
            if new_status == 'PENDING' and job.status != new_status:
                pending_jobs.append(job)

        return pending_jobs
