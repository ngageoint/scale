from __future__ import unicode_literals

import django
import django_geoaxis
from django.db.utils import OperationalError
from django.test import TestCase
from kombu.exceptions import HttpError
from mock import patch, Mock

from messaging.backends.amqp import AMQPMessagingBackend
from messaging.backends.factory import add_message_backend
from scheduler.dependencies.manager import dependency_mgr
from scheduler.manager import scheduler_mgr
from scheduler.node.agent import Agent

def mock_response_head(*args, **kwargs):
    class MockResponse:
        def __init__(self, status_code):
            self.status_code = status_code
        
    # Test silo URL
    if args[0] == 'http://www.silo.com/':
        return MockResponse(200)
    # Test logging URL
    elif args[0] == 'http://www.logging.com/health':
        return MockResponse(200)
    elif args[0] == 'http://scale.io/social-auth/login/geoaxis/?=':
        return MockResponse(200)
    elif args[0] == 'http://unauthorized/social-auth/login/geoaxis/?=':
        return MockResponse(401)
    elif args[0] == 'http://host-offline/social-auth/login/geoaxis/?=':
        return MockResponse(503)
    
    return MockResponse(404)
    
def mock_response_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code, error=None):
            self.json_data = json_data
            self.status_code = status_code
            self.error = error
        def json(self):
            return self.json_data
        def raise_for_status(self):
            if self.error:
                raise self.error
    # Test silo URL
    if args[0] == 'http://www.silo.com/':
        return MockResponse({'key': 'value'}, 200)
    # Test logging URL
    elif args[0] == 'http://www.logging.com/health':
        return MockResponse({'plugins': [{'type':'elasticsearch', 'buffer_queue_length': 0, 'buffer_total_queued_size': 0}]}, 200)
    elif args[0] == 'http://localhost':
        return MockResponse({'plugins': [{'type':'elasticsearch', 'buffer_queue_length': 20, 'buffer_total_queued_size': 100000000000}]}, 200)
    elif args[0] == 'https://scale.io/social-auth/login/geoaxis/?=':
        return MockResponse({}, 200)
    elif args[0] == 'https://unauthorized/social-auth/login/geoaxis/?=':
        return MockResponse({}, 401, HttpError('Unauthorized'))
    elif args[0] == 'https://host-offline/social-auth/login/geoaxis/?=':
        return MockResponse({}, 503, HttpError('Service Unavailable'))
    
    return MockResponse({}, 404, HttpError('File not found'))


