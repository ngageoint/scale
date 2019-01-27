from __future__ import unicode_literals

import django
from django.test import TransactionTestCase
from django.utils.timezone import now

import job.test.utils as job_test_utils
import recipe.test.utils as recipe_test_utils
import storage.test.utils as storage_test_utils
import trigger.test.utils as trigger_test_utils
from ingest.models import Strike
from ingest.strike.configuration.json.configuration_v6 import StrikeConfigurationV6
from ingest.triggers.ingest_trigger_handler import IngestTriggerHandler
from job.models import Job
from queue.models import Queue
from storage.models import ScaleFile


class TestIngestTriggerHandlerProcessIngestedSourceFile(TransactionTestCase):
    fixtures = ['ingest_job_types.json']
    def setUp(self):
        django.setup()

        self.input_name = 'Test Input'
        self.output_name = 'Test Output'

        interface_1 = {
            'version': '1.0',
            'command': 'my_cmd',
            'command_arguments': 'args',
            'input_data': [{
                'name': self.input_name,
                'type': 'file',
            }],
        }
        self.job_type_1 = job_test_utils.create_job_type(interface=interface_1)

        interface_2 = {
            'version': '1.0',
            'command': 'my_cmd',
            'command_arguments': 'args',
            'input_data': [{
                'name': self.input_name,
                'type': 'file',
            }],
            'output_data': [{
                'name': self.output_name,
                'type': 'file',
            }],
        }
        self.job_type_2 = job_test_utils.create_job_type(interface=interface_2)

        # create a recipe that runs both jobs
        definition_1 = {
            'version': '1.0',
            'input_data': [{
                'name': self.input_name,
                'type': 'file',
                'required': True,
            }],
            'jobs': [{
                'name': 'Job 2',
                'job_type': {
                    'name': self.job_type_2.name,
                    'version': self.job_type_2.version,
                },
                'recipe_inputs': [{
                    'recipe_input': self.input_name,
                    'job_input': self.input_name,
                }],
            }, {
                'name': 'Job 1',
                'job_type': {
                    'name': self.job_type_1.name,
                    'version': self.job_type_1.version,
                },
                'dependencies': [{
                    'name': 'Job 2',
                    'connections': [{
                        'output': self.output_name,
                        'input': self.input_name,
                    }],
                }],
            }],
        }
        self.recipe_type_1 = recipe_test_utils.create_recipe_type_v5(definition=definition_1)

        self.file_name = 'my_file.txt'
        self.data_type = 'test_file_type'
        self.media_type = 'text/plain'

        self.workspace = storage_test_utils.create_workspace()
        self.source_file = ScaleFile.objects.create(file_name=self.file_name, file_type='SOURCE',
                                                    media_type=self.media_type, file_size=10, data_type=self.data_type,
                                                    file_path='the_path', workspace=self.workspace)
        self.source_file.add_data_type_tag('type1')
        self.source_file.add_data_type_tag('type2')
        self.source_file.add_data_type_tag('type3')

    def test_successful_job_creation(self):
        """Tests successfully processing an ingest that triggers job creation."""

        # Set up data
        configuration = {
            'version': '1.0',
            'condition': {
                'media_type': 'text/plain',
                'data_types': ['type1', 'type2'],
            },
            'data': {
                'input_data_name': self.input_name,
                'workspace_name': self.workspace.name
            },
        }
        rule_model = trigger_test_utils.create_trigger_rule(trigger_type='INGEST', configuration=configuration)
        self.job_type_1.trigger_rule = rule_model
        self.job_type_1.save()

        # Call method to test
        IngestTriggerHandler().process_ingested_source_file(self.source_file, now())

        # Check results
        queue_1 = Queue.objects.get(job_type=self.job_type_1.id)
        job_1 = Job.objects.get(id=queue_1.job_id)
        self.assertEqual(job_1.input['input_data'][0]['name'], self.input_name)
        self.assertEqual(job_1.input['input_data'][0]['file_id'], self.source_file.id)

    def test_successful_recipe_creation(self):
        """Tests successfully processing an ingest that triggers recipe creation."""

        # Set up data
        configuration = {
            'version': '1.0',
            'condition': {
                'media_type': 'text/plain',
            },
            'data': {
                'input_data_name': self.input_name,
                'workspace_name': self.workspace.name
            },
        }

        rule_model = trigger_test_utils.create_trigger_rule(trigger_type='INGEST', configuration=configuration)
        self.recipe_type_1.trigger_rule = rule_model
        self.recipe_type_1.save()

        # Call method to test
        IngestTriggerHandler().process_ingested_source_file(self.source_file, now())

        # Check results...ensure first job is queued
        queue_1 = Queue.objects.get(job_type=self.job_type_2.id)
        job_1 = Job.objects.get(id=queue_1.job_id)
        self.assertEqual(job_1.input['input_data'][0]['name'], self.input_name)
        self.assertEqual(job_1.input['input_data'][0]['file_id'], self.source_file.id)
        self.assertEqual(job_1.input['output_data'][0]['name'], self.output_name)
        self.assertEqual(job_1.input['output_data'][0]['workspace_id'], self.workspace.id)

    def test_successful_recipe_kickoff(self):
        """Tests successfully producing an ingest that immediately calls a recipe"""

        jt1 = job_test_utils.create_seed_job_type()
        jt2 = job_test_utils.create_seed_job_type()

        source_file = ScaleFile.objects.create(file_name='input_file', file_type='SOURCE',
                                               media_type='image/png', file_size=10, data_type='image_type',
                                                    file_path='the_path', workspace=self.workspace)

        recipe_type_def = {'version': '6',
                           'input': {'files': [{'name': 'INPUT_IMAGE',
                                                'media_types': ['image/png'],
                                                'required': True,
                                                'multiple': True}],
                                    'json': []},
                           'nodes': {'node_a': {'dependencies': [],
                                                'input': {'INPUT_IMAGE': {'type': 'recipe', 'input': 'INPUT_IMAGE'}},
                                                'node_type': {'node_type': 'job', 'job_type_name': jt1.name,
                                                              'job_type_version': jt1.version,
                                                              'job_type_revision': 1}},
                                     'node_b': {'dependencies': [{'name': 'node_a'}],
                                                'input': {'INPUT_IMAGE': {'type': 'dependency', 'node': 'node_a',
                                                                          'output': 'OUTPUT_IMAGE'}},
                                                'node_type': {'node_type': 'job', 'job_type_name': jt2.name,
                                                              'job_type_version': jt2.version,
                                                              'job_type_revision': 1}}}}

        recipe = recipe_test_utils.create_recipe_type_v6(name='test-recipe', definition=recipe_type_def)

        strike_config = {
            'version': '6',
            'workspace': self.workspace.name,
            'monitor': {'type': 'dir-watcher', 'transfer_suffix': '_tmp'},
            'files_to_ingest': [{
                'filename_regex': 'input_file',
                'data_types': ['image_type'],
                'new_workspace': self.workspace.name,
                'new_file_path': 'my/path'
            }],
            'recipe': {
                'name': 'test-recipe',
                'conditions':[{
                    'input_name': 'INPUT_IMAGE',
                    'media_types': ['image/png'],
                    'data_types': ['image_type'],
                    'not_data_types': [],
                }],
            },
        }

        config = StrikeConfigurationV6(strike_config).get_configuration()
        strike = Strike.objects.create_strike('my_name', 'my_title', 'my_description', config)

        ingest_recipe_config = {
            'name': recipe.name,
            'conditions': [{
               'input_name': 'INPUT_IMAGE',
               'media_types': ['image/png'],
               'data_types': ['image_type'],
               'not_data_types': [],
            }],
        }

        # Call method to test
        IngestTriggerHandler().kick_off_recipe_from_ingest(strike, source_file, ingest_recipe_config, now())
        import pdb; pdb.set_trace()

        # Verify first job in the recipe is queued
        queue_1 = Queue.objects.get(job_type=jt1.id)
        job = Job.objects.get(id=queue_1.job_id)
        self.assertEqual(job.input['input_data'][0]['name'], 'INPUT_IMAGE')
        self.assertEqual(job.input['input_data'][0]['file_id'], self.source_file.id)
