from __future__ import unicode_literals
from __future__ import absolute_import

import django
from django.test import TestCase

from data.filter.filter import DataFilter
from data.interface.interface import Interface
from data.interface.parameter import FileParameter
from job.test import utils as job_test_utils
from recipe.definition.definition import RecipeDefinition
from recipe.definition.json.definition_v6 import convert_recipe_definition_to_v6_json
from recipe.messages.process_condition import create_process_condition_messages, ProcessCondition
from recipe.models import RecipeCondition, RecipeNode
from recipe.test import utils as recipe_test_utils
from storage.test import utils as storage_test_utils


class TestProcessCondition(TestCase):

    def setUp(self):
        django.setup()

    def test_json(self):
        """Tests converting a ProcessCondition message to and from JSON"""

        definition = RecipeDefinition(Interface())
        # TODO: once DataFilter is implemented, create a DataFilter object here that accepts the inputs
        definition.add_condition_node('node_a', Interface(), DataFilter()) #True
        definition_dict = convert_recipe_definition_to_v6_json(definition).get_dict()
        recipe_type = recipe_test_utils.create_recipe_type_v6(definition=definition_dict)
        recipe = recipe_test_utils.create_recipe(recipe_type=recipe_type)
        condition = recipe_test_utils.create_recipe_condition(recipe=recipe, save=True)
        recipe_test_utils.create_recipe_node(recipe=recipe, node_name='node_a', condition=condition, save=True)

        # Create message
        message = create_process_condition_messages([condition.id])[0]

        # Convert message to JSON and back, and then execute
        message_json_dict = message.to_json()
        new_message = ProcessCondition.from_json(message_json_dict)
        result = new_message.execute()

        self.assertTrue(result)
        condition = RecipeCondition.objects.get(id=condition.id)
        self.assertEqual(len(new_message.new_messages), 1)
        self.assertEqual(new_message.new_messages[0].type, 'update_recipe')
        self.assertEqual(new_message.new_messages[0].root_recipe_id, recipe.id)
        self.assertTrue(condition.is_processed)
        self.assertIsNotNone(condition.processed)
        self.assertTrue(condition.is_accepted)

    def test_execute(self):
        """Tests calling ProcessCondition.execute() successfully"""

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
                        'files': [{'name': 'OUTPUT_A', 'pattern': '*.png', 'multiple': True}]
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
                    'inputs': {'files': []},
                    'outputs': {
                        'files': [{'name': 'OUTPUT_B', 'pattern': '*.png', 'multiple': True}]
                    }
                }
            }
        }
        job_type_2 = job_test_utils.create_job_type(interface=manifest_2)
        output_1_dict = {
            'version': '1.0',
            'output_data': [{
                'name': 'OUTPUT_A',
                'file_ids': [file_1.id, file_2.id]
            }]
        }
        output_2_dict = {
            'version': '1.0',
            'output_data': [{
                'name': 'OUTPUT_B',
                'file_ids': [file_3.id, file_4.id]
            }]
        }

        cond_interface = Interface()
        cond_interface.add_parameter(FileParameter('INPUT_C_1', [], multiple=True))
        cond_interface.add_parameter(FileParameter('INPUT_C_2', [], multiple=True))
        definition = RecipeDefinition(Interface())
        definition.add_job_node('node_a', job_type_1.name, job_type_1.version, job_type_1.revision_num)
        definition.add_job_node('node_b', job_type_2.name, job_type_2.version, job_type_2.revision_num)
        # TODO: once DataFilter is implemented, create a DataFilter object here that accepts the inputs
        definition.add_condition_node('node_c', cond_interface, DataFilter()) #True
        definition.add_dependency('node_a', 'node_c')
        definition.add_dependency('node_b', 'node_c')
        definition.add_dependency_input_connection('node_c', 'INPUT_C_1', 'node_a', 'OUTPUT_A')
        definition.add_dependency_input_connection('node_c', 'INPUT_C_2', 'node_b', 'OUTPUT_B')
        def_dict = convert_recipe_definition_to_v6_json(definition).get_dict()
        recipe_type = recipe_test_utils.create_recipe_type_v6(definition=def_dict)
        recipe_data_dict = {'version': '1.0', 'input_data': [], 'workspace_id': workspace.id}
        recipe = recipe_test_utils.create_recipe(recipe_type=recipe_type, input=recipe_data_dict)
        job_1 = job_test_utils.create_job(job_type=job_type_1, num_exes=1, status='COMPLETED', output=output_1_dict,
                                          recipe=recipe)
        job_2 = job_test_utils.create_job(job_type=job_type_2, num_exes=1, status='COMPLETED', output=output_2_dict,
                                          recipe=recipe)
        condition = recipe_test_utils.create_recipe_condition(recipe=recipe, save=True)
        node_a = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='node_a', job=job_1, save=False)
        node_b = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='node_b', job=job_2, save=False)
        node_c = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='node_c', condition=condition,
                                                      save=False)
        RecipeNode.objects.bulk_create([node_a, node_b, node_c])

        # Create message
        message = create_process_condition_messages([condition.id])[0]

        # Execute message
        result = message.execute()
        self.assertTrue(result)

        condition = RecipeCondition.objects.get(id=condition.id)
        # Check for update_recipe message
        self.assertEqual(len(message.new_messages), 1)
        self.assertEqual(message.new_messages[0].type, 'update_recipe')
        self.assertEqual(message.new_messages[0].root_recipe_id, recipe.id)

        # Check condition flags
        self.assertTrue(condition.is_processed)
        self.assertIsNotNone(condition.processed)
        self.assertTrue(condition.is_accepted)
        # Check condition for expected data
        self.assertSetEqual(set(condition.get_data().values.keys()), {'INPUT_C_1', 'INPUT_C_2'})
        self.assertListEqual(condition.get_data().values['INPUT_C_1'].file_ids, [file_1.id, file_2.id])
        self.assertListEqual(condition.get_data().values['INPUT_C_2'].file_ids, [file_3.id, file_4.id])

        # Test executing message again
        message_json_dict = message.to_json()
        message = ProcessCondition.from_json(message_json_dict)
        result = message.execute()
        self.assertTrue(result)

        # Still should have update_recipe message
        self.assertEqual(len(message.new_messages), 1)
        self.assertEqual(message.new_messages[0].type, 'update_recipe')
        self.assertEqual(message.new_messages[0].root_recipe_id, recipe.id)
