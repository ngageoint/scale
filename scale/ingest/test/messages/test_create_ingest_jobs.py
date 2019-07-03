from __future__ import unicode_literals

import django
from django.test import TestCase

from ingest.messages.create_ingest_jobs import CreateIngest

class TestCreateIngest(TestCase):
    
    fixtures = ['ingest_job_types']
    
    def setUp(self):
        django.setup()
        
    def test_json_create_strike(self):
        """Tests converting a CreateIngest message to and from json
        """
        
        message = CreateIngest()
        message.create_ingest_type = 'strike_job'
        message.strike_id = 1
        message.scan_id = 1
        
        message_json_dict = message.to_json()
        new_message = CreateIngest.from_json(message_json_dict)
        
        self.assertEqual(new_message.ingest_id, message.ingest_id)
        self.assertEqual(new_message.strike_id, message.strike_id)
        self.assertEqual(new_message.create_ingest_type, message.create_ingest_type)
       