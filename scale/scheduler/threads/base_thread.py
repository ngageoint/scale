"""Defines the base class for scheduler background threads"""
from __future__ import unicode_literals

import logging
import math
import time
from abc import ABCMeta

from django.db.utils import InterfaceError
from django.utils.timezone import now

from scheduler.management.commands.scale_scheduler import GLOBAL_SHUTDOWN


logger = logging.getLogger(__name__)


class BaseSchedulerThread(object):
    """This is the abstract base class for scheduler background threads"""

    __metaclass__ = ABCMeta

    def __init__(self, name, throttle, warning_threshold):
        """Constructor

        :param name: The name of this thread
        :type name: string
        :param throttle: A loop of this thread should occur no more than once per this duration
        :type throttle: :class:`datetime.timedelta`
        :param warning_threshold: A warning is logged if loop execution exceeds this duration
        :type warning_threshold: :class:`datetime.timedelta`
        """

        self._name = name
        self._running = True
        self._throttle = throttle
        self._warning_threshold = warning_threshold

    def run(self):
        """The main run loop of the thread
        """

        logger.info('%s thread started', self._name)

        while self._running:

            started = now()

            try:
                self._execute()
            except InterfaceError as err:
                logger.exception('%s thread had a critical error interfacing with the database', self._name)
                if err.message == 'connection already closed':
                    msg = '%s thread has detected that the database connection is closed and cannot be recovered.'
                    msg += ' Shutting down the scheduler...'
                    logger.error(msg, self._name)
                    GLOBAL_SHUTDOWN()
            except Exception:
                logger.exception('%s thread had a critical error', self._name)

            duration = now() - started

            msg = '%s thread loop took %.3f seconds'
            if duration > self._warning_threshold:
                logger.warning(msg, self._name, duration.total_seconds())
            else:
                logger.debug(msg, self._name, duration.total_seconds())

            # If time takes less than threshold, throttle
            if duration < self._throttle:
                # Delay until full throttle time reached
                delay = math.ceil(self._throttle.total_seconds() - duration.total_seconds())
                time.sleep(delay)

        logger.info('%s thread stopped', self._name)

    def shutdown(self):
        """Stops the thread from running
        """

        logger.info('%s thread is shutting down', self._name)
        self._running = False

    def _execute(self):
        """Executes a single loop of this thread
        """

        raise NotImplementedError
