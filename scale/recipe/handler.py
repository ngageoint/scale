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
        self._jobs = {}  # {Job name: Job}

        for recipe_job in recipe_jobs:
            self._jobs[recipe_job.job_name] = recipe_job

    # TODO: add methods for getting jobs to set to PENDING/BLOCKED, and getting jobs to queue
