"""Defines the class that manages the scheduler status background thread"""
from __future__ import unicode_literals

import datetime

from django.utils.timezone import now

from job.execution.manager import job_exe_mgr
from scheduler.manager import scheduler_mgr
from scheduler.models import Scheduler
from scheduler.node.manager import node_mgr
from scheduler.resources.manager import resource_mgr
from scheduler.sync.job_type_manager import job_type_mgr
from scheduler.tasks.manager import system_task_mgr
from scheduler.threads.base_thread import BaseSchedulerThread
from util.parse import datetime_to_string


THROTTLE = datetime.timedelta(seconds=5)
WARN_THRESHOLD = datetime.timedelta(milliseconds=500)


class SchedulerStatusThread(BaseSchedulerThread):
    """This class manages the scheduler status background thread for the scheduler"""

    def __init__(self):
        """Constructor
        """

        super(SchedulerStatusThread, self).__init__('Scheduler status', THROTTLE, WARN_THRESHOLD)

    def _execute(self):
        """See :meth:`scheduler.threads.base_thread.BaseSchedulerThread._execute`
        """

        self._generate_status_json(now())

    def _generate_status_json(self, when):
        """Generates the scheduler status JSON

        :param when: The current time
        :type when: :class:`datetime.datetime`
        """

        status_dict = {'timestamp': datetime_to_string(when)}
        scheduler_mgr.generate_status_json(status_dict)
        system_task_mgr.generate_status_json(status_dict)
        node_mgr.generate_status_json(status_dict)
        resource_mgr.generate_status_json(status_dict)
        job_exe_mgr.generate_status_json(status_dict['nodes'], when)
        job_type_mgr.generate_status_json(status_dict)
        Scheduler.objects.all().update(status=status_dict)
