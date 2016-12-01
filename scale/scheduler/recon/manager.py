"""Defines the class that manages pushing task status updates to the database"""
from __future__ import unicode_literals

import logging
import threading

from mesos.interface import mesos_pb2


logger = logging.getLogger(__name__)


class ReconciliationManager(object):
    """This class manages tasks that needs to be reconciled with Mesos. This class is thread-safe."""

    COUNT_WARNING_THRESHOLD = 1000  # If the total list count hits this threshold, log a warning

    def __init__(self):
        """Constructor
        """

        self._lock = threading.Lock()
        self._task_ids_to_reconcile = set()

    @property
    def driver(self):
        """Returns the driver

        :returns: The driver
        :rtype: :class:`mesos_api.mesos.SchedulerDriver`
        """

        return self._driver

    @driver.setter
    def driver(self, value):
        """Sets the driver

        :param value: The driver
        :type value: :class:`mesos_api.mesos.SchedulerDriver`
        """

        self._driver = value

    def add_task_ids(self, task_ids):
        """Adds a list of task IDs that need to be reconciled

        :param task_ids: The list of task IDs to reconcile
        :type task_ids: [string]
        """

        with self._lock:
            for task_id in task_ids:
                self._task_ids_to_reconcile.add(task_id)

    def perform_reconciliation(self):
        """Performs task reconciliation with the Mesos master
        """

        task_ids_to_reconcile = []
        with self._lock:
            for task_id in self._task_ids_to_reconcile:
                task_ids_to_reconcile.append(task_id)

        if not task_ids_to_reconcile:
            return

        logger.info('Asking Mesos to reconcile %i task(s)', len(task_ids_to_reconcile))
        tasks = []
        for task_id in task_ids_to_reconcile:
            task = mesos_pb2.TaskStatus()
            task.task_id.value = task_id
            task.state = mesos_pb2.TASK_LOST
            tasks.append(task)
        self._driver.reconcileTasks(tasks)

    def remove_task_id(self, task_id):
        """Removes the task ID from the reconciliation set

        :param task_id: The task ID to remove
        :type task_id: string
        """

        with self._lock:
            self._task_ids_to_reconcile.discard(task_id)


recon_mgr = ReconciliationManager()
