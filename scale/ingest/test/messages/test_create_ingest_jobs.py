from __future__ import unicode_literals

import django
from django.test import TestCase
from django.utils.timezone import now

import storage.test.utils as storage_test_utils

from ingest.messages.create_ingest_jobs import CreateIngest
from ingest.models import Ingest
from storage.models import ScaleFile

class TestCreateIngest(TestCase):
    
    fixtures = ['ingest_job_types']
    
    def setUp(self):
        django.setup()
        
    def test_json_create(self):
        """Tests converting a CreateIngest message to and from json
        """
        
        message = CreateIngest()
        message.create_ingest_type = 'strike_job'
        message.strike_id = 1
        message.ingest_id = 1
        
        message_json_dict = message.to_json()
        new_message = CreateIngest.from_json(message_json_dict)
        
        self.assertEqual(new_message.ingest_id, message.ingest_id)
        self.assertEqual(new_message.strike_id, message.strike_id)
        self.assertEqual(new_message.create_ingest_type, message.create_ingest_type)
        self.assertIsNone(new_message.scan_id)
        
        scan_message = CreateIngest()
        scan_message.create_ingest_type = 'scan_job'
        scan_message.scan_id = 2
        scan_message.ingest_id = 2
    
        scan_message_json_dict = scan_message.to_json()
        new_scan_message = CreateIngest.from_json(scan_message_json_dict)
        
        self.assertEqual(new_scan_message.ingest_id, scan_message.ingest_id)
        self.assertEqual(new_scan_message.scan_id, scan_message.scan_id)
        self.assertEqual(new_scan_message.create_ingest_type, scan_message.create_ingest_type)
        self.assertIsNone(new_scan_message.strike_id)
        
    def test_execute(self):
        """Tests executing a CreateIngest message
        """
        
        workspace_1 = storage_test_utils.create_workspace()
        workspace_2 = storage_test_utils.create_workspace()
        source_file = ScaleFile.objects.create(file_name='input_file', file_type='SOURCE',
                                               media_type='text/plain', file_size=10, data_type_tags=['type1'],
                                               file_path='the_path', workspace=workspace_1)
        ingest = Ingest.objects.create(file_name='input_file', file_size=10, status='TRANSFERRING', 
                                            bytes_transferred=10, transfer_started=now(), media_type='text/plain',
                                            ingest_started=now(), data_started=now(), 
                                            workspace=workspace_1, new_workspace=workspace_2, 
                                            data_type_tags=['type1'], source_file=source_file)
        
        message = CreateIngest()
        message.create_ingest_type = 'strike_job'
        message.strike_id = 1
        message.ingest_id = ingest.id
        
        result = message.execute()
        
        self.assertTrue(result)
        self.assertEqual(len(message.new_messages), 1)
        self.assertEqual(message.new_messages[0].type, 'process_job_input')
        