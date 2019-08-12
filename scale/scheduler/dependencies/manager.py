"""Defines the class that manages gathering Scale dependency system statuses"""
from __future__ import unicode_literals

import logging

from django.utils.timezone import now
#from django.conf import settings
from scale import settings as scale_settings
from util.broker import BrokerDetails


from kombu import Connection


logger = logging.getLogger(__name__)


class DependencyManager(object):
    """This class pulls the status for various systems Scale depends on. This class is thread-safe."""

    # The status should be updated if its JSON is older than this threshold
    STATUS_FRESHNESS_THRESHOLD = 12.0  # seconds

    def __init__(self):
        """Constructor
        """

        self._all_statuses = {}
        self._last_updated = now()

        # LOGS (fluentd) - check connectivity and msg backlog (undelivered messages)
        self._all_statuses['logs'] = self._generate_log_status()

        # ELASTICSEARCH - cluster health
        self._all_statuses['elasticsearch'] = self._generate_elasticsearch_status()

        # SILO (SILO should report a fail if SILO cannot talk to it's configured container repos too)
        self._all_statuses['silo'] = self._generate_silo_status()

        # DATABASE - simple connection possible
        self._all_statuses['database'] = self._generate_database_status()

        # MSGBUS - RabbitMQ (amqp)or SQS
        self._all_statuses['msg_queue'] = self._generate_msg_queue_status()

        # IDAM (GEOAxIS ... or whatever only if configured) get response from GEOAxIS
        self._all_statuses['idam'] = self._generate_idam_status()

        ]# NODES (if > 1/3 become unhealthy then go red?) if degraded
        self._all_statuses['nodes'] = self._generate_nodes_status()

    def generate_status_json(self, status_dict):
        """Generates the portion of the status JSON that describes the systems Scale depends on

        :param status_dict: The status JSON dict
        :type status_dict: dict
        """

        status_dict['dependencies'] = self._all_statuses
        return status_dict

    def _generate_log_status(self):
        """Generates the logs status message (fluentd)

        :return: JSON describing the logs status
        :rtype: dict
        """
        status_dict = {}

        status_timestamp = parse_datetime(status_dict['timestamp'])
        if (now() - status_timestamp).total_seconds() > StatusView.STATUS_FRESHNESS_THRESHOLD:
            if scale_settings.LOGGING_HEALTH_ADDRESS:
                logging_check = 'timeout -s SIGKILL 5s curl %s; if [[ $? != 0 ]]; then exit %d; fi'
                logging_check = logging_check % (scale_settings.LOGGING_HEALTH_ADDRESS, HealthTask.BAD_LOGSTASH_CODE)

            status_dict('OK', 'some msg')

        return status_dict


    def _generate_elasticsearch_status(self):
        """Generates the elasticsearch status message

        :return: JSON describing the elasticsearch status
        :rtype: dict
        """
        status_dict = {}
        status_dict('OK', 'some msg')

        return status_dict

    def _generate_silo_status(self):
        """Generates the silo status message

        :return: JSON describing the silo status
        :rtype: dict
        """
        status_dict = {}
        status_dict('OK', 'some msg')

        return status_dict

    def _generate_database_status(self):
        """Generates the database status message

        :return: JSON describing the database status
        :rtype: dict
        """
        status_dict = {}
        status_dict('OK', 'some msg')

        return status_dict
    def _generate_msg_queue_status(self):
        """
        """
        status_dict = {}

        # if type is amqp, then we know it's rabbit. Don't worry about SQS
        broker_details = BrokerDetails.from_broker_url(scale_settings.BROKER_URL)
        if broker_details.get_type() == 'amqp':
            with Connection(scale_settings.BROKER_URL) as connection:


        status_dict('OK', 'some msg')

        return status_dict

    def _generate_idam_status(self):
        """Generates the IDAM (GEOAxIS) status message

        :return: JSON describing the IDAM status
        :rtype: dict
        """
        status_dict = {}
        status_dict('OK', 'some msg')

        return status_dict

    def _generate_nodes_status(self):
        """Generates the nodes status message

        :return: JSON describing the nodes status
        :rtype: dict
        """
        status_dict = {}
        status_dict('OK', 'some msg')

        return status_dict


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
