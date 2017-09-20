"""Defines the class that manages the messaging background thread"""
from __future__ import absolute_import
from __future__ import unicode_literals

import datetime
import logging

from job.execution.manager import job_exe_mgr
from messaging.manager import CommandMessageManager
from scheduler.threads.base_thread import BaseSchedulerThread


logger = logging.getLogger(__name__)


THROTTLE = datetime.timedelta(seconds=1)
WARN_THRESHOLD = datetime.timedelta(milliseconds=500)


class MessagingThread(BaseSchedulerThread):
    """This class manages the messaging background thread for the scheduler"""

    def __init__(self):
        """Constructor
        """

        super(MessagingThread, self).__init__('Messaging', THROTTLE, WARN_THRESHOLD)

        self._manager = CommandMessageManager()
        self._messages = []

    def _execute(self):
        """See :meth:`scheduler.threads.base_thread.BaseSchedulerThread._execute`
        """

        # If there are no previous messages to send, see if there are any new messages
        if not self._messages:
            self._messages = job_exe_mgr.get_messages()

        count = len(self._messages)
        if count:
            logger.info('Sending %d message(s)', count)
            self._manager.send_messages(self._messages)
            self._messages = []
