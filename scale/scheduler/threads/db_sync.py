"""Defines the class that manages the database sync background thread"""
from __future__ import unicode_literals

import datetime
import logging

from django.conf import settings
from mesos.interface import mesos_pb2

from job.execution.manager import job_exe_mgr
from scheduler.cleanup.manager import cleanup_mgr
from scheduler.node.manager import node_mgr
from scheduler.sync.job_type_manager import job_type_mgr
from scheduler.sync.scheduler_manager import scheduler_mgr
from scheduler.sync.workspace_manager import workspace_mgr
from scheduler.threads.base_thread import BaseSchedulerThread
from scheduler.vault.manager import secrets_mgr


THROTTLE = datetime.timedelta(seconds=10)
WARN_THRESHOLD = datetime.timedelta(seconds=5)


logger = logging.getLogger(__name__)


class DatabaseSyncThread(BaseSchedulerThread):
    """This class manages the database sync background thread for the scheduler"""

    def __init__(self, driver):
        """Constructor

        :param driver: The Mesos scheduler driver
        :type driver: :class:`mesos_api.mesos.SchedulerDriver`
        """

        super(DatabaseSyncThread, self).__init__('Database sync', THROTTLE, WARN_THRESHOLD)
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

        scheduler_mgr.sync_with_database()
        job_type_mgr.sync_with_database()
        workspace_mgr.sync_with_database()

        mesos_master = scheduler_mgr.mesos_address
        node_mgr.sync_with_database(mesos_master.hostname, mesos_master.port, scheduler_mgr.scheduler)
        cleanup_mgr.update_nodes(node_mgr.get_nodes())

        # Kill running tasks for canceled job executions
        for task_to_kill in job_exe_mgr.sync_with_database():
            pb_task_to_kill = mesos_pb2.TaskID()
            pb_task_to_kill.value = task_to_kill.id
            logger.info('Killing task %s', task_to_kill.id)
            self._driver.killTask(pb_task_to_kill)

        if settings.SECRETS_URL:
            secrets_mgr.sync_with_backend()
