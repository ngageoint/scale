from __future__ import unicode_literals
from __future__ import absolute_import

import django
from django.test import TransactionTestCase

from data.data.json.data_v6 import DataV6
from data.interface.interface import Interface
from job.messages.process_job_input import ProcessJobInput
from job.models import Job, JobInputFile
from job.test import utils as job_test_utils
from storage.test import utils as storage_test_utils


class TestProcessJobInput(TransactionTestCase):

    def setUp(self):
        django.setup()

    def test_json(self):
        """Tests converting a ProcessJobInput message to and from JSON"""

        job = job_test_utils.create_job(num_exes=0, status='PENDING', input_file_size=None, input=DataV6().get_dict())

        # Create message
        message = ProcessJobInput()
        message.job_id = job.id

        # Convert message to JSON and back, and then execute
        message_json_dict = message.to_json()
        new_message = ProcessJobInput.from_json(message_json_dict)
        result = new_message.execute()

        self.assertTrue(result)
        job = Job.objects.get(id=job.id)
        self.assertEqual(len(new_message.new_messages), 1)
        self.assertEqual(new_message.new_messages[0].type, 'queued_jobs')
        self.assertFalse(new_message.new_messages[0].requeue)
        # Job should have input_file_size set to 0 (no input files)
        self.assertEqual(job.input_file_size, 0.0)

    def test_execute_with_data(self):
        """Tests calling ProcessJobInput.execute() successfully when the job already has data populated"""

        workspace = storage_test_utils.create_workspace()
        file_1 = storage_test_utils.create_file(workspace=workspace, file_size=104857600.0)
        file_2 = storage_test_utils.create_file(workspace=workspace, file_size=987654321.0)
        interface = {
            'version': '1.0',
            'command': 'my_command',
            'command_arguments': 'args',
            'input_data': [{
                'name': 'Input 1',
                'type': 'file',
                'media_types': ['text/plain'],
            }, {
                'name': 'Input 2',
                'type': 'file',
                'media_types': ['text/plain'],
            }],
            'output_data': [{
                'name': 'Output 1',
                'type': 'files',
                'media_type': 'image/png',
            }]}
        job_type = job_test_utils.create_job_type(interface=interface)

        input_dict = {
            'version': '1.0',
            'input_data': [{
                'name': 'Input 1',
                'file_id': file_1.id
            }, {
                'name': 'Input 2',
                'file_id': file_2.id
            }],
            'output_data': [{
                'name': 'Output 1',
                'workspace_id': workspace.id
            }]}

        job = job_test_utils.create_job(job_type=job_type, num_exes=0, status='PENDING', input_file_size=None,
                                        input=input_dict)

        # Create message
        message = ProcessJobInput()
        message.job_id = job.id

        # Execute message
        result = message.execute()
        self.assertTrue(result)

        job = Job.objects.get(id=job.id)
        # Check for queued jobs message
        self.assertEqual(len(message.new_messages), 1)
        self.assertEqual(message.new_messages[0].type, 'queued_jobs')
        self.assertFalse(message.new_messages[0].requeue)

        # Check job for expected input_file_size
        self.assertEqual(job.input_file_size, 1042.0)

        # Make sure job input file models are created
        job_input_files = JobInputFile.objects.filter(job_id=job.id)
        self.assertEqual(len(job_input_files), 2)
        for job_input_file in job_input_files:
            if job_input_file.job_input == 'Input 1':
                self.assertEqual(job_input_file.input_file_id, file_1.id)
            elif job_input_file.job_input == 'Input 2':
                self.assertEqual(job_input_file.input_file_id, file_2.id)
            else:
                self.fail('Invalid input name: %s' % job_input_file.job_input)

        # Test executing message again
        message_json_dict = message.to_json()
        message = ProcessJobInput.from_json(message_json_dict)
        result = message.execute()
        self.assertTrue(result)

        # Still should have queued jobs message
        self.assertEqual(len(message.new_messages), 1)
        self.assertEqual(message.new_messages[0].type, 'queued_jobs')
        self.assertFalse(message.new_messages[0].requeue)

        # Make sure job input file models are unchanged
        job_input_files = JobInputFile.objects.filter(job_id=job.id)
        self.assertEqual(len(job_input_files), 2)

    def test_execute_with_recipe_legacy(self):
        """Tests calling ProcessJobInput.execute() successfully when a legacy job has to get its data from its recipe"""

        workspace = storage_test_utils.create_workspace()
        file_1 = storage_test_utils.create_file(workspace=workspace, file_size=104857600.0)
        file_2 = storage_test_utils.create_file(workspace=workspace, file_size=987654321.0)
        file_3 = storage_test_utils.create_file(workspace=workspace, file_size=65456.0)
        file_4 = storage_test_utils.create_file(workspace=workspace, file_size=24564165456.0)
        interface_1 = {
            'version': '1.0',
            'command': 'my_command',
            'command_arguments': 'args',
            'input_data': [],
            'output_data': [{
                'name': 'Output 1',
                'type': 'files',
                'media_type': 'image/png',
            }]}
        job_type_1 = job_test_utils.create_job_type(interface=interface_1)
        interface_2 = {
            'version': '1.0',
            'command': 'my_command',
            'command_arguments': 'args',
            'input_data': [{
                'name': 'Input 1',
                'type': 'files',
                'media_types': ['image/png'],
            }],
            'output_data': [{
                'name': 'New Output 1',
                'type': 'files',
                'media_type': 'image/png',
            }]
        }
        job_type_2 = job_test_utils.create_job_type(interface=interface_2)
        output_dict = {
            'version': '1.0',
            'output_data': [{
                'name': 'Output 1',
                'file_ids': [file_1.id, file_2.id, file_3.id, file_4.id]
            }]
        }
        job_1 = job_test_utils.create_job(job_type=job_type_1, num_exes=1, status='COMPLETED', output=output_dict)
        job_2 = job_test_utils.create_job(job_type=job_type_2, num_exes=0, status='PENDING', input_file_size=None,
                                          input=None)

        from recipe.definition.definition import RecipeDefinition
        from recipe.definition.json.definition_v1 import convert_recipe_definition_to_v1_json
        from recipe.test import utils as recipe_test_utils
        definition = RecipeDefinition(Interface())
        definition.add_job_node('node_a', job_type_1.name, job_type_1.version, job_type_1.revision_num)
        definition.add_job_node('node_b', job_type_2.name, job_type_2.version, job_type_2.revision_num)
        definition.add_dependency('node_b', 'node_a')
        definition.add_dependency_input_connection('node_b', 'Input 1', 'node_a', 'Output 1')
        def_dict = convert_recipe_definition_to_v1_json(definition).get_dict()
        recipe_type = recipe_test_utils.create_recipe_type(definition=def_dict)
        recipe_data_dict = {'version': '1.0', 'input_data': [], 'workspace_id': workspace.id}
        recipe = recipe_test_utils.create_recipe(recipe_type=recipe_type, input=recipe_data_dict)
        recipe_test_utils.create_recipe_job(recipe=recipe, job_name='node_a', job=job_1)
        recipe_test_utils.create_recipe_job(recipe=recipe, job_name='node_b', job=job_2)
        job_1.recipe = recipe
        job_1.save()
        job_2.recipe = recipe
        job_2.save()

        # Create message
        message = ProcessJobInput()
        message.job_id = job_2.id

        # Execute message
        result = message.execute()
        self.assertTrue(result)

        job_2 = Job.objects.get(id=job_2.id)
        # Check for queued jobs message
        self.assertEqual(len(message.new_messages), 1)
        self.assertEqual(message.new_messages[0].type, 'queued_jobs')
        self.assertFalse(message.new_messages[0].requeue)

        # Check job for expected input_file_size
        self.assertEqual(job_2.input_file_size, 24469.0)
        # Check job for expected output workspaces in job input data (legacy)
        self.assertDictEqual(job_2.input, {'version': '1.0',
                                           'input_data': [{'name': 'Input 1',
                                                           'file_ids': [file_1.id, file_2.id, file_3.id, file_4.id]}],
                                           'output_data': [{'name': 'New Output 1', 'workspace_id': workspace.id}]})

        # Make sure job input file models are created
        job_input_files = JobInputFile.objects.filter(job_id=job_2.id)
        self.assertEqual(len(job_input_files), 4)
        file_ids = set()
        for job_input_file in job_input_files:
            self.assertEqual(job_input_file.job_input, 'Input 1')
            file_ids.add(job_input_file.input_file_id)
        self.assertSetEqual(file_ids, {file_1.id, file_2.id, file_3.id, file_4.id})

        # Test executing message again
        message_json_dict = message.to_json()
        message = ProcessJobInput.from_json(message_json_dict)
        result = message.execute()
        self.assertTrue(result)

        # Still should have queued jobs message
        self.assertEqual(len(message.new_messages), 1)
        self.assertEqual(message.new_messages[0].type, 'queued_jobs')
        self.assertFalse(message.new_messages[0].requeue)

        # Make sure job input file models are unchanged
        job_input_files = JobInputFile.objects.filter(job_id=job_2.id)
        self.assertEqual(len(job_input_files), 4)

    def test_execute_with_recipe(self):
        """Tests calling ProcessJobInput.execute() successfully when a job has to get its data from its recipe"""

        workspace = storage_test_utils.create_workspace()
        file_1 = storage_test_utils.create_file(workspace=workspace, file_size=104857600.0)
        file_2 = storage_test_utils.create_file(workspace=workspace, file_size=987654321.0)
        file_3 = storage_test_utils.create_file(workspace=workspace, file_size=65456.0)
        file_4 = storage_test_utils.create_file(workspace=workspace, file_size=24564165456.0)
        manifest_1 = {
            'seedVersion': '1.0.0',
            'job': {
                'name': 'job-a',
                'jobVersion': '1.0.0',
                'packageVersion': '1.0.0',
                'title': '',
                'description': '',
                'maintainer': {
                    'name': 'John Doe',
                    'email': 'jdoe@example.com'
                },
                'timeout': 10,
                'interface': {
                    'command': '',
                    'inputs': {'files': [], 'json': []},
                    'outputs': {
                        'files': [{'name': 'OUTPUT_A', 'pattern': '*.png'}]
                    }
                }
            }
        }
        job_type_1 = job_test_utils.create_job_type(interface=manifest_1)
        manifest_2 = {
            'seedVersion': '1.0.0',
            'job': {
                'name': 'job-b',
                'jobVersion': '1.0.0',
                'packageVersion': '1.0.0',
                'title': '',
                'description': '',
                'maintainer': {
                    'name': 'John Doe',
                    'email': 'jdoe@example.com'
                },
                'timeout': 10,
                'interface': {
                    'command': '',
                    'inputs': {'files': [{'name': 'INPUT_B', 'multiple': True}]},
                    'outputs': {
                        'files': [{'name': 'OUTPUT_B', 'pattern': '*.png'}]
                    }
                }
            }
        }
        job_type_2 = job_test_utils.create_job_type(interface=manifest_2)
        output_dict = {
            'version': '1.0',
            'output_data': [{
                'name': 'OUTPUT_A',
                'file_ids': [file_1.id, file_2.id, file_3.id, file_4.id]
            }]
        }
        job_1 = job_test_utils.create_job(job_type=job_type_1, num_exes=1, status='COMPLETED', output=output_dict)
        job_2 = job_test_utils.create_job(job_type=job_type_2, num_exes=0, status='PENDING', input_file_size=None,
                                          input=None)

        from recipe.definition.definition import RecipeDefinition
        from recipe.definition.json.definition_v1 import convert_recipe_definition_to_v1_json
        from recipe.test import utils as recipe_test_utils
        definition = RecipeDefinition(Interface())
        definition.add_job_node('node_a', job_type_1.name, job_type_1.version, job_type_1.revision_num)
        definition.add_job_node('node_b', job_type_2.name, job_type_2.version, job_type_2.revision_num)
        definition.add_dependency('node_b', 'node_a')
        definition.add_dependency_input_connection('node_b', 'INPUT_B', 'node_a', 'OUTPUT_A')
        def_dict = convert_recipe_definition_to_v1_json(definition).get_dict()
        recipe_type = recipe_test_utils.create_recipe_type(definition=def_dict)
        recipe_data_dict = {'version': '1.0', 'input_data': [], 'workspace_id': workspace.id}
        recipe = recipe_test_utils.create_recipe(recipe_type=recipe_type, input=recipe_data_dict)
        recipe_test_utils.create_recipe_job(recipe=recipe, job_name='node_a', job=job_1)
        recipe_test_utils.create_recipe_job(recipe=recipe, job_name='node_b', job=job_2)
        job_1.recipe = recipe
        job_1.save()
        job_2.recipe = recipe
        job_2.save()

        # Create message
        message = ProcessJobInput()
        message.job_id = job_2.id

        # Execute message
        result = message.execute()
        self.assertTrue(result)

        job_2 = Job.objects.get(id=job_2.id)
        # Check for queued jobs message
        self.assertEqual(len(message.new_messages), 1)
        self.assertEqual(message.new_messages[0].type, 'queued_jobs')
        self.assertFalse(message.new_messages[0].requeue)

        # Check job for expected input_file_size
        self.assertEqual(job_2.input_file_size, 24469.0)
        # Check job for expected input data
        self.assertSetEqual(set(job_2.get_input_data().values.keys()), {'INPUT_B'})
        self.assertListEqual(job_2.get_input_data().values['INPUT_B'].file_ids,
                             [file_1.id, file_2.id, file_3.id, file_4.id])

        # Make sure job input file models are created
        job_input_files = JobInputFile.objects.filter(job_id=job_2.id)
        self.assertEqual(len(job_input_files), 4)
        file_ids = set()
        for job_input_file in job_input_files:
            self.assertEqual(job_input_file.job_input, 'INPUT_B')
            file_ids.add(job_input_file.input_file_id)
        self.assertSetEqual(file_ids, {file_1.id, file_2.id, file_3.id, file_4.id})

        # Test executing message again
        message_json_dict = message.to_json()
        message = ProcessJobInput.from_json(message_json_dict)
        result = message.execute()
        self.assertTrue(result)

        # Still should have queued jobs message
        self.assertEqual(len(message.new_messages), 1)
        self.assertEqual(message.new_messages[0].type, 'queued_jobs')
        self.assertFalse(message.new_messages[0].requeue)

        # Make sure job input file models are unchanged
        job_input_files = JobInputFile.objects.filter(job_id=job_2.id)
        self.assertEqual(len(job_input_files), 4)
