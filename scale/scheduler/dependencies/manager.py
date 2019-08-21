"""Defines the class that manages gathering Scale dependency system statuses"""
from __future__ import unicode_literals

import logging
import os
import requests
import socket
from urlparse import urlparse

from django.db import connection
from django.db.utils import OperationalError
from django.utils.timezone import now
from rest_framework import status

from kombu import Connection

from messaging.manager import CommandMessageManager
from scale import settings as scale_settings
from scheduler.manager import scheduler_mgr
from util.broker import BrokerDetails
from util.exceptions import InvalidBrokerUrl
from util.parse import datetime_to_string, parse_datetime

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

        # NODES (if > 1/3 become unhealthy then go red?) if degraded
        self._all_statuses['nodes'] = self._generate_nodes_status()

    def generate_status_json(self, status_dict):
        """Generates the portion of the status JSON that describes the systems Scale depends on

        :param status_dict: The status JSON dict
        :type status_dict: dict
        """

        status_dict['last_updated'] = datetime_to_string(self._last_updated)
        status_dict['dependencies'] = self._all_statuses
        return status_dict

    def _generate_log_status(self):
        """Generates the logs status message (fluentd)

        :return: JSON describing the logs status
        :rtype: dict
        """

        status_dict =  {'OK': True, 'detail': {}, 'errors': [], 'warnings': []}
        if scale_settings.LOGGING_HEALTH_ADDRESS:
            status_dict['detail']['logging_health_address'] = scale_settings.LOGGING_HEALTH_ADDRESS
            try:
                response = requests.get(scale_settings.LOGGING_HEALTH_ADDRESS)
                if response.status_code != status.HTTP_200_OK:
                    status_dict['OK'] = False
                    status_dict['errors'].append({response.status_code: 'Logging health address returned %d'%response.status_code})
                else:
                    for plugin in response.json()['plugins']:
                        if plugin['type'] == 'elasticsearch':
                            if scale_settings.FLUENTD_BUFFER_WARN > 0 and plugin['buffer_queue_length'] > scale_settings.FLUENTD_BUFFER_WARN:
                                msg = 'Length of log buffer is too long: %d > %d' %(plugin['buffer_queue_length'], scale_settings.FLUENTD_BUFFER_WARN)
                                status_dict['warnings'].append({'LARGE_BUFFER': msg})
                            if scale_settings.FLUENTD_BUFFER_SIZE_WARN > 0 and plugin['buffer_total_queued_size'] > scale_settings.FLUENTD_BUFFER_SIZE_WARN:
                                msg = 'Size of log buffer is too large: %d > %d' %(plugin['buffer_total_queued_size'], scale_settings.FLUENTD_BUFFER_SIZE_WARN)
                                status_dict['warnings'].append({'LARGE_BUFFER_SIZE': msg})
            except Exception as ex:
                msg = 'Error with LOGGING_HEALTH_ADDRESS: %s' % unicode(ex)
                status_dict['OK'] = False
                status_dict['errors'].append({'UNKNOWN_ERROR': msg})
        else:
            status_dict['OK'] = False
            status_dict['errors'].append({'NO_LOGGING_HEALTH_DEFINED': 'No logging health URL defined'})
        if scale_settings.LOGGING_ADDRESS:
            status_dict['detail']['logging_address'] = scale_settings.LOGGING_ADDRESS
            try:
                s = socket.socket()
                o = urlparse(scale_settings.LOGGING_ADDRESS)
                s.connect((o.hostname, o.port))
            except Exception as ex:
                msg = 'Error with LOGGING_ADDRESS: %s' % unicode(ex)
<<<<<<< HEAD
                status_dict = {'OK': False, 'errors': [{'UNKNOWN_ERROR': msg}], 'warnings': []}
        else: 
            status_dict =  {'OK': False, 'errors': [{'NO_LOGGING_DEFINED': 'No logging URL defined'}], 'warnings': []}
=======
                status_dict['OK'] = False
                status_dict['errors'].append({'UNKNOWN_ERROR': msg})
        else:
            status_dict['OK'] = False
            status_dict['errors'].append({'NO_LOGGING_DEFINED': 'No logging address defined'})

