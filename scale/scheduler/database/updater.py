"""Defines the class that performs the Scale database update"""
from __future__ import unicode_literals

import logging

from django.db import connection, transaction

from batch.configuration.configuration import BatchConfiguration
from batch.models import Batch
from job.execution.tasks.json.results.task_results import TaskResults
from job.models import Job, JobExecution, JobExecutionEnd, JobExecutionOutput, TaskUpdate
from recipe.models import Recipe
from util.exceptions import TerminatedCommand
from util.parse import datetime_to_string


logger = logging.getLogger(__name__)


class DatabaseUpdater(object):
    """This class manages the Scale database update. This class is thread-safe."""

    def __init__(self):
        """Constructor
        """

        self._running = True

    def update(self):
        """Runs the database update
        """

    def stop(self):
        """Informs the database updater to stop running
        """

        logger.info('Scale database updater has been told to stop')
        self._running = False

