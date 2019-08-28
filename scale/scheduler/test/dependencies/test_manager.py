from __future__ import unicode_literals

import django
import django_geoaxis
from django.db.utils import OperationalError
from django.test import TestCase
from kombu.exceptions import HttpError
from mock import patch

from messaging.backends.amqp import AMQPMessagingBackend
from messaging.backends.factory import add_message_backend
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
    elif args[0] == 'http://scale.io/social-auth/login/geoaxis/?=':
        return MockResponse({}, 200)
    elif args[0] == 'http://unauthorized/social-auth/login/geoaxis/?=':
        return MockResponse({}, 401, HttpError('Unauthorized'))
    elif args[0] == 'http://host-offline/social-auth/login/geoaxis/?=':
        return MockResponse({}, 503, HttpError('Service Unavailable'))
    
    return MockResponse({}, 404, HttpError('File not found'))

class TestDependenciesManager(TestCase):

    def setUp(self):
        django.setup()
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
 
        from scheduler.dependencies.manager import dependency_mgr
        logs = dependency_mgr._generate_log_status()
        self.assertIsNotNone(logs)
        self.assertDictEqual(logs, {'OK': False, 'detail': {}, 'errors': [{'NO_LOGGING_HEALTH_DEFINED': 'No logging health URL defined'}, {'NO_LOGGING_DEFINED': 'No logging address defined'}], 'warnings': []})   

    @patch('scale.settings.LOGGING_ADDRESS', 'tcp://localhost:1234')
    @patch('scale.settings.LOGGING_HEALTH_ADDRESS', 'localhost')
    def test_generate_log_status_bad(self):
        """Tests the _generate_log_status method with invalid settings"""
 
        from scheduler.dependencies.manager import dependency_mgr
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
 
        from scheduler.dependencies.manager import dependency_mgr
        logs = dependency_mgr._generate_log_status()
        self.assertIsNotNone(logs)
        self.assertDictEqual(logs, {'OK': True, 'detail': {'logging_address': 'tcp://localhost:1234', 'logging_health_address': 'http://www.logging.com/health'}, 'errors': [], 'warnings': []}) 

    @patch('scale.settings.LOGGING_ADDRESS', 'tcp://localhost:1234')
    @patch('scale.settings.LOGGING_HEALTH_ADDRESS', 'http://localhost')
    @patch('scale.settings.FLUENTD_BUFFER_WARN', 10)
    @patch('scale.settings.FLUENTD_BUFFER_SIZE_WARN', 100000000)
    @patch('socket.socket.connect')
    @patch('requests.get', side_effect=mock_response_get)
    def test_generate_log_status_warn(self, mock_requests, connect):
        """Tests the _generate_log_status method with good settings and large queues"""
 
        from scheduler.dependencies.manager import dependency_mgr
        logs = dependency_mgr._generate_log_status()
        self.assertIsNotNone(logs)
        msg = 'Length of log buffer is too long: 20 > 10'
        warnings = [{'LARGE_BUFFER': msg}]
        msg = 'Size of log buffer is too large: 100000000000 > 100000000'
        warnings.append({'LARGE_BUFFER_SIZE': msg})
        self.assertDictEqual(logs, {'OK': True, 'detail': {'logging_address': 'tcp://localhost:1234', 'logging_health_address': 'http://localhost'}, 'errors': [], 'warnings': warnings}) 
     
    def test_generate_elasticsearch_status(self):
        """Tests the _generate_elasticsearch_status method"""

        from scheduler.dependencies.manager import dependency_mgr
        elasticsearch = dependency_mgr._generate_elasticsearch_status()
        self.assertDictEqual(elasticsearch, {'OK': False, 'errors': [{'UNKNOWN_ERROR': 'Elasticsearch is unreachable. SOS.'}], 'warnings': []})
            
        with patch('scale.settings.ELASTICSEARCH') as mock_elasticsearch:
            # Setup elasticsearch status
            mock_elasticsearch.ping.return_value = False
            elasticsearch = dependency_mgr._generate_elasticsearch_status()
            self.assertDictEqual(elasticsearch, {'OK': False, 'errors': [{'CLUSTER_ERROR': 'Elasticsearch cluster is unreachable. SOS.'}], 'warnings': []})
            mock_elasticsearch.ping.return_value = True
            mock_elasticsearch.cluster.health.return_value = {'status': 'red'}
            elasticsearch = dependency_mgr._generate_elasticsearch_status()
            self.assertDictEqual(elasticsearch, {'OK': False, 'errors': [{'CLUSTER_RED': 'Elasticsearch cluster health is red. SOS.'}], 'warnings': []})
            mock_elasticsearch.cluster.health.return_value = {'status': 'green'}
            mock_elasticsearch.info.return_value = {'tagline' : 'You know, for X'}
            from scheduler.dependencies.manager import dependency_mgr
            elasticsearch = dependency_mgr._generate_elasticsearch_status()
            self.assertDictEqual(elasticsearch, {u'OK': True, u'detail': {u'tagline': u'You know, for X'}})
            
    def test_generate_silo_status(self):
        """Tests the _generate_silo_status method"""

        from scheduler.dependencies.manager import dependency_mgr
        silo = dependency_mgr._generate_silo_status()
        self.assertDictEqual(silo, {'OK': False, 'errors': [{'NO_SILO_DEFINED': 'No silo URL defined in environment. SOS.'}], 'warnings': []}) 
            
        with patch.dict('os.environ', {'SILO_URL': 'https://localhost'}):
            from scheduler.dependencies.manager import dependency_mgr
            silo = dependency_mgr._generate_silo_status()
            self.assertFalse(silo['OK'])
            
        with patch.dict('os.environ', {'SILO_URL': 'https://en.wikipedia.org/wiki/Silo'}):
            from scheduler.dependencies.manager import dependency_mgr
            silo = dependency_mgr._generate_silo_status()
            self.assertDictEqual(silo, {'OK': True, 'detail': {'url': 'https://en.wikipedia.org/wiki/Silo'}})
            
    def test_generate_database_status(self):
        """Tests the _generate_database_status method"""
    
        from scheduler.dependencies.manager import dependency_mgr
        database = dependency_mgr._generate_database_status()
        self.assertDictEqual(database, {'OK': True, 'detail': 'Database alive and well'})
        
        with patch('django.db.connection.ensure_connection') as mock:
            mock.side_effect = OperationalError
            from scheduler.dependencies.manager import dependency_mgr
            database = dependency_mgr._generate_database_status()
            self.assertDictEqual(database, {'OK': False, 'errors': [{'OPERATIONAL_ERROR': 'Database unavailable.'}], 'warnings': []})

    def test_generate_message_queue_status(self):
        """Tests the _generate_msg_queue_status method"""
    
        with patch('messaging.backends.amqp.Connection') as connection:
            from scheduler.dependencies.manager import dependency_mgr
            msg_queue = dependency_mgr._generate_msg_queue_status()
            self.assertFalse(msg_queue['OK'])
            self.assertEqual(msg_queue['errors'][0].keys(), ['UNKNOWN_ERROR'])

    def test_generate_idam_status_no_geoaxis(self):
        """Tests the _generate_idam_status method with geoaxis disabled"""
    
        from scheduler.dependencies.manager import dependency_mgr
        idam = dependency_mgr._generate_idam_status()
        self.assertDictEqual(idam, {'OK': True, 'detail': {'geoaxis': False, 'msg': 'Geoaxis is not enabled'}, 'errors': [], 'warnings': []})
        
    @patch('scale.settings.SOCIAL_AUTH_GEOAXIS_KEY', 'key')
    @patch('scale.settings.SOCIAL_AUTH_GEOAXIS_SECRET', 'secret')
    @patch('scale.settings.GEOAXIS_ENABLED', True)
    @patch('scale.settings.AUTHENTICATION_BACKENDS', ['django.contrib.auth.backends.ModelBackend', 'django_geoaxis.backends.geoaxis.GeoAxisOAuth2'])
    @patch('requests.get', side_effect=mock_response_get)
    def test_generate_idam_status_geoaxis_404(self, mock_get):
        """Tests the _generate_idam_status method with geoaxis enabled and a bad url"""
        
        from scheduler.dependencies.manager import dependency_mgr
        idam = dependency_mgr._generate_idam_status()
        detail = {}
        detail['Geoaxis Host'] = u'geoaxis.gxaccess.com'
        detail['geoaxis'] = True
        detail['backends'] = ['django.contrib.auth.backends.ModelBackend', 'django_geoaxis.backends.geoaxis.GeoAxisOAuth2']
        detail['Geoaxis Authorization Url'] = django_geoaxis.backends.geoaxis.GeoAxisOAuth2.AUTHORIZATION_URL
        self.assertDictEqual(idam, {'OK': False, 'detail': detail, 'errors': [{u'GEOAXIS_ERROR': 'Error accessing Geoaxis login url: HTTP File not found: None'}], 'warnings': []})

    @patch('scale.settings.SOCIAL_AUTH_GEOAXIS_KEY', 'key')
    @patch('scale.settings.SOCIAL_AUTH_GEOAXIS_SECRET', 'secret')
    @patch('scale.settings.GEOAXIS_ENABLED', True)
    @patch('scale.settings.AUTHENTICATION_BACKENDS',
           ['django.contrib.auth.backends.ModelBackend', 'django_geoaxis.backends.geoaxis.GeoAxisOAuth2'])
    @patch('scale.settings.SCALE_HOST', 'http://unauthorized')
    @patch('requests.get', side_effect=mock_response_get)
    def test_generate_idam_status_geoaxis_401(self, mock_get):
        """Tests the _generate_idam_status method with geoaxis enabled and a bad config"""

        from scheduler.dependencies.manager import dependency_mgr
        idam = dependency_mgr._generate_idam_status()
        detail = {}
        detail['Geoaxis Host'] = u'geoaxis.gxaccess.com'
        detail['geoaxis'] = True
        detail['backends'] = ['django.contrib.auth.backends.ModelBackend',
                              'django_geoaxis.backends.geoaxis.GeoAxisOAuth2']
        detail['Geoaxis Authorization Url'] = django_geoaxis.backends.geoaxis.GeoAxisOAuth2.AUTHORIZATION_URL
        self.assertDictEqual(idam, {'OK': False, 'detail': detail, 'errors': [{u'GEOAXIS_ERROR': 'Error accessing Geoaxis login url: HTTP Unauthorized: None'}], 'warnings': []})

    @patch('scale.settings.SOCIAL_AUTH_GEOAXIS_KEY', 'key')
    @patch('scale.settings.SOCIAL_AUTH_GEOAXIS_SECRET', 'secret')
    @patch('scale.settings.GEOAXIS_ENABLED', True)
    @patch('scale.settings.AUTHENTICATION_BACKENDS',
           ['django.contrib.auth.backends.ModelBackend', 'django_geoaxis.backends.geoaxis.GeoAxisOAuth2'])
    @patch('scale.settings.SCALE_HOST', 'http://host-offline')
    @patch('requests.get', side_effect=mock_response_get)
    def test_generate_idam_status_geoaxis_503(self, mock_get):
        """Tests the _generate_idam_status method with geoaxis enabled and an unreachable host"""

        from scheduler.dependencies.manager import dependency_mgr
        idam = dependency_mgr._generate_idam_status()
        detail = {}
        detail['Geoaxis Host'] = u'geoaxis.gxaccess.com'
        detail['geoaxis'] = True
        detail['backends'] = ['django.contrib.auth.backends.ModelBackend',
                              'django_geoaxis.backends.geoaxis.GeoAxisOAuth2']
        detail['Geoaxis Authorization Url'] = django_geoaxis.backends.geoaxis.GeoAxisOAuth2.AUTHORIZATION_URL
        self.assertDictEqual(idam, {'OK': False, 'detail': detail, 'errors': [{u'GEOAXIS_ERROR': 'Error accessing Geoaxis login url: HTTP Service Unavailable: None'}], 'warnings': []})

    @patch('scale.settings.SOCIAL_AUTH_GEOAXIS_KEY', 'key')
    @patch('scale.settings.SOCIAL_AUTH_GEOAXIS_SECRET', 'secret')
    @patch('scale.settings.GEOAXIS_ENABLED', True)
    @patch('scale.settings.AUTHENTICATION_BACKENDS',
           ['django.contrib.auth.backends.ModelBackend', 'django_geoaxis.backends.geoaxis.GeoAxisOAuth2'])
    @patch('scale.settings.SCALE_HOST', 'http://scale.io')
    @patch('requests.get', side_effect=mock_response_get)
    def test_generate_idam_status_geoaxis_success(self, mock_get):
        """Tests the _generate_idam_status method with geoaxis enabled and a successful response"""

        from scheduler.dependencies.manager import dependency_mgr
        idam = dependency_mgr._generate_idam_status()
        detail = {}
        detail['Geoaxis Host'] = u'geoaxis.gxaccess.com'
        detail['geoaxis'] = True
        detail['backends'] = ['django.contrib.auth.backends.ModelBackend',
                              'django_geoaxis.backends.geoaxis.GeoAxisOAuth2']
        detail['Geoaxis Authorization Url'] = django_geoaxis.backends.geoaxis.GeoAxisOAuth2.AUTHORIZATION_URL
        self.assertDictEqual(idam, {'OK': True, 'detail': detail, 'errors': [], 'warnings': []})

    def test_generate_nodes_status(self):
        """Tests the _generate_nodes_status method"""

        from scheduler.dependencies.manager import dependency_mgr
        nodes = dependency_mgr._generate_nodes_status()
        self.assertDictEqual(nodes, {'OK': False, 'errors': [{'NODES_OFFLINE': 'No nodes reported.'}], 'warnings': []}) 
        
        # Setup nodes
        from scheduler.node.manager import node_mgr
        node_mgr.register_agents([self.agent_1, self.agent_2, self.agent_3, self.agent_4, self.agent_5, self.agent_6,self.agent_7, self.agent_8, self.agent_9, self.agent_10])
        node_mgr.sync_with_database(scheduler_mgr.config)
        
        nodes = node_mgr.get_nodes()
        self.assertEqual(len(nodes), 10)
        
        nodes = dependency_mgr._generate_nodes_status()
        self.assertDictEqual(nodes, {'OK': True, 'detail': 'Enough nodes are online to function.', 'errors': [], 'warnings': []})  
        
        node_mgr.lost_node(self.agent_1.agent_id)
        node_mgr.lost_node(self.agent_2.agent_id)
        node_mgr.lost_node(self.agent_3.agent_id)
        node_mgr.lost_node(self.agent_4.agent_id)
        nodes = dependency_mgr._generate_nodes_status()
        self.assertDictEqual(nodes, {'OK': False, 'detail': 'Over a third of nodes are in an error state', 'errors': [{'NODES_ERRORED': 'Over a third of the nodes are offline or degraded.'}], 'warnings': []})  
        