>>>>>>> :hammer: More robust log checks; check buffer sizes and warn if too large
        return status_dict


    def _generate_elasticsearch_status(self):
        """Generates the elasticsearch status message

        :return: JSON describing the elasticsearch status
        :rtype: dict
        """
        
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
                    status_dict = {'OK': True}
                    status_dict['detail'] = elasticsearch.info()

        return status_dict

    def _generate_silo_status(self):
        """Generates the silo status message

        :return: JSON describing the silo status
        :rtype: dict
        """
        
        silo_url = os.getenv('SILO_URL')
        
        # Hit the silo url to make sure it's alive
        if not silo_url:
            status_dict = {'OK': False, 'errors': [{'NO_SILO_DEFINED': 'No silo URL defined in environment. SOS.'}], 'warnings': []}
        else:
            try:
                response = requests.head(silo_url)
                if response.status_code == status.HTTP_200_OK:
                    status_dict = {'OK': True, 'detail': {'url': silo_url}}
                else:
                    status_dict = {'OK': False, 'errors': [{response.status_code: 'Silo returned a status code of %s' % response.status_code}], 'warnings': []}
            except Exception as ex:
                msg = 'Error with SILO_URL: %s' % unicode(ex)
                status_dict = {'OK': False, 'errors': [{'UNKNOWN_ERROR': msg}], 'warnings': []}
                
        return status_dict

    def _generate_database_status(self):
        """Generates the database status message

        :return: JSON describing the database status
        :rtype: dict
        """
        try:
            connection.ensure_connection()
            status_dict = {'OK': True, 'detail': 'Database alive and well'}
        except Exception as ex:
            status_dict = {'OK': False, 'errors': [{'OPERATIONAL_ERROR': 'Database unavailable.'}], 'warnings': []}
        
        return status_dict
        
    def _generate_msg_queue_status(self):
        """Generates the Message Queue status message
        AMQP (rabbitmq)
        """
        
        status_dict = {'OK': False, 'errors': [], 'warnings': []}
        status_dict['broker_url'] = scale_settings.BROKER_URL
        status_dict['queue_name'] = scale_settings.QUEUE_NAME
        status_dict['num_message_handlers'] = scheduler_mgr.config.num_message_handlers
        try:
            broker_details = BrokerDetails.from_broker_url(scale_settings.BROKER_URL)
        except InvalidBrokerUrl:
            msg = 'Error parsing broker url'
            status_dict['errors'] = [{'INVALID_BROKER_URL': msg}]
        if broker_details.get_type() == 'amqp':
            try:
                with Connection(scale_settings.BROKER_URL) as conn:
                    conn.connect() # Exceptions may be raised upon connect
                    status_dict = {'OK': True, 'errors': [], 'warnings': []}
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
        elif broker_details.get_type() == 'sqs':
            status_dict['region_name'] = broker_details.get_address()
            try:
                CommandMessageManager().get_queue_size()
            except Exception as ex:
                logger.error('Unable to get queue size from sqs: %s' % unicode(ex))
                msg = 'Error connecting to SQS: Check Logs for details'
                status_dict = {'OK': False, 'errors': [{'SQS_ERROR': msg}], 'warnings': []}

        if status_dict['OK']:
            status_dict['queue_depth'] = CommandMessageManager().get_queue_size()
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
        from scheduler.node.manager import node_mgr
        node_status ={}
        node_mgr.generate_status_json(node_status)
        if 'nodes' in node_status and len(node_status['nodes']) > 0:
            node_status = node_status['nodes']
            third_nodes = len(node_status)*0.3
            
            offline_count = 0
            degraded_count = 0
            for node in node_status:
                if node['state']['name'] == 'OFFLINE':
                    offline_count += 1
                elif node['state']['name'] == 'DEGRADED':
                    degraded_count += 1
                    
            status_dict = {'OK': True, 'errors': [], 'warnings': [], 'detail': 'Enough nodes are online to function.'}
            if (offline_count + degraded_count) > third_nodes:
                status_dict['errors'].append({'NODES_ERRORED': 'Over a third of the nodes are offline or degraded.'})
                status_dict['OK'] = False
                status_dict['detail'] = 'Over a third of nodes are in an error state'

        else:
            status_dict = {'OK': False, 'errors': [{'NODES_OFFLINE': 'No nodes reported.'}], 'warnings': []}

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