class TestDependenciesManager(TestCase):

    def setUp(self):
        django.setup()
        self.maxDiff = None
        add_message_backend(AMQPMessagingBackend)
        
        
        from scheduler.models import Scheduler
        Scheduler.objects.create(id=1)
        
        scheduler_mgr.config.is_paused = False
        self.agent_1 = Agent('agent_1', 'host_1')
        self.agent_2 = Agent('agent_2', 'host_2')
        self.agent_3 = Agent('agent_3', 'host_3')
        self.agent_4 = Agent('agent_4', 'host_4')
        self.agent_5 = Agent('agent_5', 'host_5')
        self.agent_6 = Agent('agent_6', 'host_6')
        self.agent_7 = Agent('agent_7', 'host_7')
        self.agent_8 = Agent('agent_8', 'host_8')
        self.agent_9 = Agent('agent_9', 'host_9')
        self.agent_10 = Agent('agent_10', 'host_10')

    def test_generate_log_status_none(self):
        """Tests the _generate_log_status method without logs set"""
 
        logs = dependency_mgr._generate_log_status()
        self.assertIsNotNone(logs)
        self.assertDictEqual(logs, {'OK': False, 'detail': {'msg': 'LOGGING_ADDRESS is not defined'}, 'errors': [{'NO_LOGGING_HEALTH_DEFINED': 'No logging health URL defined'}, {'NO_LOGGING_DEFINED': 'No logging address defined'}], 'warnings': []})   

    @patch('scale.settings.LOGGING_ADDRESS', 'tcp://localhost:1234')
    @patch('scale.settings.LOGGING_HEALTH_ADDRESS', 'localhost')
    def test_generate_log_status_bad(self):
        """Tests the _generate_log_status method with invalid settings"""
 
        logs = dependency_mgr._generate_log_status()
        self.assertIsNotNone(logs)
        self.assertEqual(logs['OK'], False)
        self.assertEqual(len(logs['errors']), 2)

    @patch('scale.settings.LOGGING_ADDRESS', 'tcp://localhost:1234')
    @patch('scale.settings.LOGGING_HEALTH_ADDRESS', 'http://www.logging.com/health')
    @patch('scale.settings.FLUENTD_BUFFER_WARN', 10)
    @patch('scale.settings.FLUENTD_BUFFER_SIZE_WARN', 100000000)
    @patch('socket.socket.connect')
    @patch('requests.get', side_effect=mock_response_get)
    def test_generate_log_status_good(self, mock_requests, connect):
        """Tests the _generate_log_status method with good settings"""
 
        logs = dependency_mgr._generate_log_status()
        self.assertIsNotNone(logs)
        self.assertDictEqual(logs, {'OK': True, 'detail': {'msg': 'Logs are healthy', 'logging_address': 'tcp://localhost:1234', 'logging_health_address': 'http://www.logging.com/health'}, 'errors': [], 'warnings': []}) 

    @patch('scale.settings.LOGGING_ADDRESS', 'tcp://localhost:1234')
    @patch('scale.settings.LOGGING_HEALTH_ADDRESS', 'http://localhost')
    @patch('scale.settings.FLUENTD_BUFFER_WARN', 10)
    @patch('scale.settings.FLUENTD_BUFFER_SIZE_WARN', 100000000)
    @patch('socket.socket.connect')
    @patch('requests.get', side_effect=mock_response_get)
    def test_generate_log_status_warn(self, mock_requests, connect):
        """Tests the _generate_log_status method with good settings and large queues"""
 
        logs = dependency_mgr._generate_log_status()
        self.assertIsNotNone(logs)
        msg = 'Length of log buffer is too long: 20 > 10'
        warnings = [{'LARGE_BUFFER': msg}]
        msg = 'Size of log buffer is too large: 100000000000 > 100000000'
        warnings.append({'LARGE_BUFFER_SIZE': msg})
        self.assertDictEqual(logs, {'OK': True, 'detail': { 'msg': 'Logs are potentially backing up', 
                                                            'logging_address': 'tcp://localhost:1234', 'logging_health_address': 
                                                            'http://localhost'}, 'errors': [], 'warnings': warnings}) 
     
    def test_generate_elasticsearch_status(self):
        """Tests the _generate_elasticsearch_status method"""

        elasticsearch = dependency_mgr._generate_elasticsearch_status()
        self.assertDictEqual(elasticsearch, {'OK': False, 'detail': {'msg': 'ELASTICSEARCH_URL is not set', 'url': None}, 
                                             'errors': [{'UNKNOWN_ERROR': 'ELASTICSEARCH_URL is not set.'}], 'warnings': []})
            

        with patch('scale.settings.ELASTICSEARCH_URL', 'http://offline.host'):
            elasticsearch = dependency_mgr._generate_elasticsearch_status()
        self.assertDictEqual(elasticsearch, {'OK': False, 'detail': {'msg': 'Unable to connect to elasticsearch', 'url': 'http://offline.host'}, 
                                             'errors': [{'CLUSTER_ERROR': 'Elasticsearch cluster is unreachable.'}], 'warnings': []})
        
        with patch('elasticsearch.Elasticsearch') as mock_elasticsearch:
            mock_elasticsearch.return_value.ping.return_value = True
            mock_elasticsearch.return_value.cluster.health.return_value = {'status': 'red'}
            with patch('scale.settings.ELASTICSEARCH_URL', 'http://red.host'):
                elasticsearch = dependency_mgr._generate_elasticsearch_status()
            self.assertDictEqual(elasticsearch, {'OK': False, 'detail': {'msg': 'One or more primary shards is not allocated to any node', 'url': 'http://red.host'},
                                                 'errors': [{'CLUSTER_RED': 'Elasticsearch cluster health is red. A primary shard is not allocated.'}], 'warnings': []})
            mock_elasticsearch.return_value.cluster.health.return_value = {'status': 'green'}
            mock_elasticsearch.return_value.info.return_value = {'tagline' : 'You know, for X'}
            with patch('scale.settings.ELASTICSEARCH_URL', 'http://green.host'):
                elasticsearch = dependency_mgr._generate_elasticsearch_status()
            self.assertDictEqual(elasticsearch, {u'OK': True, u'detail': {u'info': {u'tagline': u'You know, for X'}, 
                                                                          u'msg': u'Elasticsearch is healthy', u'url': u'http://green.host'}, 'errors': [], 'warnings': []})
            
    def test_generate_silo_status(self):
        """Tests the _generate_silo_status method"""

        silo = dependency_mgr._generate_silo_status()
        self.assertDictEqual(silo, {'OK': False, 'detail': {'url': None}, 'errors': [{'NO_SILO_DEFINED': 'No silo URL defined in environment. SOS.'}], 'warnings': []}) 
            
        with patch.dict('os.environ', {'SILO_URL': 'https://localhost'}):
            silo = dependency_mgr._generate_silo_status()
            self.assertFalse(silo['OK'])
            
        with patch.dict('os.environ', {'SILO_URL': 'https://en.wikipedia.org/wiki/Silo'}):
            silo = dependency_mgr._generate_silo_status()
            self.assertDictEqual(silo, {'OK': True, 'detail': {'msg': 'Silo is alive and connected', 'url': 'https://en.wikipedia.org/wiki/Silo'}, 'errors': [], 'warnings': []})
            
    def test_generate_database_status(self):
        """Tests the _generate_database_status method"""
    
        database = dependency_mgr._generate_database_status()
        self.assertDictEqual(database, {'OK': True, 'detail': {'msg': 'Database alive and well'}, 'errors': [], 'warnings': []})
        
        with patch('django.db.connection.ensure_connection') as mock:
            mock.side_effect = OperationalError
            database = dependency_mgr._generate_database_status()
            self.assertDictEqual(database, {'OK': False, 'detail': {'msg': 'Unable to connect to database'}, 
                                            'errors': [{'OPERATIONAL_ERROR': 'Database unavailable.'}], 'warnings': []})

    @patch('scale.settings.BROKER_URL', 'bad_broker')
    def test_generate_message_queue_status_invalid_broker(self):
        """Tests the _generate_msg_queue_status method with a bad broker setting"""
    
        msg_queue = dependency_mgr._generate_msg_queue_status()
        self.assertFalse(msg_queue['OK'])
        self.assertEqual(msg_queue['errors'][0].keys(), ['INVALID_BROKER_URL'])
        self.assertDictEqual(msg_queue, {'OK': False,
                                         'detail': {'num_message_handlers': scheduler_mgr.config.num_message_handlers, 'queue_depth': 0, 'type': '',
                                                    'queue_name': 'scale-command-messages', u'region_name': u'', 'msg': 'Error parsing broker url'},
                                         'errors': [{'INVALID_BROKER_URL': 'Error parsing broker url'}], 'warnings': []})

    @patch('scheduler.dependencies.manager.CommandMessageManager.get_queue_size')
    def test_generate_message_queue_status_rabbit_error(self, mock_get_queue_size):
        """Tests the _generate_msg_queue_status method with a bad amqp config"""
    
        mock_get_queue_size.side_effect = Exception('Error connecting to rabbit')
        msg_queue = dependency_mgr._generate_msg_queue_status()
        self.assertDictEqual(msg_queue, {'OK': False,
                                         'detail': {'num_message_handlers': scheduler_mgr.config.num_message_handlers, 'queue_depth': 0, 'type': 'amqp',
                                                    'queue_name': 'scale-command-messages', u'region_name': u'', 'msg': 'Unable to get message queue size.' },
                                         'errors': [{u'RABBITMQ_ERROR': u'Error connecting to RabbitMQ: Check Logs for details'}],
                                         'warnings': []})

    @patch('scale.settings.MESSSAGE_QUEUE_DEPTH_WARN', 100)
    @patch('scheduler.dependencies.manager.CommandMessageManager.get_queue_size')
    def test_generate_message_queue_status_rabbit_success(self, mock_get_queue_size):
        """Tests the _generate_msg_queue_status method with a good amqp config"""
    
        mock_get_queue_size.return_value = 99
        msg_queue = dependency_mgr._generate_msg_queue_status()
        self.assertDictEqual(msg_queue, {'OK': True,
                                         'detail': {'num_message_handlers': scheduler_mgr.config.num_message_handlers, 'queue_depth': 99, 'type': 'amqp',
                                                    'queue_name': 'scale-command-messages', u'region_name': u'', 'msg': 'Message Queue is healthy'},
                                         'errors': [], 'warnings': []})

        mock_get_queue_size.return_value = 101
        msg_queue = dependency_mgr._generate_msg_queue_status()
        self.assertDictEqual(msg_queue, {'OK': True,
                                         'detail': {'num_message_handlers': scheduler_mgr.config.num_message_handlers, 'queue_depth': 101, 'type': 'amqp',
                                                    'queue_name': 'scale-command-messages', 'region_name': '', 'msg': 'Message queue is large. Scale may be unresponsive.'},
                                         'errors': [], 'warnings': [{u'LARGE_QUEUE': u'Message queue is very large'}]})

    @patch('scale.settings.BROKER_URL', 'sqs://aws.com')
    @patch('scheduler.dependencies.manager.CommandMessageManager.get_queue_size')
    def test_generate_message_queue_status_sqs_error(self, mock_get_queue_size):
        """Tests the _generate_msg_queue_status method with a bad sqs config"""

        mock_get_queue_size.side_effect = Exception('Error connecting to sqs')
        msg_queue = dependency_mgr._generate_msg_queue_status()
        self.assertDictEqual(msg_queue, {'OK': False,
                                         'detail': {'num_message_handlers': scheduler_mgr.config.num_message_handlers, 'queue_depth': 0, 'type': 'sqs',
                                                    'queue_name': 'scale-command-messages', u'region_name': u'aws.com', 'msg': 'Unable to get message queue size.'},
                                         'errors': [{u'SQS_ERROR': u'Error connecting to SQS: Check Logs for details'}],
                                         'warnings': []})

    @patch('scale.settings.MESSSAGE_QUEUE_DEPTH_WARN', 100)
    @patch('scale.settings.BROKER_URL', 'sqs://aws.com')
    @patch('messaging.manager.CommandMessageManager.get_queue_size')
    def test_generate_message_queue_status_sqs_success(self, mock_get_queue_size):
        """Tests the _generate_msg_queue_status method with a good sqs config"""

        mock_get_queue_size.return_value = 99
        msg_queue = dependency_mgr._generate_msg_queue_status()
        self.assertDictEqual(msg_queue, {'OK': True,
                                         'detail': {'num_message_handlers': scheduler_mgr.config.num_message_handlers, 'type': 'sqs',
                                                    u'queue_depth': 99, u'queue_name': 'scale-command-messages',
                                                    u'region_name': u'aws.com', 'msg': 'Message Queue is healthy'},
                                         'errors': [], 'warnings': []})

        mock_get_queue_size.return_value = 101
        msg_queue = dependency_mgr._generate_msg_queue_status()
        self.assertDictEqual(msg_queue, {'OK': True,
                                         'detail': {'num_message_handlers': scheduler_mgr.config.num_message_handlers, 'type': 'sqs',
                                                    u'queue_depth': 101, u'queue_name': 'scale-command-messages',
                                                    u'region_name': u'aws.com', 'msg': 'Message queue is large. Scale may be unresponsive.'},
                                         'errors': [],
                                         'warnings': [{u'LARGE_QUEUE': u'Message queue is very large'}]})

    def test_generate_idam_status_no_geoaxis(self):
        """Tests the _generate_idam_status method with geoaxis disabled"""
    
        idam = dependency_mgr._generate_idam_status()
        self.assertDictEqual(idam, {'OK': True, 'detail': {'geoaxis_enabled': False, 'msg': 'GEOAxIS is not enabled'}, 'errors': [], 'warnings': []})
        
    @patch('scale.settings.SOCIAL_AUTH_GEOAXIS_KEY', 'key')
    @patch('scale.settings.SOCIAL_AUTH_GEOAXIS_SECRET', 'secret')
    @patch('scale.settings.GEOAXIS_ENABLED', True)
    @patch('scale.settings.AUTHENTICATION_BACKENDS', ['django.contrib.auth.backends.ModelBackend', 'django_geoaxis.backends.geoaxis.GeoAxisOAuth2'])
    @patch('requests.get', side_effect=mock_response_get)
    def test_generate_idam_status_geoaxis_404(self, mock_get):
        """Tests the _generate_idam_status method with geoaxis enabled and a bad url"""
        
        idam = dependency_mgr._generate_idam_status()
        detail = {}
        detail['geoaxis_host'] = u'geoaxis.gxaccess.com'
        detail['geoaxis_enabled'] = True
        detail['backends'] = ['django.contrib.auth.backends.ModelBackend', 'django_geoaxis.backends.geoaxis.GeoAxisOAuth2']
        detail['geoaxis_authorization_url'] = django_geoaxis.backends.geoaxis.GeoAxisOAuth2.AUTHORIZATION_URL
        detail['scale_vhost'] = 'localhost:8000'
        msg = 'Error accessing Geoaxis login url https://localhost:8000/social-auth/login/geoaxis/?=: HTTP File not found: None'
        detail['msg'] = msg
        self.assertDictEqual(idam, {'OK': False, 'detail': detail, 'errors': [{u'GEOAXIS_ERROR': msg}], 'warnings': []})

    @patch('scale.settings.SOCIAL_AUTH_GEOAXIS_KEY', 'key')
    @patch('scale.settings.SOCIAL_AUTH_GEOAXIS_SECRET', 'secret')
    @patch('scale.settings.GEOAXIS_ENABLED', True)
    @patch('scale.settings.AUTHENTICATION_BACKENDS',
           ['django.contrib.auth.backends.ModelBackend', 'django_geoaxis.backends.geoaxis.GeoAxisOAuth2'])
    @patch('scale.settings.SCALE_VHOST', 'unauthorized')
    @patch('requests.get', side_effect=mock_response_get)
    def test_generate_idam_status_geoaxis_401(self, mock_get):
        """Tests the _generate_idam_status method with geoaxis enabled and a bad config"""

        idam = dependency_mgr._generate_idam_status()
        detail = {}
        detail['geoaxis_host'] = u'geoaxis.gxaccess.com'
        detail['geoaxis_enabled'] = True
        detail['backends'] = ['django.contrib.auth.backends.ModelBackend',
                              'django_geoaxis.backends.geoaxis.GeoAxisOAuth2']
        detail['geoaxis_authorization_url'] = django_geoaxis.backends.geoaxis.GeoAxisOAuth2.AUTHORIZATION_URL
        detail['scale_vhost'] = 'unauthorized'
        msg = 'Error accessing Geoaxis login url https://unauthorized/social-auth/login/geoaxis/?=: HTTP Unauthorized: None'
        detail['msg'] = msg
        self.assertDictEqual(idam, {'OK': False, 'detail': detail, 'errors': [{u'GEOAXIS_ERROR': msg}], 'warnings': []})

    @patch('scale.settings.SOCIAL_AUTH_GEOAXIS_KEY', 'key')
    @patch('scale.settings.SOCIAL_AUTH_GEOAXIS_SECRET', 'secret')
    @patch('scale.settings.GEOAXIS_ENABLED', True)
    @patch('scale.settings.AUTHENTICATION_BACKENDS',
           ['django.contrib.auth.backends.ModelBackend', 'django_geoaxis.backends.geoaxis.GeoAxisOAuth2'])
    @patch('scale.settings.SCALE_VHOST', 'host-offline')
    @patch('requests.get', side_effect=mock_response_get)
    def test_generate_idam_status_geoaxis_503(self, mock_get):
        """Tests the _generate_idam_status method with geoaxis enabled and an unreachable host"""

        idam = dependency_mgr._generate_idam_status()
        detail = {}
        detail['geoaxis_host'] = u'geoaxis.gxaccess.com'
        detail['geoaxis_enabled'] = True
        detail['backends'] = ['django.contrib.auth.backends.ModelBackend',
                              'django_geoaxis.backends.geoaxis.GeoAxisOAuth2']
        detail['geoaxis_authorization_url'] = django_geoaxis.backends.geoaxis.GeoAxisOAuth2.AUTHORIZATION_URL
        detail['scale_vhost'] = 'host-offline'
        msg = 'Error accessing Geoaxis login url https://host-offline/social-auth/login/geoaxis/?=: HTTP Service Unavailable: None'
        detail['msg'] = msg
        self.assertDictEqual(idam, {'OK': False, 'detail': detail, 'errors': [{u'GEOAXIS_ERROR': msg}], 'warnings': []})

    @patch('scale.settings.SOCIAL_AUTH_GEOAXIS_KEY', 'key')
    @patch('scale.settings.SOCIAL_AUTH_GEOAXIS_SECRET', 'secret')
    @patch('scale.settings.GEOAXIS_ENABLED', True)
    @patch('scale.settings.AUTHENTICATION_BACKENDS',
           ['django.contrib.auth.backends.ModelBackend', 'django_geoaxis.backends.geoaxis.GeoAxisOAuth2'])
    @patch('scale.settings.SCALE_VHOST', 'scale.io')
    @patch('requests.get', side_effect=mock_response_get)
    def test_generate_idam_status_geoaxis_success(self, mock_get):
        """Tests the _generate_idam_status method with geoaxis enabled and a successful response"""

        idam = dependency_mgr._generate_idam_status()
        detail = {}
        detail['geoaxis_host'] = u'geoaxis.gxaccess.com'
        detail['geoaxis_enabled'] = True
        detail['backends'] = ['django.contrib.auth.backends.ModelBackend',
                              'django_geoaxis.backends.geoaxis.GeoAxisOAuth2']
        detail['geoaxis_authorization_url'] = django_geoaxis.backends.geoaxis.GeoAxisOAuth2.AUTHORIZATION_URL
        detail['scale_vhost'] = 'scale.io'
        detail['msg'] = 'GEOAxIS is enabled'
        self.assertDictEqual(idam, {'OK': True, 'detail': detail, 'errors': [], 'warnings': []})

    def test_generate_nodes_status(self):
        """Tests the _generate_nodes_status method"""

        # Setup nodes
        from scheduler.node.manager import node_mgr
        node_mgr.clear()

        nodes = dependency_mgr._generate_nodes_status()
        self.assertDictEqual(nodes, {'OK': False, 'detail': {'msg': 'No nodes reported'}, 'errors': [{'NODES_OFFLINE': 'No nodes reported.'}], 'warnings': []}) 

        node_mgr.register_agents([self.agent_1, self.agent_2, self.agent_3, self.agent_4, self.agent_5, self.agent_6,self.agent_7, self.agent_8, self.agent_9, self.agent_10])
        node_mgr.sync_with_database(scheduler_mgr.config)
        
        nodes = node_mgr.get_nodes()
        self.assertEqual(len(nodes), 10)
        
        nodes = dependency_mgr._generate_nodes_status()
        self.assertDictEqual(nodes, {'OK': True, 'detail': {'msg': 'Enough nodes are online to function.'}, 'errors': [], 'warnings': []})  
        
        node_mgr.lost_node(self.agent_1.agent_id)
        node_mgr.lost_node(self.agent_2.agent_id)
        node_mgr.lost_node(self.agent_3.agent_id)
        node_mgr.lost_node(self.agent_4.agent_id)
        nodes = dependency_mgr._generate_nodes_status()
        self.assertDictEqual(nodes, {'OK': False, 'detail': {u'msg': u'Over a third of nodes are in an error state'}, 
                                     'errors': [{'NODES_ERRORED': 'Over a third of the nodes are offline or degraded.'}], 
                                     'warnings': [{u'NODES_OFFLINE': u'4 nodes are offline'}]})  
        