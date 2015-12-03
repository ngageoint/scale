#PydevCodeAnalysisIgnore
from __future__ import unicode_literals

import django
from django.test import TestCase
from django.utils.timezone import now

import job.test.utils as job_test_utils
import recipe.test.utils as recipe_test_utils
import storage.test.utils as storage_test_utils
from job.models import JobType
from job.models import JobExecution
from queue.models import Queue
from recipe.models import RecipeType
from recipe.test import utils as recipe_utils
from source.models import SourceFile
from source.triggers.parse_rule import ParseTriggerRule
from storage.models import Workspace
from trigger.exceptions import InvalidTriggerRule
from trigger.models import TriggerEvent


class TestParseTriggerRuleInit(TestCase):

    def setUp(self):
        django.setup()

        self.job_type1 = job_test_utils.create_job_type()
        self.recipe_type1 = recipe_test_utils.create_recipe_type()
        self.workspace1 = storage_test_utils.create_workspace()

    def test_init_blank(self):
        '''Tests calling ParseTriggerRule constructor with blank JSON.'''

        # No exception is success
        ParseTriggerRule({})

    def test_init_bad_version(self):
        '''Tests calling ParseTriggerRule constructor with bad version number.'''

        config = {
            'version': 'BAD VERSION',
        }
        self.assertRaises(InvalidTriggerRule, ParseTriggerRule, config)

    def test_init_media_type_wrong_type(self):
        '''Tests calling ParseTriggerRule constructor with a non-string media_type.'''

        config = {
            'trigger': {
                'media_type': 1234,
            },
        }
        self.assertRaises(InvalidTriggerRule, ParseTriggerRule, config)

    def test_init_data_typers_wrong_type(self):
        '''Tests calling ParseTriggerRule constructor with a non-list data_types.'''

        config = {
            'trigger': {
                'data_types': 1234,
            },
        }
        self.assertRaises(InvalidTriggerRule, ParseTriggerRule, config)

    def test_init_data_types_empty(self):
        '''Tests calling IngestTriggerRule constructor with no data_types.'''

        config = {
            'trigger': {
                'data_types': [],
            },
        }
        # No exception is success
        ParseTriggerRule(config)

    def test_init_job_missing_type(self):
        '''Tests calling ParseTriggerRule constructor with a job missing its job_type field.'''

        config = {
            'create': {
                'jobs': [{
                    'file_input_name': 'name',
                    'workspace_name': self.workspace1.name,
                }],
            },
        }
        self.assertRaises(InvalidTriggerRule, ParseTriggerRule, config)

    def test_init_job_wrong_type(self):
        '''Tests calling ParseTriggerRule constructor with a non-object job_type field.'''

        config = {
            'create': {
                'jobs': [{
                    'job_type': 'BAD',
                    'file_input_name': 'name',
                    'workspace_name': self.workspace1.name,
                },
            ]},
        }
        self.assertRaises(InvalidTriggerRule, ParseTriggerRule, config)

    def test_init_job_missing_file_input_name(self):
        '''Tests calling ParseTriggerRule constructor with a job missing its file_input_name field.'''

        config = {
            'create': {
                'jobs': [{
                    'job_type': {
                        'name': self.job_type1.name,
                        'version': self.job_type1.version,
                    },
                    'workspace_name': self.workspace1.name,
                }],
            },
        }
        self.assertRaises(InvalidTriggerRule, ParseTriggerRule, config)

    def test_init_file_input_name_wrong_type(self):
        '''Tests calling ParseTriggerRule constructor with a non-string file_input_name field.'''

        config = {
            'create': {
                'jobs': [{
                    'job_type': {
                        'name': self.job_type1.name,
                        'version': self.job_type1.version,
                    },
                    'file_input_name': 999,
                    'workspace_name': self.workspace1.name,
                }],
            },
        }
        self.assertRaises(InvalidTriggerRule, ParseTriggerRule, config)

    def test_init_workspace_name_wrong_type(self):
        '''Tests calling ParseTriggerRule constructor with a non-string workspace_name field.'''

        config = {
            'create': {
                'jobs': [{
                    'job_type': {
                        'name': self.job_type1.name,
                        'version': self.job_type1.version,
                    },
                    'file_input_name': 'name',
                    'workspace_name': 1234,
                }],
            },
        }
        self.assertRaises(InvalidTriggerRule, ParseTriggerRule, config)

    def test_init_successful_one_job_workspace(self):
        '''Tests calling ParseTriggerRule constructor successfully with one job with a workspace.'''

        config = {
            'create': {
                'jobs': [{
                    'job_type': {
                        'name': self.job_type1.name,
                        'version': self.job_type1.version,
                    },
                    'file_input_name': 'name',
                    'workspace_name': self.workspace1.name,
                }],
            },
        }
        # No exception is success
        ParseTriggerRule(config)

    def test_init_successful_one_job_no_workspace(self):
        '''Tests calling ParseTriggerRule constructor successfully with one job without a workspace.'''

        config = {
            'create': {
                'jobs': [{
                    'job_type': {
                        'name': self.job_type1.name,
                        'version': self.job_type1.version,
                    },
                    'file_input_name': 'name',
                }],
            },
        }
        # No exception is success
        ParseTriggerRule(config)

    def test_init_recipe_missing_type(self):
        '''Tests calling ParseTriggerRule constructor with a recipe missing its recipe_type field.'''

        config = {
            'create': {
                'recipes': [{
                    'file_input_name': 'name',
                    'workspace_name': self.workspace1.name,
                }],
            },
        }
        self.assertRaises(InvalidTriggerRule, ParseTriggerRule, config)

    def test_init_recipe_wrong_type(self):
        '''Tests calling ParseTriggerRule constructor with a non-object recipe_type field.'''

        config = {
            'create': {
                'recipes': [{
                    'recipe_type': 'BAD',
                    'file_input_name': 'name',
                    'workspace_name': self.workspace1.name,
                }],
            },
        }
        self.assertRaises(InvalidTriggerRule, ParseTriggerRule, config)

    def test_init_recipe_missing_file_input_name(self):
        '''Tests calling ParseTriggerRule constructor with a recipe missing its file_input_name field.'''

        config = {
            'create': {
                'recipes': [{
                    'recipe_type': {
                        'name': self.recipe_type1.name,
                        'version': self.recipe_type1.version,
                    },
                    'workspace_name': self.workspace1.name,
                }],
            },
        }
        self.assertRaises(InvalidTriggerRule, ParseTriggerRule, config)

    def test_init_recipe_file_input_name_wrong_type(self):
        '''Tests calling ParseTriggerRule constructor with a non-string file_input_name field.'''

        config = {
            'create': {
                'recipes': [{
                    'recipe_type': {
                        'name': self.recipe_type1.name,
                        'version': self.recipe_type1.version,
                    },
                    'file_input_name': 999,
                    'workspace_name': self.workspace1.name,
                }],
            },
        }
        self.assertRaises(InvalidTriggerRule, ParseTriggerRule, config)

    def test_init_recipe_workspace_name_wrong_type(self):
        '''Tests calling ParseTriggerRule constructor with a non-string workspace_name field.'''

        config = {
            'create': {
                'recipes': [{
                    'recipe_type': {
                        'name': self.recipe_type1.name,
                        'version': self.recipe_type1.version,
                    },
                    'file_input_name': 'name',
                    'workspace_name': 1234,
                }],
            },
        }
        self.assertRaises(InvalidTriggerRule, ParseTriggerRule, config)

    def test_init_successful_one_recipe_workspace(self):
        '''Tests calling ParseTriggerRule constructor successfully with one recipe with a workspace.'''

        config = {
            'create': {
                'recipes': [{
                    'recipe_type': {
                        'name': self.recipe_type1.name,
                        'version': self.recipe_type1.version,
                    },
                    'file_input_name': 'name',
                    'workspace_name': self.workspace1.name,
                }],
            },
        }
        # No exception is success
        ParseTriggerRule(config)

    def test_init_successful_one_recipe_no_workspace(self):
        '''Tests calling ParseTriggerRule constructor successfully with one recipe without a workspace.'''

        config = {
            'create': {
                'recipes': [{
                    'recipe_type': {
                        'name': self.recipe_type1.name,
                        'version': self.recipe_type1.version,
                    },
                    'file_input_name': 'name',
                }],
            },
        }
        # No exception is success
        ParseTriggerRule(config)


