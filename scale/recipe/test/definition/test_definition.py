from __future__ import unicode_literals

import django
from django.test import TestCase
from mock import MagicMock

import job.test.utils as job_test_utils
import recipe.test.utils as recipe_test_utils
from data.data.data import Data
from data.data.value import FileValue, JsonValue
from data.filter.filter import DataFilter
from data.interface.exceptions import InvalidInterface, InvalidInterfaceConnection
from data.interface.interface import Interface
from data.interface.parameter import FileParameter, JsonParameter
from recipe.definition.definition import RecipeDefinition
from recipe.definition.exceptions import InvalidDefinition
from recipe.models import RecipeNodeOutput


class TestRecipeDefinition(TestCase):

    def setUp(self):
        django.setup()

    def test_add_dependency_missing_parent(self):
        """Tests calling RecipeDefinition.add_dependency() with a missing parent node"""

        input_interface = Interface()
        definition = RecipeDefinition(input_interface)
        definition.add_job_node('node_1', 'job_type_1', '1.0', 1)

        with self.assertRaises(InvalidDefinition) as context:
            definition.add_dependency('bad_parent', 'node_1')
        self.assertEqual(context.exception.error.name, 'UNKNOWN_NODE')

    def test_add_dependency_missing_child(self):
        """Tests calling RecipeDefinition.add_dependency() with a missing child node"""

        input_interface = Interface()
        definition = RecipeDefinition(input_interface)
        definition.add_job_node('node_1', 'job_type_1', '1.0', 1)

        with self.assertRaises(InvalidDefinition) as context:
            definition.add_dependency('node_1', 'missing_child')
        self.assertEqual(context.exception.error.name, 'UNKNOWN_NODE')

    def test_dependency_input_conn_missing_dependency(self):
        """Tests calling RecipeDefinition.add_dependency_input_connection() with an unknown dependency node"""

        input_interface = Interface()
        definition = RecipeDefinition(input_interface)
        definition.add_job_node('node_1', 'job_type_1', '1.0', 1)

        with self.assertRaises(InvalidDefinition) as context:
            definition.add_dependency_input_connection('node_1', 'input_1', 'missing_dependency', 'output_1')
        self.assertEqual(context.exception.error.name, 'UNKNOWN_NODE')

    def test_dependency_input_conn_cannot_connect_to_recipe(self):
        """Tests calling RecipeDefinition.add_dependency_input_connection() to connect to a recipe node (invalid)"""

        input_interface = Interface()
        definition = RecipeDefinition(input_interface)
        definition.add_job_node('node_1', 'job_type_1', '1.0', 1)
        definition.add_recipe_node('node_2', 'recipe_type_1', 1)

        with self.assertRaises(InvalidDefinition) as context:
            definition.add_dependency_input_connection('node_1', 'input_1', 'node_2', 'output_1')
        self.assertEqual(context.exception.error.name, 'CONNECTION_INVALID_NODE')

    def test_dependency_input_conn_missing_input_node(self):
        """Tests calling RecipeDefinition.add_dependency_input_connection() with an unknown input node"""

        input_interface = Interface()
        definition = RecipeDefinition(input_interface)
        definition.add_job_node('node_1', 'job_type_1', '1.0', 1)

        with self.assertRaises(InvalidDefinition) as context:
            definition.add_dependency_input_connection('missing_node', 'input_1', 'node_1', 'output_1')
        self.assertEqual(context.exception.error.name, 'UNKNOWN_NODE')

    def test_dependency_input_conn_duplicate_input(self):
        """Tests calling RecipeDefinition.add_dependency_input_connection() to connect to a duplicate input"""

        input_interface = Interface()
        definition = RecipeDefinition(input_interface)
        definition.add_job_node('node_1', 'job_type_1', '1.0', 1)
        definition.add_job_node('node_2', 'job_type_2', '1.0', 1)

        definition.add_dependency_input_connection('node_1', 'input_1', 'node_2', 'output_1')
        with self.assertRaises(InvalidDefinition) as context:
            definition.add_dependency_input_connection('node_1', 'input_1', 'node_2', 'output_1')
        self.assertEqual(context.exception.error.name, 'NODE_INTERFACE')

    def test_dependency_input_conn_successful(self):
        """Tests calling RecipeDefinition.add_dependency_input_connection() successfully"""

        input_interface = Interface()
        definition = RecipeDefinition(input_interface)
        definition.add_recipe_node('node_1', 'recipe_type_1', 1)
        definition.add_job_node('node_2', 'job_type_2', '1.0', 1)

        definition.add_dependency_input_connection('node_1', 'input_1', 'node_2', 'output_1')

    def test_recipe_input_conn_missing_input(self):
        """Tests calling RecipeDefinition.add_recipe_input_connection() with an unknown recipe input"""

        input_interface = Interface()
        definition = RecipeDefinition(input_interface)
        definition.add_job_node('node_1', 'job_type_1', '1.0', 1)

        with self.assertRaises(InvalidDefinition) as context:
            definition.add_recipe_input_connection('node_1', 'input_1', 'missing_recipe_input')
        self.assertEqual(context.exception.error.name, 'UNKNOWN_INPUT')

    def test_recipe_input_conn_missing_input_node(self):
        """Tests calling RecipeDefinition.add_recipe_input_connection() with an unknown input node"""

        input_interface = Interface()
        input_interface.parameters = {'recipe_input_1': MagicMock()}
        definition = RecipeDefinition(input_interface)
        definition.add_job_node('node_1', 'job_type_1', '1.0', 1)

        with self.assertRaises(InvalidDefinition) as context:
            definition.add_recipe_input_connection('missing_node', 'input_1', 'recipe_input_1')
        self.assertEqual(context.exception.error.name, 'UNKNOWN_NODE')

    def test_recipe_input_conn_duplicate_input(self):
        """Tests calling RecipeDefinition.add_recipe_input_connection() to connect to a duplicate input"""

        input_interface = Interface()
        input_interface.parameters = {'recipe_input_1': MagicMock()}
        definition = RecipeDefinition(input_interface)
        definition.add_job_node('node_1', 'job_type_1', '1.0', 1)
        definition.add_job_node('node_2', 'job_type_2', '1.0', 1)

        definition.add_recipe_input_connection('node_1', 'input_1', 'recipe_input_1')
        with self.assertRaises(InvalidDefinition) as context:
            definition.add_recipe_input_connection('node_1', 'input_1', 'recipe_input_1')
        self.assertEqual(context.exception.error.name, 'NODE_INTERFACE')

    def test_recipe_input_conn_successful(self):
        """Tests calling RecipeDefinition.add_recipe_input_connection() successfully"""

        input_interface = Interface()
        input_interface.parameters = {'recipe_input_1': MagicMock()}
        definition = RecipeDefinition(input_interface)
        definition.add_job_node('node_1', 'job_type_1', '1.0', 1)

        definition.add_recipe_input_connection('node_1', 'input_1', 'recipe_input_1')

    def test_generate_node_input_data(self):
        """Tests calling RecipeDefinition.generate_node_input_data()"""

        input_interface = Interface()
        input_interface.add_parameter(FileParameter('recipe_input_1', ['image/gif'], multiple=True))
        input_interface.add_parameter(JsonParameter('recipe_input_2', 'string'))
        definition = RecipeDefinition(input_interface)
        definition.add_job_node('node_a', 'job_type_1', '1.0', 1)
        definition.add_job_node('node_b', 'job_type_2', '1.0', 1)
        definition.add_job_node('node_c', 'job_type_3', '1.0', 1)
        definition.add_dependency('node_c', 'node_b')
        definition.add_dependency('node_c', 'node_a')
        definition.add_recipe_input_connection('node_c', 'input_1', 'recipe_input_1')
        definition.add_recipe_input_connection('node_c', 'input_2', 'recipe_input_2')
        definition.add_dependency_input_connection('node_c', 'input_3', 'node_a', 'output_a_1')
        definition.add_dependency_input_connection('node_c', 'input_4', 'node_a', 'output_a_2')
        definition.add_dependency_input_connection('node_c', 'input_5', 'node_b', 'output_b_1')

        recipe_data = Data()
        recipe_data.add_value(FileValue('recipe_input_1', [1, 2, 3, 4, 5]))
        recipe_data.add_value(JsonValue('recipe_input_2', 'Scale is awesome!'))
        a_output_data = Data()
        a_output_data.add_value(FileValue('output_a_1', [1234]))
        a_output_data.add_value(JsonValue('output_a_2', {'foo': 'bar'}))
        b_output_data = Data()
        b_output_data.add_value(JsonValue('output_b_1', 12.34))
        node_outputs = {'node_a': RecipeNodeOutput('node_a', 'job', 1, a_output_data),
                        'node_b': RecipeNodeOutput('node_b', 'job', 1, b_output_data)}

        node_data = definition.generate_node_input_data('node_c', recipe_data, node_outputs)
        self.assertSetEqual(set(node_data.values.keys()), {'input_1', 'input_2', 'input_3', 'input_4', 'input_5'})
        self.assertListEqual(node_data.values['input_1'].file_ids, [1, 2, 3, 4, 5])
        self.assertEqual(node_data.values['input_2'].value, 'Scale is awesome!')
        self.assertListEqual(node_data.values['input_3'].file_ids, [1234])
        self.assertDictEqual(node_data.values['input_4'].value, {'foo': 'bar'})
        self.assertEqual(node_data.values['input_5'].value, 12.34)

    def test_topological_order_circular(self):
        """Tests calling RecipeDefinition.get_topological_order() with a circular dependency"""

        input_interface = Interface()
        definition = RecipeDefinition(input_interface)
        definition.add_job_node('A', 'job_type_1', '1.0', 1)
        definition.add_job_node('B', 'job_type_2', '1.0', 1)
        definition.add_recipe_node('C', 'recipe_type_1', 1)
        definition.add_recipe_node('D', 'recipe_type_2', 1)
        definition.add_dependency('A', 'B')
        definition.add_dependency('B', 'C')
        definition.add_dependency('C', 'D')
        definition.add_dependency('D', 'B')

        with self.assertRaises(InvalidDefinition) as context:
            definition.get_topological_order()
        self.assertEqual(context.exception.error.name, 'CIRCULAR_DEPENDENCY')

    def test_topological_order_successful(self):
        """Tests calling RecipeDefinition.get_topological_order() successfully"""

        input_interface = Interface()
        definition = RecipeDefinition(input_interface)
        definition.add_job_node('A', 'job_type_1', '1.0', 1)
        definition.add_job_node('B', 'job_type_2', '1.0', 1)
        definition.add_recipe_node('C', 'recipe_type_1', 1)
        definition.add_recipe_node('D', 'recipe_type_2', 1)
        definition.add_job_node('E', 'job_type_3', '1.0', 1)
        definition.add_job_node('F', 'job_type_4', '1.0', 1)
        definition.add_dependency('A', 'B')
        definition.add_dependency('A', 'C')
        definition.add_dependency('A', 'E')
        definition.add_dependency('B', 'C')
        definition.add_dependency('B', 'D')
        definition.add_dependency('C', 'D')
        definition.add_dependency('D', 'E')
        definition.add_dependency('E', 'F')

        order = definition.get_topological_order()
        expected_order = ['A', 'B', 'C', 'D', 'E', 'F']  # This is the only valid topological order for this graph

        self.assertListEqual(order, expected_order)

    def test_validate_invalid_input_interface(self):
        """Tests calling RecipeDefinition.validate() with an invalid input interface"""

        input_interface = MagicMock()
        input_interface.validate.side_effect = InvalidInterface('', '')
        definition = RecipeDefinition(input_interface)

        with self.assertRaises(InvalidDefinition) as context:
            definition.validate({}, {})
        self.assertEqual(context.exception.error.name, 'INPUT_INTERFACE')

    def test_validate_missing_dependency(self):
        """Tests calling RecipeDefinition.validate() with a connection that has a missing dependency"""

        input_interface = Interface()
        input_interface.parameters = {'recipe_input_1': MagicMock()}
        definition = RecipeDefinition(input_interface)
        definition.add_job_node('A', 'job_type_1', '1.0', 1)
        definition.add_recipe_node('B', 'recipe_type_1', 1)
        definition.add_job_node('C', 'job_type_2', '1.0', 1)
        definition.add_dependency('B', 'C')
        definition.add_dependency_input_connection('B', 'input_1', 'A', 'output_1')
        mocked_interfaces = {'A': MagicMock(), 'B': MagicMock(), 'C': MagicMock()}

        with self.assertRaises(InvalidDefinition) as context:
            definition.validate(mocked_interfaces, mocked_interfaces)
        self.assertEqual(context.exception.error.name, 'NODE_INTERFACE')

    def test_validate_invalid_connection(self):
        """Tests calling RecipeDefinition.validate() with an invalid connection to a node's input interface"""

        input_interface = Interface()
        definition = RecipeDefinition(input_interface)
        definition.add_job_node('A', 'job_type_1', '1.0', 1)
        definition.add_recipe_node('B', 'recipe_type_1', 1)
        definition.add_dependency('A', 'B')
        definition.add_dependency_input_connection('B', 'input_1', 'A', 'output_1')
        mocked_interfaces = {'A': MagicMock(), 'B': MagicMock()}
        mocked_interfaces['B'].validate_connection.side_effect = InvalidInterfaceConnection('', '')

        with self.assertRaises(InvalidDefinition) as context:
            definition.validate(mocked_interfaces, mocked_interfaces)
        self.assertEqual(context.exception.error.name, 'NODE_INTERFACE')

    def test_validate_successful(self):
        """Tests calling RecipeDefinition.validate() successfully"""

        recipe_interface = Interface()
        recipe_interface.add_parameter(JsonParameter('recipe_input_1', 'integer'))
        definition = RecipeDefinition(recipe_interface)
        definition.add_job_node('A', 'job_type_1', '1.0', 1)
        condition_interface = Interface()
        condition_interface.add_parameter(JsonParameter('cond_param', 'integer'))
        definition.add_condition_node('B', condition_interface, DataFilter(True))
        definition.add_recipe_node('C', 'recipe_type_1', 1)
        definition.add_dependency('A', 'B')
        definition.add_dependency('B', 'C')
        definition.add_recipe_input_connection('A', 'a_input_1', 'recipe_input_1')
        definition.add_dependency_input_connection('B', 'cond_param', 'A', 'a_output_1')
        definition.add_dependency_input_connection('C', 'c_input_1', 'A', 'a_output_1')
        definition.add_dependency_input_connection('C', 'c_input_2', 'B', 'cond_param')
        job_input_interface = Interface()
        job_input_interface.add_parameter(JsonParameter('a_input_1', 'integer'))
        job_output_interface = Interface()
        job_output_interface.add_parameter(JsonParameter('a_output_1', 'integer'))
        recipe_input_interface = Interface()
        recipe_input_interface.add_parameter(JsonParameter('c_input_1', 'integer'))
        recipe_input_interface.add_parameter(JsonParameter('c_input_2', 'integer'))
        input_interfaces = {'A': job_input_interface, 'C': recipe_input_interface}
        output_interfaces = {'A': job_output_interface, 'C': Interface()}

        warnings = definition.validate(input_interfaces, output_interfaces)
        self.assertListEqual(warnings, [])

    def test_update_job_node(self):
        """Tests calling RecipeDefinition.update_job_node() successfully"""

        input_interface = Interface()
        definition = RecipeDefinition(input_interface)
        definition.add_job_node('A', 'job_type_1', '1.0', 1)
        definition.add_recipe_node('B', 'recipe_type_1', 1)
        definition.add_dependency('A', 'B')
        definition.add_dependency_input_connection('B', 'input_1', 'A', 'output_1')
        definition.update_job_nodes('job_type_1', '1.0', 2)
        mocked_interfaces = {'A': MagicMock(), 'B': MagicMock()}

        warnings = definition.validate(mocked_interfaces, mocked_interfaces)
        self.assertListEqual(warnings, [])
        
    def test_update_recipe_node(self):
        """Tests calling RecipeDefinition.update_recipe_node() successfully"""

        input_interface = Interface()
        definition = RecipeDefinition(input_interface)
        definition.add_job_node('A', 'job_type_1', '1.0', 1)
        definition.add_recipe_node('B', 'recipe_type_1', 1)
        definition.add_dependency('A', 'B')
        definition.add_dependency_input_connection('B', 'input_1', 'A', 'output_1')
        definition.update_recipe_nodes('recipe_type_1', 2)
        mocked_interfaces = {'A': MagicMock(), 'B': MagicMock()}

        warnings = definition.validate(mocked_interfaces, mocked_interfaces)
        self.assertListEqual(warnings, [])
