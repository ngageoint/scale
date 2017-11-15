"""Defines the class that manages the synchronization background thread"""
from __future__ import unicode_literals

import datetime
import logging

from django.conf import settings

from job.execution.manager import job_exe_mgr
from scheduler.cleanup.manager import cleanup_mgr
from scheduler.manager import scheduler_mgr
from scheduler.node.manager import node_mgr
from scheduler.resources.manager import resource_mgr
from scheduler.sync.job_type_manager import job_type_mgr
from scheduler.sync.workspace_manager import workspace_mgr
from scheduler.threads.base_thread import BaseSchedulerThread
from scheduler.vault.manager import secrets_mgr


THROTTLE = datetime.timedelta(seconds=10)
WARN_THRESHOLD = datetime.timedelta(seconds=5)


logger = logging.getLogger(__name__)


class SyncThread(BaseSchedulerThread):
    """This class manages the synchronization background thread for the scheduler"""

    def __init__(self, driver):
        """Constructor

        :param driver: The Mesos scheduler driver
        :type driver: :class:`mesos_api.mesos.SchedulerDriver`
        """

        super(SyncThread, self).__init__('Synchronization', THROTTLE, WARN_THRESHOLD)
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
        job_exe_mgr.sync_with_database()
        workspace_mgr.sync_with_database()

        node_mgr.sync_with_database(scheduler_mgr.config)
        cleanup_mgr.update_nodes(node_mgr.get_nodes())
        mesos_master = scheduler_mgr.mesos_address
        resource_mgr.sync_with_mesos(mesos_master.hostname, mesos_master.port)

        # Handle canceled job executions
        for finished_job_exe in job_exe_mgr.sync_with_database():
            cleanup_mgr.add_job_execution(finished_job_exe)

        if settings.SECRETS_URL:
            secrets_mgr.sync_with_backend()
