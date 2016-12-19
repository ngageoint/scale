"""Defines the class that manages pushing task status updates to the database"""
from __future__ import unicode_literals

import logging
import threading

from job.models import TaskUpdate
from util.retry import retry_database_query


logger = logging.getLogger(__name__)


class TaskUpdateManager(object):
    """This class pushes task status updates to the database. This class is thread-safe."""

    COUNT_WARNING_THRESHOLD = 1000  # If the total list count hits this threshold, log a warning
    MAX_BATCH_SIZE = 500  # The maximum number of status update models to save to the database in a single batch

    def __init__(self):
        """Constructor
        """

        self._task_updates = []
        self._lock = threading.Lock()

    def add_task_update(self, task_update):
        """Adds the given task update to the manager so it can be pushed to the database

        :param task_update: The list of agent IDs to add
        :type task_update: :class:`job.models.TaskUpdate`
        """

        if task_update:
            with self._lock:
                self._task_updates.append(task_update)

    def push_to_database(self):
        """Pushes the recent status updates to the database

        :returns: The total number of status updates pushed
        :rtype: int
        """

        with self._lock:
            task_updates = self._task_updates
            self._task_updates = []

        total_count = len(task_updates)
        if total_count >= TaskUpdateManager.COUNT_WARNING_THRESHOLD:
            logger.warning('%i task updates waiting to be pushed to database', total_count)

        models = []
        count = 0
        for task_update in task_updates:
            # TODO: currently only save job task updates, once job_exe_id field in TaskUpdate model allows nulls then
            # save all models to database
            if task_update.job_exe_id:
                models.append(task_update)
                count += 1
            if count >= TaskUpdateManager.MAX_BATCH_SIZE:
                self._bulk_save(models)
                models = []
                count = 0
        if models:
            self._bulk_save(models)

    @retry_database_query
    def _bulk_save(self, models):
        """Performs a bulk save of the given task update models

        :param models: The list of task update models
        :type models: [:class:`job.models.TaskUpdate`]
        """

        TaskUpdate.objects.bulk_create(models)


task_update_mgr = TaskUpdateManager()
