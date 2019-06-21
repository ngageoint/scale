from __future__ import unicode_literals

import os
import django
from django.test import TestCase
from django.utils.timezone import now

import job.test.utils as job_test_utils
import ingest.test.utils as ingest_test_utils
import recipe.test.utils as recipe_test_utils
import storage.test.utils as storage_test_utils

from ingest.messages.create_ingest_jobs import create_strike_ingest_job_message, \
                                               create_scan_ingest_job_message, CreateIngest, STRIKE_JOB_TYPE
from ingest.models import Strike, Scan
from ingest.scan.configuration.json.configuration_v6 import ScanConfigurationV6
from ingest.strike.configuration.json.configuration_v6 import StrikeConfigurationV6
from messaging.backends.amqp import AMQPMessagingBackend
from messaging.backends.factory import add_message_backend
from storage.models import ScaleFile


class TestCreateIngest(TestCase):
    
    fixtures = ['ingest_job_types']
    
    def setUp(self):
        django.setup()
        add_message_backend(AMQPMessagingBackend)

        self.workspace_1 = storage_test_utils.create_workspace()
        self.workspace_2 = storage_test_utils.create_workspace()
        self.source_file = ScaleFile.objects.create(file_name='input_file', file_type='SOURCE',
                                               media_type='text/plain', file_size=10, data_type_tags=['type1'],
                                               file_path='the_path', workspace=self.workspace_1)

        self.source_file.add_data_type_tag('type1')
        self.source_file.add_data_type_tag('type2')
        self.source_file.add_data_type_tag('type3')

        self.ingest = ingest_test_utils.create_ingest(source_file=self.source_file, new_workspace=self.workspace_2)

        manifest = job_test_utils.create_seed_manifest(inputs_files=[{'name': 'INPUT_FILE', 'media_types': ['text/plain'], 'required': True, 'multiple': True}], inputs_json=[])
        self.jt1 = job_test_utils.create_seed_job_type(manifest=manifest)
        recipe_type_def = {'version': '6',
                           'input': {'files': [{'name': 'INPUT_FILE',
                                                'media_types': ['text/plain'],
                                                'required': True,
                                                'multiple': True}],
                                    'json': []},
                           'nodes': {'node_a': {'dependencies': [],
                                                'input': {'INPUT_FILE': {'type': 'recipe', 'input': 'INPUT_FILE'}},
                                                'node_type': {'node_type': 'job', 'job_type_name': self.jt1.name,
                                                              'job_type_version': self.jt1.version,
                                                              'job_type_revision': 1}}}}

        self.recipe_type = recipe_test_utils.create_recipe_type_v6(name='test-recipe', definition=recipe_type_def)

        strike_config = {
            'version': '6',
            'workspace': self.workspace_1.name,
            'monitor': {'type': 'dir-watcher', 'transfer_suffix': '_tmp'},
            'files_to_ingest': [{
                'filename_regex': 'input_file',
                'data_types': ['image_type'],
                'new_workspace': self.workspace_2.name,
                'new_file_path': 'my/path'
            }],
            'recipe': {
                'name': self.recipe_type.name
            },
        }
        config = StrikeConfigurationV6(strike_config).get_configuration()
        self.strike = Strike.objects.create_strike('my_name', 'my_title', 'my_description', config)

        scan_config = {
            'workspace': self.workspace_1.name,
            'scanner': {
                'type': 'dir'
            },
            'files_to_ingest': [{
                'filename_regex': 'input_file',
                'data_types': ['type1'],
                'new_file_path': os.path.join('my', 'path'),
                'new_workspace': self.workspace_2.name,
            }],
            'recipe': {
                'name': self.recipe_type.name,
            },
        }
        scan_configuration = ScanConfigurationV6(scan_config).get_configuration()
        self.scan = Scan.objects.create_scan('my_name', 'my_title', 'my_description', scan_configuration)
        
    def test_json_create(self):
        """Tests converting a CreateIngest message to and from json
        """

        message = CreateIngest()
        message.create_ingest_type = STRIKE_JOB_TYPE
        message.ingest_id = self.ingest.id
        message.strike_id = self.strike.id

        # Convert message to JSON and back, and then execute
        message_dict = message.to_json()
        new_message = CreateIngest.from_json(message_dict)
        result = new_message.execute()

        self.assertTrue(result)
        self.assertEqual(len(new_message.new_messages), 1)
        self.assertTrue(new_message.new_messages[0].type, 'process_job_input')


    def test_execute(self):
        """Tests executing a CreateIngest message """
        message = create_strike_ingest_job_message(self.ingest.id, self.strike.id)
        result = message.execute()
        self.assertTrue(result)
        self.assertEqual(len(message.new_messages), 1)
        new_message = message.new_messages[0]
        self.assertTrue(new_message.type, 'process_job_input')

        # TODO test scan ingest job
        # message = create_scan_ingest_job_message(self.ingest.id, self.workspace_1.name, self.workspace_2.name,
        #                                            self.scan.id, self.source_file.file_name)
        # result = message.execute()
        # self.assertTrue(result)
        # self.assertEqual(len(message.new_messages), 1)
        # new_message = message.new_messages[0]
        # self.assertTrue(new_message.type, 'process_job_input')
        