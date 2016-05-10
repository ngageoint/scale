"""Defines the class that manages the database sync background thread"""
from __future__ import unicode_literals

import logging
import math
import time

from django.db import DatabaseError
from django.utils.timezone import now

from job.models import JobExecution


logger = logging.getLogger(__name__)


try:
    from mesos.interface import mesos_pb2
    logger.info('Successfully imported native Mesos bindings')
except ImportError:
    logger.info('No native Mesos bindings, falling back to stubs')
    import mesos_api.mesos_pb2 as mesos_pb2


class DatabaseSyncThread(object):
    """This class manages the database sync background thread for the scheduler"""

    THROTTLE = 10  # seconds

    def __init__(self, driver, job_exe_manager, job_type_manager, node_manager, scheduler_manager, workspace_manager):
        """Constructor

        :param driver: The Mesos scheduler driver
        :type driver: :class:`mesos_api.mesos.SchedulerDriver`
        :param job_exe_manager: The running job execution manager
        :type job_exe_manager: :class:`job.execution.running.manager.RunningJobExecutionManager`
        :param job_type_manager: The job type manager
        :type job_type_manager: :class:`scheduler.sync.job_type_manager.JobTypeManager`
        :param node_manager: The node manager
        :type node_manager: :class:`scheduler.sync.node_manager.NodeManager`
        :param scheduler_manager: The scheduler manager
        :type scheduler_manager: :class:`scheduler.sync.scheduler_manager.SchedulerManager`
        :param workspace_manager: The workspace manager
        :type workspace_manager: :class:`scheduler.sync.workspace_manager.WorkspaceManager`
        """

        self._driver = driver
        self._job_exe_manager = job_exe_manager
        self._job_type_manager = job_type_manager
        self._node_manager = node_manager
        self._scheduler_manager = scheduler_manager
        self._workspace_manager = workspace_manager
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

        logger.info('Database sync thread started')

        while self._running:

            started = now()

            try:
                self._perform_sync()
            except Exception:
                logger.exception('Critical error in database sync thread')

            ended = now()
            secs_passed = (ended - started).total_seconds()

            # If time takes less than a minute, throttle
            if secs_passed < DatabaseSyncThread.THROTTLE:
                # Delay until full throttle time reached
                delay = math.ceil(DatabaseSyncThread.THROTTLE - secs_passed)
                time.sleep(delay)

        logger.info('Database sync thread stopped')

    def shutdown(self):
        """Stops the thread from running and performs any needed clean up
        """

        logger.info('Shutting down database sync thread')
        self._running = False

    def _perform_sync(self):
        """Performs the sync with the database
        """

        self._scheduler_manager.sync_with_database()
        self._job_type_manager.sync_with_database()
        self._workspace_manager.sync_with_database()

        scheduler = self._scheduler_manager.get_scheduler()
        self._node_manager.sync_with_database(scheduler.master_hostname, scheduler.master_port)

        self._sync_running_job_executions()

    def _sync_running_job_executions(self):
        """Syncs job executions that are currently running by handling any canceled or timed out executions
        """

        running_job_exes = {}
        for job_exe in self._job_exe_manager.get_all_job_exes():
            running_job_exes[job_exe.id] = job_exe

        right_now = now()

        for job_exe_model in JobExecution.objects.filter(id__in=running_job_exes.keys()).iterator():
            running_job_exe = running_job_exes[job_exe_model.id]
            task_to_kill = None

            if job_exe_model.status == 'CANCELED':
                task_to_kill = running_job_exe.execution_canceled()
            elif job_exe_model.is_timed_out(right_now):
                try:
                    task_to_kill = running_job_exe.execution_timed_out(right_now)
                except DatabaseError:
                    logger.exception('Error failing timed out job execution %i', running_job_exe.id)

            if task_to_kill:
                pb_task_to_kill = mesos_pb2.TaskID()
                pb_task_to_kill.value = task_to_kill.id
                logger.info('Killing task %s', task_to_kill.id)
                self._driver.killTask(pb_task_to_kill)

            if running_job_exe.is_finished():
                self._job_exe_manager.remove_job_exe(running_job_exe.id)
