"""Defines the class that manages gathering Scale dependency system statuses"""
from __future__ import unicode_literals

import logging
import os
import requests

<<<<<<< HEAD
from django.db import connection
from django.db.utils import OperationalError
from django.utils.timezone import now
#from django.conf import settings
from rest_framework import status
=======
from django.utils.timezone import now
#from django.conf import settings
from scale import settings as scale_settings
from util.broker import BrokerDetails
>>>>>>> b9a7fb0fa03ebff4f230ed951041ea81ecca717f

from scale import settings as scale_settings
from util.broker import BrokerDetails

from kombu import Connection


from kombu import Connection
from messaging.manager import CommandMessageManager
from scheduler.models import Scheduler
from util.parse import parse_datetime

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

        status_dict['last_updated'] = self._last_updated
        status_dict['dependencies'] = self._all_statuses
        return status_dict

    def _generate_log_status(self):
        """Generates the logs status message (fluentd)

        :return: JSON describing the logs status
        :rtype: dict
        """
        status_dict = {}

        if scale_settings.LOGGING_HEALTH_ADDRESS:
            response = requests.head(scale_settings.LOGGING_HEALTH_ADDRESS)
            if response.status_code == status.HTTP_200_OK:
                status_dict['OK'] = True
                status_dict['detail'] = {'url': scale_settings.LOGGING_HEALTH_ADDRESS}
            else:
                status_dict =  {'OK': False, 'errors': [{response.status_code: 'Logging health address returned %d'%response.status_code}], 'warnings': []}
        elif scale_settings.LOGGING_ADDRESS:
            response = requests.head(scale_settings.LOGGING_ADDRESS)
            if response.status_code == status.HTTP_200_OK:
                status_dict['OK'] = True
                status_dict['detail'] = {'url': scale_settings.LOGGING_ADDRESS}
            else:
                status_dict =  {'OK': False, 'errors': [{response.status_code: 'Logging address returned %d'%response.status_code}], 'warnings': []}
        else: 
            status_dict =  {'OK': False, 'errors': [{'NO_LOGGING_DEFINED': 'No logging URL defined'}], 'warnings': []}

        return status_dict


    def _generate_elasticsearch_status(self):
        """Generates the elasticsearch status message

        :return: JSON describing the elasticsearch status
        :rtype: dict
        """
        status_dict = {}
        
        elasticsearch = scale_settings.ELASTICSEARCH
        if not elasticsearch:
            status_dict = {'OK': False, 'errors': [{'UNKNOWN_ERROR': 'Elasticsearch is unreachable. SOS.'}], 'warnings': []}
        else:
            if not elasticsearch.ping():
                status_dict = {'OK': False, 'errors': [{'CLUSTER_ERROR': 'Elasticsearch cluster is unreachable. SOS.'}], 'warnings': []}
            else:
                health = elasticsearch.cluster.health()
                if health['status'] == 'red':
                    status_dict = {'OK': False, 'errors': [{'CLUSTER_RED': 'Elasticsearch cluster health is red. SOS.'}], 'warnings': []}
                elif health['status'] == 'yellow':
                    status_dict = {'OK': False, 'errors': [{'CLUSTER_YELLOW': 'Elasticsearch cluster health is yellow. SOS.'}], 'warnings': []}
                elif health['status'] == 'green':
                    status_dict['OK'] = True
                    status_dict['detail'] = elasticsearch.info()

        return status_dict

    def _generate_silo_status(self):
        """Generates the silo status message

        :return: JSON describing the silo status
        :rtype: dict
        """
        
        status_dict = {}
        silo_url = os.getenv('SILO_URL')
        
        # Hit the silo url to make sure it's alive
        if not silo_url:
            status_dict = {'OK': False, 'errors': [{'NO_SILO_DEFINED': 'No silo URL defined in environment. SOS.'}], 'warnings': []}
        else:
            response = requests.head(silo_url)
            if response.status_code == status.HTTP_200_OK:
                status_dict['OK'] = True
                status_dict['detail'] = {'url': silo_url}
            else:
                status_dict = {'OK': False, 'errors': [{response.status_code: 'Silo returned a status code of %s' % response.status_code}], 'warnings': []}

        return status_dict

    def _generate_database_status(self):
        """Generates the database status message

        :return: JSON describing the database status
        :rtype: dict
        """
        try:
            connection.ensure_connection()
            status_dict = {'OK': True, 'detail': 'Database alive and well'}
        except OperationalError:
            status_dict = {'OK': False, 'errors': [{'OPERATIONAL_ERROR': 'Database unavailable.'}], 'warnings': []}
        
        return status_dict
        
    def _generate_msg_queue_status(self):
        """Generates the Message Queue status message
        AMQP (rabbitmq)
        """
        status_dict = {}
        import pdb; pdb.set_trace()
        # if type is amqp, then we know it's rabbit. Don't worry about SQS
        broker_details = BrokerDetails.from_broker_url(scale_settings.BROKER_URL)
        if broker_details.get_type() == 'amqp':
            try:
                with Connection(scale_settings.BROKER_URL) as conn:
                    conn.connect() # Exceptions may be raised upon connect
                    status_dict = {'OK': True, 'detail': {'url': scale_settings.BROKER_URL}}
            except Exception as ex:
                msg = 'Error connecting to RabbitMQ: %s' % unicode(ex)
                status_dict = {'OK': False, 'errors': [{'UNKNOWN_ERROR': msg}], 'warnings': []}
            # except ConnectionRefusedError as ex:
            #     msg = 'Unable to connect to RabbitMQ: Connection was refused: %s' % unicode(ex)
            #     status_dict = {'OK': False, 'errors': [{'CONNECTION_REFUSED': msg}], 'warnings':[]}
            # except AccessRefused as ex:
            #     msg = 'Unable to connect to RabbitMQ: Authentication error: %s' % unicode(ex)
            #     status_dict = {'OK': False, 'errors': [{'ACCESS_REFUSED': msg}], 'warnings': []}
            # except IOError as ex:
            #     msg = 'IO Error connecting to RabbitMQ: %s' % unicode(ex)
            #     status_dict = {'OK': False, 'errors': [{'IO_ERROR': msg}], 'warnings': []}
            # except BaseException as ex:
            #     msg = 'Unknown Error connecting to RabbitMQ: %s' % unicode(ex)
            #     status_dict = {'OK': False, 'errors': [{'UNKNOWN_ERROR': msg}], 'warnings': []}
            else:
                # Check the message queue depth
                backend = CommandMessageManager()._backend
                with Connection(scale_settings.BROKER_URL) as connection:
                    with connection.SimpleQueue(backend._queue_name) as simple_queue:
                        details = {'queue_depth': {backend._queue_name: simple_queue.qsize()}}

                status_dict = {'OK': True, 'details': details, 'errors': [], 'warnings': []}

        return status_dict

    def _generate_idam_status(self):
        """Generates the IDAM (GEOAxIS) status message

        :return: JSON describing the IDAM status
        :rtype: dict
        """
        status_dict = {}
        status_dict['OK'] = True
        status_dict['detail'] = 'some msg'
        return status_dict

    def _generate_nodes_status(self):
        """Generates the nodes status message

        :return: JSON describing the nodes status
        :rtype: dict
        """
        status_dict = {}

        status_dict['OK'] = True
        status_dict['detail'] = 'some msg'

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
