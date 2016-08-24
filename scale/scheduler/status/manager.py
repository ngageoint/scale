"""Defines the class that manages pushing task status updates to the database"""
from __future__ import unicode_literals

import logging
import threading

from job.models import TaskUpdate
from mesos_api.utils import create_task_update_model
from util.retry import retry_database_query


logger = logging.getLogger(__name__)


class StatusManager(object):
    """This class pushes task status updates to the database. This class is thread-safe."""

    COUNT_WARNING_THRESHOLD = 1000  # If the total list count hits this threshold, log a warning
    MAX_BATCH_SIZE = 500  # The maximum number of status update models to save to the database in a single batch

    def __init__(self):
        """Constructor
        """

        self._status_updates = []
        self._lock = threading.Lock()

    def add_status_update(self, status_update):
        """Adds the given status update to the manager so it can be pushed to the database

        :param status_update: The list of agent IDs to add
        :type status_update: :class:`mesos_pb2.TaskStatus`
        """

        if status_update:
            with self._lock:
                self._status_updates.append(status_update)

    def push_to_database(self):
        """Pushes the recent status updates to the database

        :returns: The total number of status updates pushed
        :rtype: int
        """

        with self._lock:
            status_updates = self._status_updates
            self._status_updates = []

        total_count = len(status_updates)
        if total_count >= StatusManager.COUNT_WARNING_THRESHOLD:
            logger.warning('%i status updates waiting to be pushed to database', total_count)

        models = []
        count = 0
        for status_update in status_updates:
            try:
                models.append(create_task_update_model(status_update))
                count += 1
            except:
                logger.exception('Failed to create database model for task status update')
            if count >= StatusManager.MAX_BATCH_SIZE:
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
