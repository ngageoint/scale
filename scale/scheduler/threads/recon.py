"""Defines the class that manages the reconciliation background thread"""
from __future__ import unicode_literals

import logging
import math
import threading
import time

from django.utils.timezone import now


from scheduler.recon.manager import recon_mgr

logger = logging.getLogger(__name__)


class ReconciliationThread(object):
    """This class manages the reconciliation background thread for the scheduler"""

    THROTTLE = 60  # seconds

    def __init__(self):
        """Constructor
        """

        self._lock = threading.Lock()
        self._running = True

    def run(self):
        """The main run loop of the thread
        """

        logger.info('Reconciliation thread started')

        while self._running:

            started = now()

            try:
                recon_mgr.perform_reconciliation()
            except Exception:
                logger.exception('Critical error in reconciliation thread')

            ended = now()
            secs_passed = (ended - started).total_seconds()

            # If time takes less than a minute, throttle
            if secs_passed < ReconciliationThread.THROTTLE:
                # Delay until full throttle time reached
                delay = math.ceil(ReconciliationThread.THROTTLE - secs_passed)
                time.sleep(delay)

        logger.info('Reconciliation thread stopped')

    def shutdown(self):
        """Stops the thread from running and performs any needed clean up
        """

        logger.info('Shutting down reconciliation thread')
        self._running = False
