"""Defines the class that manages gathering Scale dependency system statuses"""
from __future__ import unicode_literals

import logging

from django.conf import settings



logger = logging.getLogger(__name__)


class DependencyManager(object):
    """This class pulls the status for various systems Scale depends on. This class is thread-safe."""

    def __init__(self):
        """Constructor
        """

        self._all_statuses = {}

        # LOGS (fluentd) - check connectivity and msg backlog (undelivered messages)
        # ELASTICSEARCH - cluster health
        # SILO (SILO should report a fail if SILO cannot talk to it's configured container repos too)
        # DATABASE - simple connection possible
        # MSGBUS - RabbitMQ (amqp)or SQS
        # IDAM (GEOAxIS ... or whatever only if configured) get response from GEOAxIS
        # NODES (if > 1/3 become unhealthy then go red?) if degraded

    def generate_status_json(self, status_dict):
        """Generates the portion of the status JSON that describes the systems Scale depends on

        :param status_dict: The status JSON dict
        :type status_dict: dict
        """

        status_dict['dependencies'] = self._all_statuses
        return status_dict

    def _generate_msg_queue_status(self):
        """
        """

        return self._status_dict('OK', 'some msg')

    def _generate_

    def _status_dict(self, status, msg, **kwargs):
        """
        """

        s = {}
        s['status'] = status
        s['message'] = msg

        for k, v in kwargs.items():
            s[k] = v

        return s


dependency_mgr = DependencyManager()
