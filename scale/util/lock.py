"""Defines a lock that logs activity for deadlock debugging"""
from __future__ import unicode_literals

import logging
import threading

logger = logging.getLogger(__name__)


class DebugLock(object):
    def __init__(self, class_name):
        self._class_name = class_name
        self._lock = threading.Lock()

    def acquire(self):
        logger.info('Attempting to acquire %s lock...', self._class_name)
        self._lock.acquire()
        logger.info('Acquired %s lock...', self._class_name)

    def release(self):
        self._lock.release()
        logger.info('Released %s lock...', self._class_name)

    def __enter__(self):
        self.acquire()

    def __exit__(self, type, value, traceback):
        self.release()
