"""Defines the class that manages the task handling background thread"""
from __future__ import unicode_literals

import logging
import math
import time

from django.db import DatabaseError
from django.utils.timezone import now
from mesos.interface import mesos_pb2

from job.execution.manager import running_job_mgr
from job.execution.tasks.cleanup_task import CLEANUP_TASK_ID_PREFIX
from job.execution.tasks.exe_task import JOB_TASK_ID_PREFIX
from job.models import JobExecution
from job.tasks.manager import task_mgr
from job.tasks.pull_task import PULL_TASK_ID_PREFIX
from scheduler.cleanup.manager import cleanup_mgr
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
            task_to_kill = task
            # Update the manager corresponding to the task's type so the manager can handle task failure
            if task.id.startswith(PULL_TASK_ID_PREFIX):
                node_mgr.handle_task_timeout(task)
            elif task.id.startswith(CLEANUP_TASK_ID_PREFIX):
                cleanup_mgr.handle_task_timeout(task)
            elif task.id.startswith(JOB_TASK_ID_PREFIX):
                job_exe_id = JobExecution.get_job_exe_id(task.id)
                running_job_exe = running_job_mgr.get_job_exe(job_exe_id)

                if running_job_exe:
                    task_to_kill = None
                    try:
                        task_to_kill = running_job_exe.execution_timed_out(task, when)
                    except DatabaseError:
                        logger.exception('Error failing timed out job execution %i', running_job_exe.id)

                    # Remove finished job execution
                    if running_job_exe.is_finished():
                        running_job_mgr.remove_job_exe(job_exe_id)
                        cleanup_mgr.add_job_execution(running_job_exe)

            if task_to_kill:
                pb_task_to_kill = mesos_pb2.TaskID()
                pb_task_to_kill.value = task_to_kill.id
                logger.info('Killing task %s', task_to_kill.id)
                self._driver.killTask(pb_task_to_kill)
