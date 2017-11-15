"""Defines the class that manages the task handling background thread"""
from __future__ import unicode_literals

import datetime
import logging

from django.utils.timezone import now
from mesos.interface import mesos_pb2

from job.execution.manager import job_exe_mgr
from job.execution.tasks.exe_task import JOB_TASK_ID_PREFIX
from job.tasks.manager import task_mgr
from scheduler.node.manager import node_mgr
from scheduler.recon.manager import recon_mgr
from scheduler.tasks.manager import system_task_mgr
from scheduler.threads.base_thread import BaseSchedulerThread


THROTTLE = datetime.timedelta(seconds=5)
WARN_THRESHOLD = datetime.timedelta(milliseconds=500)


logger = logging.getLogger(__name__)


class TaskHandlingThread(BaseSchedulerThread):
    """This class manages the task handling background thread for the scheduler"""

    def __init__(self, driver):
        """Constructor

        :param driver: The Mesos scheduler driver
        :type driver: :class:`mesos_api.mesos.SchedulerDriver`
        """

        super(TaskHandlingThread, self).__init__('Task handling', THROTTLE, WARN_THRESHOLD)
        self._driver = driver

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

    def _execute(self):
        """See :meth:`scheduler.threads.base_thread.BaseSchedulerThread._execute`
        """

        when = now()

        self._timeout_tasks(when)
        self._reconcile_tasks(when)
        self._kill_tasks()

    def _kill_tasks(self):
        """Sends kill messages for any tasks that need to be stopped
        """

        tasks_to_kill = system_task_mgr.get_tasks_to_kill()
        tasks_to_kill.extend(task_mgr.get_tasks_to_kill())

        for task in tasks_to_kill:
            # Send kill message for system task
            pb_task_to_kill = mesos_pb2.TaskID()
            pb_task_to_kill.value = task.id
            logger.info('Killing task %s', task.id)
            self._driver.killTask(pb_task_to_kill)

    def _reconcile_tasks(self, when):
        """Sends any tasks that need to be reconciled to the reconciliation manager

        :param when: The current time
        :type when: :class:`datetime.datetime`
        """

        recon_mgr.add_tasks(task_mgr.get_tasks_to_reconcile(when))

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
