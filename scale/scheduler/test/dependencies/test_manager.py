from __future__ import unicode_literals

import copy
from datetime import timedelta
import os
import django
from django.db.utils import OperationalError
from django.test import TestCase
from django.utils.timezone import now
from mock import MagicMock
from mock import call, patch

from messaging.backends.amqp import AMQPMessagingBackend
from messaging.backends.factory import add_message_backend
from node.test import utils as node_test_utils
from scheduler.manager import scheduler_mgr
from scheduler.node.agent import Agent
from scheduler.node.manager import NodeManager

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
    
    return MockResponse(404)

class TestDependenciesManager(TestCase):

    def setUp(self):
        django.setup()
        add_message_backend(AMQPMessagingBackend)
        
        
        from scheduler.models import Scheduler
        Scheduler.objects.create(id=1)
        
        scheduler_mgr.config.is_paused = False
        self.agent_1 = Agent('agent_1', 'host_1')
        self.agent_2 = Agent('agent_2', 'host_2')  # Will represent a new agent ID for host 2
        node_1 = node_test_utils.create_node(hostname='host_1')
        

    def test_generate_log_status(self):
        """Tests the _generate_log_status method"""
 
        from scheduler.dependencies.manager import dependency_mgr
        logs = dependency_mgr._generate_log_status()
        self.assertIsNotNone(logs)
        self.assertDictEqual(logs, {'OK': False, 'errors': [{'NO_LOGGING_DEFINED': 'No logging URL defined'}], 'warnings': []})   
        
        with patch('scale.settings.LOGGING_ADDRESS', 'http://www.logging.com/health'):
            from scheduler.dependencies.manager import dependency_mgr
            logs = dependency_mgr._generate_log_status()
            self.assertIsNotNone(logs)
            self.assertDictEqual(logs, {'OK': True, 'detail': {'url': 'http://www.logging.com/health'}})

        with patch('scale.settings.LOGGING_ADDRESS', 'localhost'):
            from scheduler.dependencies.manager import dependency_mgr
            logs = dependency_mgr._generate_log_status()
            self.assertIsNotNone(logs)
            errors =  [{'UNKNOWN_ERROR': "Error with LOGGING_ADDRESS: Invalid URL 'localhost': No schema supplied. Perhaps you meant http://localhost?"}]
            self.assertDictEqual(logs, {'OK': False, 'errors': errors, 'warnings': []})

        with patch('scale.settings.LOGGING_HEALTH_ADDRESS', 'http://www.logging.com/health'):
            from scheduler.dependencies.manager import dependency_mgr
            logs = dependency_mgr._generate_log_status()
            self.assertIsNotNone(logs)
            self.assertDictEqual(logs, {'OK': True, 'detail': {'url': 'http://www.logging.com/health'}})

        with patch('scale.settings.LOGGING_HEALTH_ADDRESS', 'http://localhost'):
            from scheduler.dependencies.manager import dependency_mgr
            logs = dependency_mgr._generate_log_status()
            self.assertIsNotNone(logs)
            self.assertFalse(logs['OK'])
     
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

    def test_generate_idam_status(self):
        """Tests the _generate_idam_status method"""
    
        from scheduler.dependencies.manager import dependency_mgr
        idam = dependency_mgr._generate_idam_status()
        self.assertDictEqual(idam, {u'OK': True, u'detail': u'some msg'}) 

    def test_generate_nodes_status(self):
        """Tests the _generate_nodes_status method"""

        # Setup nodes
        manager = NodeManager()
        manager.register_agents([self.agent_1, self.agent_2])
        manager.sync_with_database(scheduler_mgr.config)
        
        from scheduler.dependencies.manager import dependency_mgr
        nodes = dependency_mgr._generate_nodes_status()
        self.assertDictEqual(nodes, {'OK': True, 'detail': 'Enough nodes are online to function.', 'errors': [], 'warnings': []})  

        