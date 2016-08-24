"""Defines the class that manages pushing task status updates to the database"""
from __future__ import unicode_literals

import logging
import threading


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
            model = None  # TODO: convert status update to a model
            models.append(model)
            count += 1
            if count >= StatusManager.MAX_BATCH_SIZE:
                # TODO: bulk create the models with retrying
                models = []
                count = 0
        if models:
            # TODO: bulk create the models with retrying
            pass
