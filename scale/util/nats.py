"""Utility functions for accessing NATS"""
import logging
from collections import namedtuple

import pynats
from django.conf import settings

from util.exceptions import InvalidAWSCredentials, FileDoesNotExist

logger = logging.getLogger(__name__)


class NATSClient(object):
    """Manages automatically creating and destroying clients to NATS services."""

    def __init__(self, endpoint_url=None):
        """Constructor

        :param endpoint_url: The NATS endpoint URL the resource resides in.
        :type endpoint_url: string
        """

        self.endpoint_url = endpoint_url
        self._conn = None

    def __enter__(self):
        """Callback handles creating a new client for NATS access."""

        logger.debug('Setting up NATS client...')

        self._conn = pynats.Connection(url=self.endpoint_url)
        self._conn.connect()
        return self

    def __exit__(self, type, value, traceback):
        """Callback handles destroying an existing client."""
        if self._conn:
            self._conn.close()

    @property
    def connection(self):
        return self._conn

    def get_topic_by_name(self, nats_topic_name, callback):
        """Gets a NATS topic by the given name

        :param nats_topic_name: The unique name of the NATS topic
        :type nats_topic_name: string
        :return: Queue resource to perform queue operations
        """

        return self._conn.subscribe(nats_topic_name, callback)

