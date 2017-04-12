"""Defines the class that manages the task handling background thread"""
from __future__ import unicode_literals

import logging
import math
import time

from django.utils.timezone import now
from mesos.interface import mesos_pb2

from job.execution.manager import job_exe_mgr
from job.execution.tasks.exe_task import JOB_TASK_ID_PREFIX
from job.tasks.manager import task_mgr
from scheduler.node.manager import node_mgr
from scheduler.recon.manager import recon_mgr


logger = logging.getLogger(__name__)


class TaskHandlingThread(object):
    """This class manages the task handling background thread for the scheduler"""

    THROTTLE = 10  # seconds

    def __init__(self, driver):
        """Constructor

        :param driver: The Mesos scheduler driver
        :type driver: :class:`mesos_api.mesos.SchedulerDriver`
        """

        self._driver = driver
        self._running = True

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

        when = now()

        self._timeout_tasks(when)
        self._reconcile_tasks(when)

    def _reconcile_tasks(self, when):
        """Sends any tasks that need to be reconciled to the reconciliation manager

        :param when: The current time
        :type when: :class:`datetime.datetime`
        """

        task_ids = []
        for task in task_mgr.get_tasks_to_reconcile(when):
            task_ids.append(task.id)
        recon_mgr.add_task_ids(task_ids)

    def _timeout_tasks(self, when):
        """Handles any tasks that have exceeded their time out thresholds

        :param when: The current time
        :type when: :class:`datetime.datetime`
        """

        # Time out tasks that have exceeded thresholds
        for task in task_mgr.get_timeout_tasks(when):
            # Handle task timeout based on the type of the task
            if task.id.startswith(JOB_TASK_ID_PREFIX):
                # Job task, notify job execution manager
                job_exe_mgr.handle_task_timeout(task, when)
            else:
                # Not a job task, so must be a node task
                node_mgr.handle_task_timeout(task)

            # Send kill message for timed out task
            pb_task_to_kill = mesos_pb2.TaskID()
            pb_task_to_kill.value = task.id
            logger.info('Killing task %s', task.id)
            self._driver.killTask(pb_task_to_kill)
