"""Defines the class that manages reconciling tasks"""
from __future__ import unicode_literals

import datetime
import logging
import threading

from django.utils.timezone import now
from mesos.interface import mesos_pb2

COUNT_WARNING_THRESHOLD = 1000  # If the total list count hits this threshold, log a warning
FULL_RECON_THRESHOLD = datetime.timedelta(minutes=2)

logger = logging.getLogger(__name__)


class ReconciliationManager(object):
    """This class manages tasks that need to be reconciled. This class is thread-safe."""

    def __init__(self):
        """Constructor
        """

        self._driver = None
        self._lock = threading.Lock()

        # Rookie tasks have just been added and have not sent a reconciliation request yet
        # After their first reconciliation request, they will move to self._tasks
        self._rookie_tasks = {}  # {Task ID: Task}
        self._tasks = {}  # {Task ID: Task}
        self._last_full_reconciliation = now()  # Last time all tasks were reconciled

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

    def add_tasks(self, tasks):
        """Adds a list of tasks that need to be reconciled

        :param tasks: The list of tasks to reconcile
        :type tasks: list
        """

        with self._lock:
            for task in tasks:
                if task.id not in self._tasks:
                    self._rookie_tasks[task.id] = task

    def perform_reconciliation(self):
        """Performs task reconciliation with the Mesos master
        """

        tasks_to_reconcile = {}
        with self._lock:
            when = now()
            # Reconcile all tasks if time threshold has been reached
            if when > self._last_full_reconciliation + FULL_RECON_THRESHOLD:
                self._last_full_reconciliation = when
                for task in self._tasks.values():
                    tasks_to_reconcile[task.id] = task
            # Always reconcile rookie tasks and move them to self._tasks
            # This enables tasks to be quickly reconciled the first time
            for task in self._rookie_tasks.values():
                tasks_to_reconcile[task.id] = task
                self._tasks[task.id] = task
            self._rookie_tasks = {}

        if not tasks_to_reconcile:
            return

        logger.info('Reconciling %d task(s)', len(tasks_to_reconcile))
        task_statuses = []
        for task in tasks_to_reconcile.values():
            task_status = mesos_pb2.TaskStatus()
            task_status.task_id.value = task.id
            task_status.state = mesos_pb2.TASK_LOST
            task_statuses.append(task_status)
        self._driver.reconcileTasks(task_statuses)

    def remove_task_id(self, task_id):
        """Removes the task ID from the reconciliation set

        :param task_id: The task ID to remove
        :type task_id: string
        """

        with self._lock:
            if task_id in self._rookie_tasks:
                del self._rookie_tasks[task_id]
            if task_id in self._tasks:
                del self._tasks[task_id]


recon_mgr = ReconciliationManager()
