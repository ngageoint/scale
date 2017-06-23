"""Defines the class that manages the reconciliation background thread"""
from __future__ import unicode_literals

import datetime

from scheduler.recon.manager import recon_mgr
from scheduler.threads.base_thread import BaseSchedulerThread


THROTTLE = datetime.timedelta(seconds=1)
WARN_THRESHOLD = datetime.timedelta(milliseconds=500)


class ReconciliationThread(BaseSchedulerThread):
    """This class manages the reconciliation background thread for the scheduler"""

    def __init__(self):
        """Constructor
        """

        super(ReconciliationThread, self).__init__('Reconciliation', THROTTLE, WARN_THRESHOLD)

    def _execute(self):
        """See :meth:`scheduler.threads.base_thread.BaseSchedulerThread._execute`
        """

        recon_mgr.perform_reconciliation()
