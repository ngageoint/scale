from __future__ import unicode_literals

import copy
from datetime import timedelta
import os
import django
from django.test import TestCase
from django.utils.timezone import now
from mock import MagicMock
from mock import call, patch

from messaging.backends.amqp import AMQPMessagingBackend
from messaging.backends.factory import add_message_backend

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
        
    
    @patch('scale.settings.LOGGING_HEALTH_ADDRESS', 'http://www.logging.com/health')
    @patch.dict('os.environ', {'SILO_URL': 'http://www.silo.com/'})
    @patch('requests.head', side_effect=mock_response_head)
    @patch('scale.settings.ELASTICSEARCH')
    @patch('messaging.backends.amqp.Connection')
    def test_generate_status_json(self, connection, mock_elasticsearch, mock_head):
        """Tests the generate_status_json method
        """
        # import pdb; pdb.set_trace()
        mock_elasticsearch.ping.return_value = True
        mock_elasticsearch.cluster.health.return_value = {'status': 'green'}
        mock_elasticsearch.info.return_value = {'tagline' : 'You know, for X'}
        
        from scheduler.dependencies.manager import dependency_mgr
        status = {}
        status = dependency_mgr.generate_status_json(status)
        self.assertIsInstance(status, dict)
        self.assertTrue('dependencies' in status)
        dependencies = status['dependencies']
        self.assertIsNotNone(dependencies)

        # Check each individual status        

        # Check Log status
        self.assertTrue('logs' in dependencies)
        logs = dependencies['logs']
        self.assertIsNotNone(logs)
        self.assertDictEqual(logs, {'OK': True, 'detail': {'url': 'http://www.logging.com/health'}})
        print(logs)
        
        # Check Elasticsearch status
        self.assertTrue('elasticsearch' in dependencies)
        elasticsearch = dependencies['elasticsearch']
        self.assertIsNotNone(elasticsearch)
        self.assertDictEqual(elasticsearch, {u'OK': True, u'detail': {u'tagline': u'You know, for X'}})
        print(elasticsearch)
        
        # Check SILO status
        self.assertTrue('silo' in dependencies)
        silo = dependencies['silo']
        self.assertIsNotNone(silo)
        self.assertDictEqual(silo, {'OK': True, 'detail': {'url': 'http://www.silo.com/'}})
        print(silo)
        
        # Check Database status
        self.assertTrue('database' in dependencies)
        database = dependencies['database']
        self.assertIsNotNone(database)
        self.assertDictEqual(database, {'OK': True, 'detail': 'Database alive and well'})
        print(database)
        
        # Check msg queue status
        self.assertTrue('msg_queue' in dependencies)
        msg_queue = dependencies['msg_queue']
        self.assertIsNotNone(msg_queue)
        # self.assertDictEqual(msg_queue, {'OK': True, 'detail': {}})
        print(msg_queue)
        
        # Check IDAM status
        self.assertTrue('idam' in dependencies)
        idam = dependencies['idam']
        self.assertIsNotNone(idam)
        self.assertDictEqual(idam, {u'OK': True, u'detail': u'some msg'})
        print(idam)
        
        # Check Nodes status
        self.assertTrue('nodes' in dependencies)
        nodes = dependencies['nodes']
        self.assertIsNotNone(nodes)
        self.assertDictEqual(nodes, {u'OK': True, u'detail': u'some msg'})
        print(nodes)
        
        