class TestParseTriggerRuleProcessParse(TestCase):

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
        self.recipe_type_1 = recipe_test_utils.create_recipe_type(definition=definition_1)

        self.when_parsed = now()
        self.file_name = 'my_file.txt'
        self.data_type = 'test_file_type'
        self.media_type = 'text/plain'

        self.workspace = storage_test_utils.create_workspace()
        self.source_file = SourceFile.objects.create(file_name=self.file_name, media_type=self.media_type, file_size=10,
                                                     data_type=self.data_type, file_path='the_path',
                                                     workspace=self.workspace)
        self.source_file.add_data_type_tag('type1')
        self.source_file.add_data_type_tag('type2')
        self.source_file.add_data_type_tag('type3')
        self.source_file.parsed = now()

    def test_successful_job_creation(self):
        '''Tests successfully processing a parse that triggers job creation.'''

        # Set up data
        configuration = {
            'version': '1.0',
            'trigger': {
                'media_type': 'text/plain',
                'data_types': ['type1', 'type2'],
            },
            'create': {
                'jobs': [{
                    'job_type': {
                        'name': self.job_type_1.name,
                        'version': self.job_type_1.version,
                    },
                    'file_input_name': self.input_name,
                }, {
                    'job_type': {
                        'name': self.job_type_2.name,
                        'version': self.job_type_2.version,
                    },
                    'file_input_name': self.input_name,
                    'workspace_name': self.workspace.name,
                }],
            },
        }
        rule = ParseTriggerRule(configuration)
        rule.save_to_db()

        # Call method to test
        rule.process_parse(self.source_file)

        # Check results
        queue_1 = Queue.objects.get(job_type=self.job_type_1.id)
        job_exe_1 = JobExecution.objects.select_related().get(pk=queue_1.job_exe_id)
        job_1 = job_exe_1.job
        self.assertEqual(job_1.data['input_data'][0]['name'], self.input_name)
        self.assertEqual(job_1.data['input_data'][0]['file_id'], self.source_file.id)

        queue_2 = Queue.objects.get(job_type=self.job_type_2.id)
        job_exe_2 = JobExecution.objects.select_related().get(pk=queue_2.job_exe_id)
        job_2 = job_exe_2.job
        self.assertEqual(job_2.data['input_data'][0]['name'], self.input_name)
        self.assertEqual(job_2.data['input_data'][0]['file_id'], self.source_file.id)
        self.assertEqual(job_2.data['output_data'][0]['name'], self.output_name)
        self.assertEqual(job_2.data['output_data'][0]['workspace_id'], self.workspace.id)

    def test_successful_recipe_creation(self):
        '''Tests successfully processing a parse that triggers recipe creation.'''

        # Set up data
        configuration = {
            'version': '1.0',
            'trigger': {
                'media_type': 'text/plain',
            },
            'create': {
                'recipes': [{
                    'recipe_type': {
                        'name': self.recipe_type_1.name,
                        'version': self.recipe_type_1.version,
                    },
                    'file_input_name': self.input_name,
                    'workspace_name': self.workspace.name,
                }],
            },
        }
        rule = ParseTriggerRule(configuration)
        rule.save_to_db()

        # Call method to test
        rule.process_parse(self.source_file)

        # Check results...ensure first job is queued
        queue_1 = Queue.objects.get(job_type=self.job_type_2.id)
        job_exe_1 = JobExecution.objects.select_related().get(pk=queue_1.job_exe_id)
        job_1 = job_exe_1.job
        self.assertEqual(job_1.data['input_data'][0]['name'], self.input_name)
        self.assertEqual(job_1.data['input_data'][0]['file_id'], self.source_file.id)
        self.assertEqual(job_1.data['output_data'][0]['name'], self.output_name)
        self.assertEqual(job_1.data['output_data'][0]['workspace_id'], self.workspace.id)
