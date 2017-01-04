"""Defines the class that manages the task handling background thread"""
from __future__ import unicode_literals

import logging
import math
import time

from django.utils.timezone import now

from job.tasks.manager import task_mgr

from scheduler.recon.manager import recon_mgr
from scheduler.task.manager import task_update_mgr


logger = logging.getLogger(__name__)


class TaskHandlingThread(object):
    """This class manages the task handling background thread for the scheduler"""

    THROTTLE = 10  # seconds

    def __init__(self):
        """Constructor
        """

        self._running = True

    def run(self):
        """The main run loop of the thread
        """

        logger.info('Task handling thread started')

        while self._running:

            started = now()

            try:
                self._handle_tasks()
            except Exception:
                logger.exception('Critical error in task handling thread')

            ended = now()
            secs_passed = (ended - started).total_seconds()

            # If time takes less than threshold, throttle
            if secs_passed < TaskHandlingThread.THROTTLE:
                # Delay until full throttle time reached
                delay = math.ceil(TaskHandlingThread.THROTTLE - secs_passed)
                time.sleep(delay)

        logger.info('Task handling thread stopped')

    def shutdown(self):
        """Stops the thread from running and performs any needed clean up
        """

        logger.info('Shutting down task handling thread')
        self._running = False

    def _handle_tasks(self):
        """Handles any task operations that need to be performed
        """

        self._reconcile_tasks()

    def _reconcile_tasks(self):
        """Sends any tasks that need to be reconciled to the reconciliation manager
        """

        when = now()
        task_ids = []
        for task in task_mgr.get_tasks_to_reconcile(when):
            task_ids.append(task.id)
        recon_mgr.add_task_ids(task_ids)
