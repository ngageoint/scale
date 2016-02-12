"""Defines the class that manages the reconciliation background thread"""
from __future__ import unicode_literals

import logging
import math
import threading
import time

from django.utils.timezone import now


logger = logging.getLogger(__name__)


try:
    from mesos.interface import mesos_pb2
    logger.info('Successfully imported native Mesos bindings')
except ImportError:
    logger.info('No native Mesos bindings, falling back to stubs')
    import mesos_api.mesos_pb2 as mesos_pb2


class ReconciliationThread(object):
    """This class manages the reconciliation background thread for the scheduler"""

    THROTTLE = 60  # seconds

    def __init__(self, driver):
        """Constructor

        :param driver: The Mesos scheduler driver
        :type driver: :class:`mesos_api.mesos.SchedulerDriver`
        """

        self._driver = driver
        self._lock = threading.Lock()
        self._running = True
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
        :type task_ids: [str]
        """

        with self._lock:
            for task_id in task_ids:
                self._task_ids_to_reconcile.add(task_id)

    def remove_task_id(self, task_id):
        """Removes the task ID from the reconciliation set

        :param task_id: The task ID to remove
        :type task_id: str
        """

        with self._lock:
            self._task_ids_to_reconcile.discard(task_id)

    def run(self):
        """The main run loop of the thread
        """

        logger.info('Reconciliation thread started')

        while self._running:

            started = now()

            try:
                self._perform_reconciliation()
            except Exception:
                logger.exception('Critical error in reconciliation thread')

            ended = now()
            secs_passed = (ended - started).total_seconds()

            # If time takes less than a minute, throttle
            if secs_passed < ReconciliationThread.THROTTLE:
                # Delay until full throttle time reached
                delay = math.ceil(ReconciliationThread.THROTTLE - secs_passed)
                time.sleep(delay)

        logger.info('Reconciliation thread stopped')

    def shutdown(self):
        """Stops the thread from running and performs any needed clean up
        """

        logger.info('Shutting down reconciliation thread')
        self._running = False

    def _perform_reconciliation(self):
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
            # TODO: adding task.slave_id would be useful if possible
            tasks.append(task)
        self._driver.reconcileTasks(tasks)
