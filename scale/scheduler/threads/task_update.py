"""Defines the class that manages the task update background thread"""
from __future__ import unicode_literals

import datetime

from scheduler.task.manager import task_update_mgr
from scheduler.threads.base_thread import BaseSchedulerThread


THROTTLE = datetime.timedelta(seconds=1)
WARN_THRESHOLD = datetime.timedelta(milliseconds=500)


class TaskUpdateThread(BaseSchedulerThread):
    """This class manages the task update background thread for the scheduler"""

    def __init__(self):
        """Constructor
        """

        super(TaskUpdateThread, self).__init__('Task update', THROTTLE, WARN_THRESHOLD)

    def _execute(self):
        """See :meth:`scheduler.threads.base_thread.BaseSchedulerThread._execute`
        """

        task_update_mgr.push_to_database()
