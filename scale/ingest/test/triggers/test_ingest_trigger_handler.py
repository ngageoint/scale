from __future__ import unicode_literals

import django
import os
from django.test import TransactionTestCase
from django.utils.timezone import now
from mock import patch

import job.test.utils as job_test_utils
import recipe.test.utils as recipe_test_utils
import storage.test.utils as storage_test_utils
import trigger.test.utils as trigger_test_utils
from ingest.triggers.ingest_trigger_handler import IngestTriggerHandler
from job.models import Job
from queue.models import Queue
from storage.models import ScaleFile


class TestIngestTriggerHandlerProcessIngestedSourceFile(TransactionTestCase):

    def setUp(self):
        django.setup()

        self.input_name = 'Test_Input'
        self.output_name = 'Test_Output'

        manifest = {
            'seedVersion': '1.0.0',
            'job': {
                'name': 'test-job',
                'jobVersion': '0.1.0',
                'packageVersion': '0.1.0',
                'title': 'Test Job',
                'description': 'Test Job',
                'maintainer': {
                    'name': 'John Doe',
                    'email': 'jdoe@example.com'
                },
                'timeout': 30,
                'interface': {
                    'command': 'my_cmd args',
                    'inputs': {
                        'files': [{'name': self.input_name, 'mediaTypes': ['text/plain'], 'required': True}]
                    }
                }
            }
        }
        self.job_type_1 = job_test_utils.create_seed_job_type(manifest=manifest)

        manifest_2 = {
            'seedVersion': '1.0.0',
            'job': {
                'name': 'test-job-2',
                'jobVersion': '1.0.0',
                'packageVersion': '1.0.0',
                'title': 'Test Job 2',
                'description': 'Test Job',
                'maintainer': {
                    'name': 'John Doe',
                    'email': 'jdoe@example.com'
                },
                'timeout': 30,
                'interface': {
                    'command': 'my_cmd args',
                    'inputs': {
                        'files': [{'name': self.input_name, 'mediaTypes': ['text/plain'], 'required': True}]
                    },
                    'outputs': {
                        'files': [{'name': self.output_name, 'pattern': '*_.txt', 'mediaType': 'text/plain'}]
                    },
                }
            }
        }
        self.job_type_2 = job_test_utils.create_seed_job_type(manifest=manifest_2)

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
        definition_1 = {
            'version': '6',
            'input': {'files': [{'name': self.input_name, 'media_types': ['text/plain'], 'required': True, 'multiple': False}],
                      'json': []},
            'nodes': {
                'job_a': {
                    'dependencies': [],
                    'input': {self.input_name: {'type': 'recipe', 'input': self.input_name}},
                    'node_type': {
                        'node_type': 'job',
                        'job_type_name': self.job_type_2.name,
                        'job_type_version': self.job_type_2.version,
                        'job_type_revision': 1,
                    }
                },
                'job_b': {
                    'dependencies': [],
                    'input': {self.input_name: {'type': 'dependency', 'node': 'job_a', 'output': self.output_name}},
                    'node_type': {
                        'node_type': 'job',
                        'job_type_name': self.job_type_1.name,
                        'job_type_version': self.job_type_1.version,
                        'job_type_revision': 1,
                    }
                }
            }
        }
        self.recipe_type_1 = recipe_test_utils.create_recipe_type_v6(definition=definition_1)

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

        # Since we're using the messaging backend, how do we make sure the first job is queued????

        # Check results...ensure first job is queued
        queue_1 = Queue.objects.get(job_type=self.job_type_2.id)
        job_1 = Job.objects.get(id=queue_1.job_id)
        self.assertEqual(job_1.input['input_data'][0]['name'], self.input_name)
        self.assertEqual(job_1.input['input_data'][0]['file_id'], self.source_file.id)
        self.assertEqual(job_1.input['output_data'][0]['name'], self.output_name)
        self.assertEqual(job_1.input['output_data'][0]['workspace_id'], self.workspace.id)
