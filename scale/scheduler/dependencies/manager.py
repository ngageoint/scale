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

from messaging.backends.amqp import AMQPMessagingBackend
from messaging.manager import CommandMessageManager
from scale import settings as scale_settings
from scheduler.manager import scheduler_mgr
from util.broker import BrokerDetails
from util.exceptions import InvalidBrokerUrl
from util.parse import datetime_to_string, parse_datetime

logger = logging.getLogger(__name__)

# The status should be updated if its JSON is older than this threshold
DEPENDENCY_STATUS_FRESHNESS_THRESHOLD = 12.0  # seconds

class DependencyManager(object):
    """This class pulls the status for various systems Scale depends on. This class is thread-safe."""

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

        self._refresh_statuses()
        status_dict['last_updated'] = datetime_to_string(self._last_updated)
        status_dict['dependencies'] = self._all_statuses
        return status_dict
        
    def _refresh_statuses(self):
        # check if it's too early to update
        if (now() - self._last_updated) < DEPENDENCY_STATUS_FRESHNESS_THRESHOLD:
            return
        
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

    def _generate_log_status(self):
        """Generates the logs status message (fluentd)

        :return: JSON describing the logs status
        :rtype: dict
        """

        status_dict =  {'OK': True, 'detail': {}, 'errors': [], 'warnings': []}
        status_dict['detail']['msg'] = 'Logs are healthy'
        if scale_settings.LOGGING_HEALTH_ADDRESS:
            status_dict['detail']['logging_health_address'] = scale_settings.LOGGING_HEALTH_ADDRESS
            try:
                response = requests.get(scale_settings.LOGGING_HEALTH_ADDRESS)
                if response.status_code != status.HTTP_200_OK:
                    status_dict['OK'] = False
                    status_dict['errors'].append({response.status_code: 'Logging health address returned %d'%response.status_code})
                    status_dict['detail']['msg'] = '%s error getting logging health' % response.status_code
                else:
                    for plugin in response.json()['plugins']:
                        if plugin['type'] == 'elasticsearch':
                            if scale_settings.FLUENTD_BUFFER_WARN > 0 and plugin['buffer_queue_length'] > scale_settings.FLUENTD_BUFFER_WARN:
                                msg = 'Length of log buffer is too long: %d > %d' %(plugin['buffer_queue_length'], scale_settings.FLUENTD_BUFFER_WARN)
                                status_dict['warnings'].append({'LARGE_BUFFER': msg})
                                status_dict['detail']['msg'] = 'Logs are potentially backing up'
                            if scale_settings.FLUENTD_BUFFER_SIZE_WARN > 0 and plugin['buffer_total_queued_size'] > scale_settings.FLUENTD_BUFFER_SIZE_WARN:
                                msg = 'Size of log buffer is too large: %d > %d' %(plugin['buffer_queue_length'], scale_settings.FLUENTD_BUFFER_WARN)
                                status_dict['warnings'].append({'LARGE_BUFFER_SIZE': msg})
                                status_dict['detail']['msg'] = 'Logs are potentially backing up'
            except Exception as ex:
                msg = 'Error with LOGGING_HEALTH_ADDRESS: %s' % unicode(ex)
                status_dict['OK'] = False
                status_dict['errors'].append({'UNKNOWN_ERROR': msg})
                status_dict['detail']['msg'] = 'Error getting log health'
        else:
            status_dict['OK'] = False
            status_dict['errors'].append({'NO_LOGGING_HEALTH_DEFINED': 'No logging health URL defined'})
            status_dict['detail']['msg'] = 'LOGGING_HEALTH_ADDRESS is not defined'
        if scale_settings.LOGGING_ADDRESS:
            status_dict['detail']['logging_address'] = scale_settings.LOGGING_ADDRESS
            try:
                s = socket.socket()
                o = urlparse(scale_settings.LOGGING_ADDRESS)
                s.connect((o.hostname, o.port))
            except Exception as ex:
                msg = 'Error with LOGGING_ADDRESS: %s' % unicode(ex)
                status_dict['OK'] = False
                status_dict['errors'].append({'UNKNOWN_ERROR': msg})
                status_dict['detail']['msg'] = 'Error connecting to logging address'
        else:
            status_dict['OK'] = False
            status_dict['errors'].append({'NO_LOGGING_DEFINED': 'No logging address defined'})
            status_dict['detail']['msg'] = 'LOGGING_ADDRESS is not defined'

        return status_dict


    def _generate_elasticsearch_status(self):
        """Generates the elasticsearch status message

        :return: JSON describing the elasticsearch status
        :rtype: dict
        """
        
        status_dict = {'OK': False, 'detail': {}, 'errors': [], 'warnings': []}
        elasticsearch = scale_settings.ELASTICSEARCH
        status_dict['detail']['url'] = scale_settings.ELASTICSEARCH_URL
        status_dict['detail']['msg'] = ''
        if not elasticsearch:
            status_dict['errors'] = [{'UNKNOWN_ERROR': 'Elasticsearch object does not exist.'}]
            status_dict['detail']['msg'] = 'Elasticsearch object does not exist'
        else:
            if not elasticsearch.ping():
                status_dict['errors'] = [{'CLUSTER_ERROR': 'Elasticsearch cluster is unreachable.'}]
                status_dict['detail']['msg'] = 'Unable to connect to elasticsearch'
            else:
                health = elasticsearch.cluster.health()
                if health['status'] == 'red':
                    status_dict['errors'] =  [{'CLUSTER_RED': 'Elasticsearch cluster health is red. A primary shard is not allocated.'}]
                    status_dict['detail']['msg'] = 'One or more primary shards is not allocated to any node'
                elif health['status'] == 'yellow':
                    status_dict['errors'] =  [{'CLUSTER_YELLOW': 'Elasticsearch cluster health is yellow. A replica shard is not allocated.'}]
                    status_dict['detail']['msg'] = 'One or more replica shards is not allocated to a node.'
                elif health['status'] == 'green':
                    status_dict['OK'] = True
                    status_dict['detail']['info'] = elasticsearch.info()
                    status_dict['detail']['msg'] = 'Elasticsearch is healthy'

        return status_dict

    def _generate_silo_status(self):
        """Generates the silo status message

        :return: JSON describing the silo status
        :rtype: dict
        """
        
        status_dict = {'OK': False, 'detail': {}, 'errors': [], 'warnings': []}
        silo_url = os.getenv('SILO_URL')
        status_dict['detail']['url'] = silo_url
        
        # Hit the silo url to make sure it's alive
        if not silo_url:
            status_dict['errors'] = [{'NO_SILO_DEFINED': 'No silo URL defined in environment. SOS.'}]
        else:
            try:
                response = requests.head(silo_url)
                if response.status_code == status.HTTP_200_OK:
                    status_dict['OK'] = True
                    status_dict['detail']['msg'] = 'Silo is alive and connected'
                else:
                    status_dict['errors'] = [{response.status_code: 'Silo returned a status code of %s' % response.status_code}]
                    status_dict['detail']['msg'] = 'Unable to connect to Silo'
            except Exception as ex:
                msg = 'Error with SILO_URL: %s' % unicode(ex)
                status_dict['errors'] = [{'UNKNOWN_ERROR': msg}]
                status_dict['detail']['msg'] = 'Unknown error connecting to Silo'
                
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
            status_dict = {'OK': False, 'detail': {'msg': 'Unable to connect to database'}, 'errors': [{'OPERATIONAL_ERROR': 'Database unavailable.'}], 'warnings': []}
        
        return status_dict
        
    def _generate_msg_queue_status(self):
        """Generates the Message Queue status message
        AMQP (rabbitmq)
        """
        
        status_dict = {'OK': False, 'detail': {}, 'errors': [], 'warnings': []}
        status_dict['detail']['queue_name'] = scale_settings.QUEUE_NAME
        status_dict['detail']['num_message_handlers'] = scheduler_mgr.config.num_message_handlers
        status_dict['detail']['queue_depth'] = 0
        status_dict['detail']['region_name'] = ''
        status_dict['detail']['type'] = ''
        try:
            broker_details = BrokerDetails.from_broker_url(scale_settings.BROKER_URL)
        except InvalidBrokerUrl:
            msg = 'Error parsing broker url'
            status_dict['errors'] = [{'INVALID_BROKER_URL': msg}]
            return status_dict

        status_dict['detail']['type'] = broker_details.get_type()
        if broker_details.get_type() == 'amqp':
            try:
                CommandMessageManager().get_queue_size()
                status_dict['OK'] = True
            except Exception as ex:
                logger.error('Error connecting to RabbitMQ: %s' % unicode(ex))
                status_dict['OK'] = False
                msg = 'Error connecting to RabbitMQ: Check Logs for details'
                status_dict['errors'] = [{'RABBITMQ_ERROR': msg}]
        elif broker_details.get_type() == 'sqs':
            status_dict['detail']['region_name'] = broker_details.get_address()
            try:
                CommandMessageManager().get_queue_size()
                status_dict['OK'] = True
            except Exception as ex:
                logger.error('Unable to get queue size from sqs: %s' % unicode(ex))
                msg = 'Error connecting to SQS: Check Logs for details'
                status_dict['OK'] = False
                status_dict['errors'] = [{'SQS_ERROR': msg}]
        else:
            status_dict['OK'] = False
            status_dict['detail']['msg'] = 'Broker is an unsupported type: %s' % broker_details.get_type()

        if status_dict['OK']:
            status_dict['detail']['queue_depth'] = CommandMessageManager().get_queue_size()
            if scale_settings.MESSSAGE_QUEUE_DEPTH_WARN > 0 and status_dict['detail']['queue_depth'] > scale_settings.MESSSAGE_QUEUE_DEPTH_WARN:
                status_dict['warnings'].append({'LARGE_QUEUE': 'Message queue is very large'})
        return status_dict

    def _generate_idam_status(self):
        """Generates the IDAM (GEOAxIS) status message

        :return: JSON describing the IDAM status
        :rtype: dict
        """

        status_dict =  {'OK': False, 'detail': {}, 'errors': [], 'warnings': []}
        if not scale_settings.GEOAXIS_ENABLED:
            status_dict = {'OK': True, 'detail': {'geoaxis_enabled': False, 'msg': 'Geoaxis is not enabled'}, 'errors': [], 'warnings': []}
            return status_dict

        status_dict['detail']['geoaxis_host'] = scale_settings.SOCIAL_AUTH_GEOAXIS_HOST
        status_dict['detail']['geoaxis_enabled'] = True
        status_dict['detail']['backends'] = scale_settings.AUTHENTICATION_BACKENDS
        status_dict['detail']['geoaxis_authorization_url'] = GeoAxisOAuth2.AUTHORIZATION_URL
        status_dict['detail']['scale_vhost'] = scale_settings.SCALE_VHOST
        status_dict['detail']['msg'] = 'Geoaxis is enabled'
        try:
            vhosts = scale_settings.SCALE_VHOST
            hostname = vhosts.split(',')[0]
            url = 'https://%s/social-auth/login/geoaxis/?=' % hostname
            response = requests.get(url)
            if response.status_code == status.HTTP_200_OK:
                status_dict['OK'] = True
            response.raise_for_status()
        except Exception as ex:
            msg = 'Error accessing Geoaxis login url %s: %s' % (url, unicode(ex))
            status_dict['errors'].append({'GEOAXIS_ERROR': msg})
            status_dict['detail']['msg'] = msg

        return status_dict

    def _generate_nodes_status(self):
        """Generates the nodes status message

        :return: JSON describing the nodes status
        :rtype: dict
        """
        from scheduler.node.manager import node_mgr
        node_status ={}
        node_mgr.generate_status_json(node_status)
        if not node_status:
              status_dict = {'OK': False, 'errors': [{'NODES_OFFLINE': 'No nodes reported.'}], 'warnings': []}
        elif 'nodes' in node_status:
            node_status = node_status['nodes']
            third_nodes = len(node_status)*0.3
            
            offline_count = 0
            degraded_count = 0
            for node in node_status:
                if node['state']['name'] == 'OFFLINE':
                    offline_count += 1
                elif node['state']['name'] == 'DEGRADED':
                    degraded_count += 1
                    
            status_dict = {'OK': True, 'errors': [], 'warnings': [], 'detail': {'msg': 'Enough nodes are online to function.'}}
            if (offline_count + degraded_count) > third_nodes:
                status_dict['errors'].append({'NODES_ERRORED': 'Over a third of the nodes are offline or degraded.'})
                status_dict['OK'] = False
                status_dict['detail']['msg'] = 'Over a third of nodes are in an error state'
            if offline_count:
                status_dict['warnings'].append({'NODES_OFFLINE': '%d nodes are offline' % offline_count})
            if degraded_count:
                status_dict['warnings'].append({'NODES_DEGRADED': '%d nodes are degraded' % degraded_count})

        else:
            status_dict = {'OK': False, 'detail': {'msg': 'No nodes reported'}, 'errors': [{'NODES_OFFLINE': 'No nodes reported.'}], 'warnings': []}

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
