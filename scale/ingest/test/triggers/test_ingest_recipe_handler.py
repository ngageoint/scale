from __future__ import unicode_literals

import django
import os
from django.db import transaction
from django.test import TransactionTestCase
from django.utils.timezone import now
from mock import patch

import job.test.utils as job_test_utils
import recipe.test.utils as recipe_test_utils
import storage.test.utils as storage_test_utils
import trigger.test.utils as trigger_test_utils
import ingest.test.utils as ingest_test_utils
from ingest.models import Strike
from ingest.models import Scan
from ingest.scan.configuration.json.configuration_v6 import ScanConfigurationV6
from ingest.strike.configuration.json.configuration_v6 import StrikeConfigurationV6
from ingest.triggers.ingest_recipe_handler import IngestRecipeHandler
from job.models import Job
from messaging.backends.amqp import AMQPMessagingBackend
from messaging.backends.factory import add_message_backend
from recipe.models import Recipe
from storage.models import ScaleFile

class TestIngestRecipeHandlerProcessIngestedSourceFile(TransactionTestCase):
    fixtures = ['ingest_job_types.json']
    def setUp(self):
        django.setup()
        
        add_message_backend(AMQPMessagingBackend)

        self.workspace = storage_test_utils.create_workspace()
        self.source_file = ScaleFile.objects.create(file_name='input_file', file_type='SOURCE',
                                               media_type='text/plain', file_size=10, data_type_tags=['type1'],
                                                    file_path='the_path', workspace=self.workspace)
        self.source_file.add_data_type_tag('type1')
        self.source_file.add_data_type_tag('type2')
        self.source_file.add_data_type_tag('type3')
        manifest = job_test_utils.create_seed_manifest(inputs_files=[{'name': 'INPUT_FILE', 'media_types': ['text/plain'], 'required': True, 'multiple': True}], inputs_json=[])
        self.jt1 = job_test_utils.create_seed_job_type(manifest=manifest)
        v6_recipe_type_def = {'version': '6',
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

        self.recipe = recipe_test_utils.create_recipe_type_v6(name='test-recipe', definition=v6_recipe_type_def)

        v7_recipe_type_def = {'version': '7',
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
        self.recipe_v7 = recipe_test_utils.create_recipe_type_v6(name='test-recipe-v7', definition=v7_recipe_type_def)

    @patch('queue.models.CommandMessageManager')
    @patch('recipe.models.CommandMessageManager')
    @patch('ingest.models.CommandMessageManager')
    def test_successful_recipe_kickoff(self, mock_msg_mgr, mock_msg_mgr_rc, mock_msg_mgr_q):
        """Tests successfully producing an ingest that immediately calls a recipe"""

        strike_config = {
            'version': '7',
            'workspace': self.workspace.name,
            'monitor': {'type': 'dir-watcher', 'transfer_suffix': '_tmp'},
            'files_to_ingest': [{
                'filename_regex': 'input_file',
                'data_types': ['image_type'],
                'new_workspace': self.workspace.name,
                'new_file_path': 'my/path'
            }],
            'recipe': {
                'name': self.recipe_v7.name
            },
        }
        config = StrikeConfigurationV6(strike_config).get_configuration()
        strike = Strike.objects.create_strike('my_name', 'my_title', 'my_description', config)
        ingest = ingest_test_utils.create_ingest(source_file=self.source_file)

        # Call method to test
        IngestRecipeHandler().process_ingested_source_file(ingest.id, strike, self.source_file, now())
        self.assertEqual(Recipe.objects.count(), 1)
        self.assertEqual(Recipe.objects.first().recipe_type.name, self.recipe_v7.name)

        # Verify ingest event and trigger event objects were created
        from ingest.models import IngestEvent
        events = IngestEvent.objects.all().values()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['type'], 'STRIKE')
        
        # Create scan
        scan_config = {
            'workspace': self.workspace.name,
            'scanner': {
                'type': 'dir'
            },
            'files_to_ingest': [{
                'filename_regex': 'input_file',
                'data_types': ['type1'],
                'new_file_path': os.path.join('my', 'path'),
                'new_workspace': self.workspace.name,
            }],
            'recipe': {
                'name': self.recipe_v7.name,
            },
        }
        scan_configuration = ScanConfigurationV6(scan_config).get_configuration()
        scan = Scan.objects.create_scan('my_name', 'my_title', 'my_description', scan_configuration)

        # Call method to test
        IngestRecipeHandler().process_ingested_source_file(ingest.id, scan, self.source_file, now())
        self.assertEqual(Recipe.objects.count(), 2)
        self.assertEqual(Recipe.objects.last().recipe_type.name, self.recipe_v7.name)

        # Verify events were created
        events = IngestEvent.objects.all().values()
        self.assertEqual(len(events), 2)
        self.assertEqual(events[1]['type'], 'SCAN')
        
        # Update the recipe then call ingest with revision 1
        manifest = job_test_utils.create_seed_manifest(
            inputs_files=[{'name': 'INPUT_FILE', 'media_types': ['text/plain'], 'required': True, 'multiple': True}], inputs_json=[])
        jt2 = job_test_utils.create_seed_job_type(manifest=manifest)
        definition = {'version': '7',
                      'input': {'files': [{'name': 'INPUT_FILE',
                                            'media_types': ['text/plain'],
                                            'required': True,
                                            'multiple': True}],
                                'json': []},
                      'nodes': {'node_a': {'dependencies': [],
                                                'input': {'INPUT_FILE': {'type': 'recipe', 'input': 'INPUT_FILE'}},
                                                'node_type': {'node_type': 'job', 'job_type_name': self.jt1.name,
                                                              'job_type_version': self.jt1.version,
                                                              'job_type_revision': 1}},
                                'node_b': {'dependencies': [],
                                                'input': {'INPUT_FILE': {'type': 'recipe', 'input': 'INPUT_FILE'}},
                                                'node_type': {'node_type': 'job', 'job_type_name': jt2.name,
                                                              'job_type_version': jt2.version,
                                                              'job_type_revision': 1}}}}
        
        recipe_test_utils.edit_recipe_type_v6(recipe_type=self.recipe, definition=definition)
        
        strike_config['recipe'] = {
            'name': self.recipe.name,
            'revision_num': 1,
        }
        config = StrikeConfigurationV6(strike_config).get_configuration()
        strike = Strike.objects.create_strike('my_name_2', 'my_title_2', 'my_description_2', config)
        ingest = ingest_test_utils.create_ingest(source_file=self.source_file)

        # Call method to test
        IngestRecipeHandler().process_ingested_source_file(ingest.id, strike, self.source_file, now())
        self.assertEqual(Recipe.objects.count(), 3)
        self.assertEqual(Recipe.objects.last().recipe_type.name, self.recipe.name)

        # Verify events were created
        events = IngestEvent.objects.all().values()
        self.assertEqual(len(events), 3)
        self.assertEqual(events[2]['type'], 'STRIKE')

    @patch('queue.models.CommandMessageManager')
    def test_successful_manual_kickoff(self, mock_msg_mgr):
        """Tests successfully producing an ingest that immediately calls a recipe"""
        
        ingest = ingest_test_utils.create_ingest(source_file=self.source_file)
        recipe_type = recipe_test_utils.create_recipe_type_v6(definition=recipe_test_utils.RECIPE_DEFINITION)

        # Call method to test
        IngestRecipeHandler().process_manual_ingested_source_file(ingest.id, self.source_file, now(), recipe_type.id)
        self.assertEqual(Recipe.objects.all().count(), 1)
        self.assertEqual(Recipe.objects.first().recipe_type.name, recipe_type.name)
