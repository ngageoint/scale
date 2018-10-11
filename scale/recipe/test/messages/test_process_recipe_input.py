from __future__ import unicode_literals
from __future__ import absolute_import

import django
from django.test import TransactionTestCase

from data.data.data import Data
from data.data.json.data_v6 import convert_data_to_v6_json
from data.data.value import FileValue, JsonValue
from data.interface.interface import Interface
from data.interface.parameter import FileParameter, JsonParameter
from job.test import utils as job_test_utils
from recipe.definition.definition import RecipeDefinition
from recipe.definition.json.definition_v1 import convert_recipe_definition_to_v1_json
from recipe.definition.json.definition_v6 import convert_recipe_definition_to_v6_json
from recipe.diff.forced_nodes import ForcedNodes
from recipe.diff.json.forced_nodes_v6 import convert_forced_nodes_to_v6
from recipe.messages.process_recipe_input import create_process_recipe_input_messages, ProcessRecipeInput
from recipe.models import Recipe, RecipeInputFile, RecipeNode
from recipe.test import utils as recipe_test_utils
from storage.test import utils as storage_test_utils


class TestProcessRecipeInput(TransactionTestCase):

    def setUp(self):
        django.setup()

    def test_json(self):
        """Tests coverting a ProcessRecipeInput message to and from JSON"""

        data_dict = convert_data_to_v6_json(Data()).get_dict()
        recipe = recipe_test_utils.create_recipe(input=data_dict)

        # Create message
        message = ProcessRecipeInput()
        message.recipe_id = recipe.id

        # Convert message to JSON and back, and then execute
        message_json_dict = message.to_json()
        new_message = ProcessRecipeInput.from_json(message_json_dict)
        result = new_message.execute()

        self.assertTrue(result)
        recipe = Recipe.objects.get(id=recipe.id)
        self.assertEqual(len(new_message.new_messages), 1)
        self.assertEqual(new_message.new_messages[0].type, 'update_recipe')
        self.assertEqual(new_message.new_messages[0].root_recipe_id, recipe.id)
        # Recipe should have input_file_size set to 0 (no input files)
        self.assertEqual(recipe.input_file_size, 0.0)

    def test_json_forced_nodes(self):
        """Tests coverting a ProcessRecipeInput message to and from JSON with forced nodes provided"""

        data_dict = convert_data_to_v6_json(Data()).get_dict()
        recipe = recipe_test_utils.create_recipe(input=data_dict)
        forced_nodes = ForcedNodes()
        forced_nodes.set_all_nodes()
        forced_nodes_dict = convert_forced_nodes_to_v6(forced_nodes).get_dict()

        # Create message
        message = create_process_recipe_input_messages([recipe.id], forced_nodes=forced_nodes)[0]

        # Convert message to JSON and back, and then execute
        message_json_dict = message.to_json()
        new_message = ProcessRecipeInput.from_json(message_json_dict)
        result = new_message.execute()

        self.assertTrue(result)
        recipe = Recipe.objects.get(id=recipe.id)
        self.assertEqual(len(new_message.new_messages), 1)
        msg = new_message.new_messages[0]
        self.assertEqual(msg.type, 'update_recipe')
        self.assertEqual(msg.root_recipe_id, recipe.id)
        self.assertDictEqual(convert_forced_nodes_to_v6(msg.forced_nodes).get_dict(), forced_nodes_dict)
        # Recipe should have input_file_size set to 0 (no input files)
        self.assertEqual(recipe.input_file_size, 0.0)

    def test_execute_with_data(self):
        """Tests calling ProcessRecipeInput.execute() successfully when the recipe already has data populated"""

        workspace = storage_test_utils.create_workspace()
        file_1 = storage_test_utils.create_file(workspace=workspace, file_size=10485760.0)
        file_2 = storage_test_utils.create_file(workspace=workspace, file_size=104857600.0)
        file_3 = storage_test_utils.create_file(workspace=workspace, file_size=987654321.0)
        recipe_interface = Interface()
        recipe_interface.add_parameter(FileParameter('input_a', ['text/plain']))
        recipe_interface.add_parameter(FileParameter('input_b', ['text/plain'], multiple=True))
        definition = RecipeDefinition(recipe_interface)
        definition_dict = convert_recipe_definition_to_v6_json(definition).get_dict()
        recipe_type = recipe_test_utils.create_recipe_type(definition=definition_dict)

        data = Data()
        data.add_value(FileValue('input_a', [file_1.id]))
        data.add_value(FileValue('input_b', [file_2.id, file_3.id]))
        data_dict = convert_data_to_v6_json(data).get_dict()
        recipe = recipe_test_utils.create_recipe(recipe_type=recipe_type, input=data_dict)

        # Create message
        message = ProcessRecipeInput()
        message.recipe_id = recipe.id

        # Execute message
        result = message.execute()
        self.assertTrue(result)

        recipe = Recipe.objects.get(id=recipe.id)
        # Check for update_recipe message
        self.assertEqual(len(message.new_messages), 1)
        self.assertEqual(message.new_messages[0].type, 'update_recipe')
        self.assertEqual(message.new_messages[0].root_recipe_id, recipe.id)

        # Check recipe for expected input_file_size
        self.assertEqual(recipe.input_file_size, 1052.0)

        # Make sure recipe input file models are created
        recipe_input_files = RecipeInputFile.objects.filter(recipe_id=recipe.id)
        self.assertEqual(len(recipe_input_files), 3)
        for recipe_input_file in recipe_input_files:
            if recipe_input_file.input_file_id == file_1.id:
                self.assertEqual(recipe_input_file.recipe_input, 'input_a')
            elif recipe_input_file.input_file_id == file_2.id:
                self.assertEqual(recipe_input_file.recipe_input, 'input_b')
            elif recipe_input_file.input_file_id == file_3.id:
                self.assertEqual(recipe_input_file.recipe_input, 'input_b')
            else:
                self.fail('Invalid input file ID: %s' % recipe_input_file.input_file_id)

        # Test executing message again
        message_json_dict = message.to_json()
        message = ProcessRecipeInput.from_json(message_json_dict)
        result = message.execute()
        self.assertTrue(result)

        # Still should have update_recipe message
        self.assertEqual(len(message.new_messages), 1)
        self.assertEqual(message.new_messages[0].type, 'update_recipe')

        # Make sure recipe input file models are unchanged
        recipe_input_files = RecipeInputFile.objects.filter(recipe_id=recipe.id)
        self.assertEqual(len(recipe_input_files), 3)

    def test_execute_with_recipe(self):
        """Tests calling ProcessRecipeInput.execute() successfully when a sub-recipe has to get its data from its
        recipe
        """

        workspace = storage_test_utils.create_workspace()
        file_1 = storage_test_utils.create_file(workspace=workspace, file_size=104857600.0)
        file_2 = storage_test_utils.create_file(workspace=workspace, file_size=987654321.0)
        file_3 = storage_test_utils.create_file(workspace=workspace, file_size=65456.0)
        file_4 = storage_test_utils.create_file(workspace=workspace, file_size=24564165456.0)
        manifest_a = {
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
                        'files': [{'name': 'output_a', 'pattern': '*.png'}]
                    }
                }
            }
        }
        job_type_a = job_test_utils.create_job_type(interface=manifest_a)
        output_data_a = Data()
        output_data_a.add_value(FileValue('output_a', [file_1.id]))
        output_data_a_dict = convert_data_to_v6_json(output_data_a).get_dict()
        manifest_b = {
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
                    'inputs': {'files': [], 'json': []},
                    'outputs': {
                        'files': [{'name': 'output_b', 'pattern': '*.png', 'multiple': True}]
                    }
                }
            }
        }
        job_type_b = job_test_utils.create_job_type(interface=manifest_b)
        output_data_b = Data()
        output_data_b.add_value(FileValue('output_b', [file_2.id, file_3.id, file_4.id]))
        output_data_b_dict = convert_data_to_v6_json(output_data_b).get_dict()
        job_a = job_test_utils.create_job(job_type=job_type_a, num_exes=1, status='COMPLETED',
                                          output=output_data_a_dict)
        job_b = job_test_utils.create_job(job_type=job_type_b, num_exes=1, status='COMPLETED',
                                          output=output_data_b_dict)
        sub_recipe_interface_c = Interface()
        sub_recipe_interface_c.add_parameter(FileParameter('input_a', ['image/png']))
        sub_recipe_interface_c.add_parameter(FileParameter('input_b', ['image/png'], multiple=True))
        sub_recipe_interface_c.add_parameter(JsonParameter('input_c', 'string'))
        sub_recipe_def_c = RecipeDefinition(sub_recipe_interface_c)
        sub_recipe_def_dict_c = convert_recipe_definition_to_v6_json(sub_recipe_def_c).get_dict()
        sub_recipe_type_c = recipe_test_utils.create_recipe_type(definition=sub_recipe_def_dict_c)
        sub_recipe_c = recipe_test_utils.create_recipe(recipe_type=sub_recipe_type_c)

        recipe_interface = Interface()
        recipe_interface.add_parameter(JsonParameter('recipe_input', 'string'))
        definition = RecipeDefinition(recipe_interface)
        definition.add_job_node('node_a', job_type_a.name, job_type_a.version, job_type_a.revision_num)
        definition.add_job_node('node_b', job_type_b.name, job_type_b.version, job_type_b.revision_num)
        definition.add_recipe_node('node_c', sub_recipe_type_c.name, sub_recipe_type_c.revision_num)
        definition.add_recipe_input_connection('node_c', 'input_c', 'recipe_input')
        definition.add_dependency('node_c', 'node_a')
        definition.add_dependency_input_connection('node_c', 'input_a', 'node_a', 'output_a')
        definition.add_dependency('node_c', 'node_b')
        definition.add_dependency_input_connection('node_c', 'input_b', 'node_b', 'output_b')
        def_dict = convert_recipe_definition_to_v6_json(definition).get_dict()
        recipe_type = recipe_test_utils.create_recipe_type(definition=def_dict)
        recipe_data = Data()
        recipe_data.add_value(JsonValue('recipe_input', 'hello'))
        recipe_data_dict = convert_data_to_v6_json(recipe_data).get_dict()
        recipe = recipe_test_utils.create_recipe(recipe_type=recipe_type, input=recipe_data_dict)
        recipe_node_a = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='node_a', job=job_a)
        recipe_node_b = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='node_b', job=job_b)
        recipe_node_c = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='node_c', sub_recipe=sub_recipe_c)
        RecipeNode.objects.bulk_create([recipe_node_a, recipe_node_b, recipe_node_c])
        job_a.recipe = recipe
        job_a.save()
        job_b.recipe = recipe
        job_b.save()
        sub_recipe_c.recipe = recipe
        sub_recipe_c.save()

        # Create message
        message = ProcessRecipeInput()
        message.recipe_id = sub_recipe_c.id

        # Execute message
        result = message.execute()
        self.assertTrue(result)

        sub_recipe_c = Recipe.objects.get(id=sub_recipe_c.id)
        # Check for update_recipe message
        self.assertEqual(len(message.new_messages), 1)
        self.assertEqual(message.new_messages[0].type, 'update_recipe')

        # Check sub-recipe for expected input_file_size
        self.assertEqual(sub_recipe_c.input_file_size, 24469.0)
        # Check sub-recipe for expected input data
        self.assertNotEqual(sub_recipe_c.input['version'], '1.0')  # Should not be legacy
        self.assertSetEqual(set(sub_recipe_c.get_input_data().values.keys()), {'input_a', 'input_b', 'input_c'})
        self.assertListEqual(sub_recipe_c.get_input_data().values['input_a'].file_ids, [file_1.id])
        self.assertListEqual(sub_recipe_c.get_input_data().values['input_b'].file_ids,
                             [file_2.id, file_3.id, file_4.id])
        self.assertEqual(sub_recipe_c.get_input_data().values['input_c'].value, 'hello')

        # Make sure sub-recipe input file models are created
        input_files = RecipeInputFile.objects.filter(recipe_id=sub_recipe_c.id)
        self.assertEqual(len(input_files), 4)
        file_ids = {input_file.input_file_id for input_file in input_files}
        self.assertSetEqual(file_ids, {file_1.id, file_2.id, file_3.id, file_4.id})

        # Test executing message again
        message_json_dict = message.to_json()
        message = ProcessRecipeInput.from_json(message_json_dict)
        result = message.execute()
        self.assertTrue(result)

        # Still should have update_recipe message
        self.assertEqual(len(message.new_messages), 1)
        self.assertEqual(message.new_messages[0].type, 'update_recipe')

        # Make sure recipe input file models are unchanged
        input_files = RecipeInputFile.objects.filter(recipe_id=sub_recipe_c.id)
        self.assertEqual(len(input_files), 4)

    def test_execute_with_recipe_legacy(self):
        """Tests calling ProcessRecipeInput.execute() successfully when a legacy sub-recipe has to get its data from its
        recipe
        """

        workspace = storage_test_utils.create_workspace()
        file_1 = storage_test_utils.create_file(workspace=workspace, file_size=104857600.0)
        file_2 = storage_test_utils.create_file(workspace=workspace, file_size=987654321.0)
        file_3 = storage_test_utils.create_file(workspace=workspace, file_size=65456.0)
        file_4 = storage_test_utils.create_file(workspace=workspace, file_size=24564165456.0)
        manifest_a = {
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
                        'files': [{'name': 'output_a', 'pattern': '*.png'}]
                    }
                }
            }
        }
        job_type_a = job_test_utils.create_job_type(interface=manifest_a)
        output_data_a = Data()
        output_data_a.add_value(FileValue('output_a', [file_1.id]))
        output_data_a_dict = convert_data_to_v6_json(output_data_a).get_dict()
        manifest_b = {
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
                    'inputs': {'files': [], 'json': []},
                    'outputs': {
                        'files': [{'name': 'output_b', 'pattern': '*.png', 'multiple': True}]
                    }
                }
            }
        }
        job_type_b = job_test_utils.create_job_type(interface=manifest_b)
        output_data_b = Data()
        output_data_b.add_value(FileValue('output_b', [file_2.id, file_3.id, file_4.id]))
        output_data_b_dict = convert_data_to_v6_json(output_data_b).get_dict()
        job_a = job_test_utils.create_job(job_type=job_type_a, num_exes=1, status='COMPLETED',
                                          output=output_data_a_dict)
        job_b = job_test_utils.create_job(job_type=job_type_b, num_exes=1, status='COMPLETED',
                                          output=output_data_b_dict)
        sub_recipe_interface_c = Interface()
        sub_recipe_interface_c.add_parameter(FileParameter('input_a', ['image/png']))
        sub_recipe_interface_c.add_parameter(FileParameter('input_b', ['image/png'], multiple=True))
        sub_recipe_def_c = RecipeDefinition(sub_recipe_interface_c)
        sub_recipe_def_dict_c = convert_recipe_definition_to_v1_json(sub_recipe_def_c).get_dict()
        sub_recipe_type_c = recipe_test_utils.create_recipe_type(definition=sub_recipe_def_dict_c)
        sub_recipe_c = recipe_test_utils.create_recipe(recipe_type=sub_recipe_type_c)

        definition = RecipeDefinition(Interface())
        definition.add_job_node('node_a', job_type_a.name, job_type_a.version, job_type_a.revision_num)
        definition.add_job_node('node_b', job_type_b.name, job_type_b.version, job_type_b.revision_num)
        definition.add_recipe_node('node_c', sub_recipe_type_c.name, sub_recipe_type_c.revision_num)
        definition.add_dependency('node_c', 'node_a')
        definition.add_dependency_input_connection('node_c', 'input_a', 'node_a', 'output_a')
        definition.add_dependency('node_c', 'node_b')
        definition.add_dependency_input_connection('node_c', 'input_b', 'node_b', 'output_b')
        def_dict = convert_recipe_definition_to_v6_json(definition).get_dict()
        recipe_type = recipe_test_utils.create_recipe_type(definition=def_dict)
        recipe_data_dict = {'version': '1.0', 'input_data': [], 'workspace_id': workspace.id}
        recipe = recipe_test_utils.create_recipe(recipe_type=recipe_type, input=recipe_data_dict)
        recipe_node_a = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='node_a', job=job_a)
        recipe_node_b = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='node_b', job=job_b)
        recipe_node_c = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='node_c', sub_recipe=sub_recipe_c)
        RecipeNode.objects.bulk_create([recipe_node_a, recipe_node_b, recipe_node_c])
        job_a.recipe = recipe
        job_a.save()
        job_b.recipe = recipe
        job_b.save()
        sub_recipe_c.recipe = recipe
        sub_recipe_c.save()

        # Create message
        message = ProcessRecipeInput()
        message.recipe_id = sub_recipe_c.id

        # Execute message
        result = message.execute()
        self.assertTrue(result)

        sub_recipe_c = Recipe.objects.get(id=sub_recipe_c.id)
        # Check for update_recipe message
        self.assertEqual(len(message.new_messages), 1)
        self.assertEqual(message.new_messages[0].type, 'update_recipe')

        # Check sub-recipe for expected input_file_size
        self.assertEqual(sub_recipe_c.input_file_size, 24469.0)
        # Check sub-recipe for expected input data
        self.assertEqual(sub_recipe_c.input['version'], '1.0')  # Should be legacy input data with workspace ID
        self.assertEqual(sub_recipe_c.input['workspace_id'], workspace.id)
        self.assertSetEqual(set(sub_recipe_c.get_input_data().values.keys()), {'input_a', 'input_b'})
        self.assertListEqual(sub_recipe_c.get_input_data().values['input_a'].file_ids, [file_1.id])
        self.assertListEqual(sub_recipe_c.get_input_data().values['input_b'].file_ids,
                             [file_2.id, file_3.id, file_4.id])

        # Make sure sub-recipe input file models are created
        input_files = RecipeInputFile.objects.filter(recipe_id=sub_recipe_c.id)
        self.assertEqual(len(input_files), 4)
        file_ids = {input_file.input_file_id for input_file in input_files}
        self.assertSetEqual(file_ids, {file_1.id, file_2.id, file_3.id, file_4.id})

        # Test executing message again
        message_json_dict = message.to_json()
        message = ProcessRecipeInput.from_json(message_json_dict)
        result = message.execute()
        self.assertTrue(result)

        # Still should have update_recipe message
        self.assertEqual(len(message.new_messages), 1)
        self.assertEqual(message.new_messages[0].type, 'update_recipe')

        # Make sure recipe input file models are unchanged
        input_files = RecipeInputFile.objects.filter(recipe_id=sub_recipe_c.id)
        self.assertEqual(len(input_files), 4)
