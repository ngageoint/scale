from __future__ import unicode_literals

import django
from django.test import TestCase
from mock import MagicMock

from data.interface.exceptions import InvalidInterface, InvalidInterfaceConnection
from data.interface.interface import Interface
from recipe.definition.definition import RecipeDefinition
from recipe.definition.exceptions import InvalidDefinition


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

        input_interface = Interface()
        definition = RecipeDefinition(input_interface)
        definition.add_job_node('A', 'job_type_1', '1.0', 1)
        definition.add_recipe_node('B', 'recipe_type_1', 1)
        definition.add_dependency('A', 'B')
        definition.add_dependency_input_connection('B', 'input_1', 'A', 'output_1')
        mocked_interfaces = {'A': MagicMock(), 'B': MagicMock()}

        warnings = definition.validate(mocked_interfaces, mocked_interfaces)
        self.assertListEqual(warnings, [])
