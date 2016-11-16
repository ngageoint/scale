"""Defines a lock that logs activity for deadlock debugging"""
from __future__ import unicode_literals

import logging
import threading


logger = logging.getLogger(__name__)


class DebugLock(object):

    def __init__(self):
        self._lock = threading.Lock()

    def acquire(self):
        logger.info('Attempting to acquire...')
        self._lock.acquire()
        logger.info('Acquired')

    def release(self):
        self._lock.release()
        logger.info('Released')

    def __enter__(self):
        self.acquire()

    def __exit__(self, type, value, traceback):
        self.release()
