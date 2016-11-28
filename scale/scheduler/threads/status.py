"""Defines the class that manages the status update background thread"""
from __future__ import unicode_literals

import logging
import math
import time

from django.utils.timezone import now

from scheduler.status.manager import task_update_mgr


logger = logging.getLogger(__name__)


class StatusUpdateThread(object):
    """This class manages the status update background thread for the scheduler"""

    THROTTLE = 1  # seconds

    def __init__(self):
        """Constructor
        """

        self._running = True

    def run(self):
        """The main run loop of the thread
        """

        logger.info('Status update thread started')

        while self._running:

            started = now()

            try:
                task_update_mgr.push_to_database()
            except Exception:
                logger.exception('Critical error in status update thread')

            ended = now()
            secs_passed = (ended - started).total_seconds()

            # If time takes less than threshold, throttle
            if secs_passed < StatusUpdateThread.THROTTLE:
                # Delay until full throttle time reached
                delay = math.ceil(StatusUpdateThread.THROTTLE - secs_passed)
                time.sleep(delay)

        logger.info('Status update thread stopped')

    def shutdown(self):
        """Stops the thread from running and performs any needed clean up
        """

        logger.info('Shutting down status update thread')
        self._running = False
