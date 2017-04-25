"""Defines the class that manages the scheduuler status background thread"""
from __future__ import unicode_literals

import logging
import math
import time

from django.utils.timezone import now

from job.execution.manager import job_exe_mgr
from scheduler.models import Scheduler
from scheduler.node.manager import node_mgr
from scheduler.sync.job_type_manager import job_type_mgr


logger = logging.getLogger(__name__)


class SchedulerStatusThread(object):
    """This class manages the scheduler status background thread for the scheduler"""

    THROTTLE = 5  # seconds
    WARNING_THRESHOLD = 0.5  # seconds

    def __init__(self):
        """Constructor
        """

        self._running = True

    def run(self):
        """The main run loop of the thread
        """

        logger.info('Scheduler status thread started')

        while self._running:

            started = now()

            try:
                status_dict = {}
                node_mgr.generate_status_json(status_dict)
                job_exe_mgr.generate_status_json(status_dict['nodes'], now())
                job_type_mgr.generate_status_json(status_dict)
                Scheduler.objects.all().update(status=status_dict)
            except Exception:
                logger.exception('Critical error in scheduler status thread')

            ended = now()
            secs_passed = (ended - started).total_seconds()

            msg = 'Scheduler status thread loop took %.3f seconds'
            if secs_passed > SchedulerStatusThread.WARNING_THRESHOLD:
                logger.warning(msg, secs_passed)
            else:
                logger.debug(msg, secs_passed)

            # If time takes less than threshold, throttle
            if secs_passed < SchedulerStatusThread.THROTTLE:
                # Delay until full throttle time reached
                delay = math.ceil(SchedulerStatusThread.THROTTLE - secs_passed)
                time.sleep(delay)

        logger.info('Scheduler status thread stopped')

    def shutdown(self):
        """Stops the thread from running and performs any needed clean up
        """

        logger.info('Shutting down scheduler status thread')
        self._running = False
