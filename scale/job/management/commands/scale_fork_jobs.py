"""Defines the command line method for running the Scale clock process"""
from __future__ import unicode_literals

import logging
import os
import signal
import sys

from django.core.management.base import BaseCommand

from data.data.value import FileValue
from error.exceptions import get_error_by_exception
from job.messages.create_jobs import RecipeJob
from job.models import Job
from recipe.instance.node import JobNodeInstance
from recipe.models import Recipe

logger = logging.getLogger(__name__)

GENERAL_FAIL_EXIT_CODE = 1
MISSING_JOB_EXIT_CODE = 10
MISSING_RECIPE_EXIT_CODE = 11
MISSING_JOB_DATA = 12
MISSING_PARAMETER = 13
NO_FILES = 20
NO_CHILDREN = 30
BAD_CHILD = 31

class Command(BaseCommand):
    """Command that executes the Scale clock
    """

    help = 'Used in a recipe to take a list of files from the input data and fork off a job in the recipe for each file'

    def __init__(self):
        """Constructor
        """
        super(Command, self).__init__()
        self.running = False
        self.fork_job = None
        self.recipe = None

    def handle(self, *args, **options):
        """See :meth:`django.core.management.base.BaseCommand.handle`.

        This method starts the Scale fork job.
        """
        self.running = True

        # Register a listener to handle clean shutdowns
        signal.signal(signal.SIGTERM, self._onsigterm)

        logger.info('Command starting: scale_fork_jobs')
        while self.running:
            try:
                if not self.fork_job:
                    self._init_job_fork()

                if not self.fork_job:
                    logger.info("Unable to get fork job")
                    sys.exit(MISSING_JOB_EXIT_CODE)

                if not self.recipe:
                    logger.info("Unable to get fork recipe")
                    sys.exit(MISSING_RECIPE_EXIT_CODE)

                data = self.fork_job.get_input_data()
                if not data:
                    logger.info("Unable to get data for fork job")
                    sys.exit(MISSING_JOB_DATA)

                if 'FORK_FILES' not in data.values:
                    logger.info("Fork job is missing 'FORK_FILES' parameter")
                    sys.exit(MISSING_PARAMETER)

                files = data.values['FORK_FILES']
                if not isinstance(files, FileValue):
                    logger.info("'FORK_FILES' parameter is the wrong type")
                    sys.exit(MISSING_PARAMETER)

                if len(files.file_ids) == 0:
                    logger.info("No files passed to fork job")
                    sys.exit(NO_FILES)

                for id in files.file_ids:
                    logger.debug("Adding forked job for file id %d:" % id)
                    #self.recipe.add_job_node

                recipe_instance = Recipe.objects.get_recipe_instance(recipe_id=self.recipe.id)
                recipe_model = recipe_instance.recipe_model

                fork_node = recipe_instance.get_job_node(job_id=self.fork_job.id)
                if not fork_node.children:
                    logger.warning("No children for fork job")
                    sys.exit(NO_CHILDREN)

                definition = self.recipe.get_definition()

                for child_name, child_node in fork_node.children.items():
                    # TODO: Also allow recipe nodes later? conditions?
                    if not isinstance(child_node, JobNodeInstance):
                        logger.error("%s is a child node of a fork job but is not a job node")
                        sys.exit(BAD_CHILD)
                    for id in files.file_ids:
                        logger.debug("Adding forked job for file id %d:" % id)
                        node_def = child_node.definition
                        name = child_name + '_' + id
                        definition.add_job_node(name, node_def.job_type_name, node_def.job_type_version, node_def.revision_num)
                        definition.add_dep
                        job = RecipeJob(node_def.job_type_name, node_def.job_type_version, node_def.revision_num,
                                        child_name + id, False)
                        recipe_jobs.append(job)

                        # write our own version of _generate_input_data_from_recipe or refactor to share some code
                        # we need to update the connections in the definition for n forked jobs without saving the definition back
                        # to the database. Once the definition is bastardized we can run _generate_input_data_from_recipe
                        # generally same as it is currently and have our forked outputs passed into each job node

                # get child of forked job (likely join job) if it exists and make it depend on all forked jobs




            except Exception as ex:
                exit_code = GENERAL_FAIL_EXIT_CODE
                err = get_error_by_exception(ex.__class__.__name__)
                if err:
                    err.log()
                    exit_code = err.exit_code
                logger.exception('Fork Job %d encountered an error: %s')
                sys.exit(exit_code)

        logger.info('Command completed: scale_fork_jobs')

        sys.exit(0)

    def _init_job_fork(self):
        """Initializes the job fork process by determining which job execution this process is
        """
        logger.info('Initializing job fork')
        job_id = os.getenv('SCALE_JOB_ID')
        try:
            fork_job = Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            logger.exception('Failed to get job %d - job does not exist.' % job_id)
            return

        self.fork_job = fork_job
        self.recipe = fork_job.recipe

    def _onsigterm(self, signum, _frame):
        """See signal callback registration: :py:func:`signal.signal`.

        This callback performs a clean shutdown when a TERM signal is received.
        """
        logger.info('Job Fork job terminated due to signal: %i', signum)
        self.running = False
