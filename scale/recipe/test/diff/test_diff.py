from __future__ import unicode_literals

import django
from django.test import TestCase

from data.filter.filter import DataFilter
from data.interface.interface import Interface
from data.interface.parameter import FileParameter, JsonParameter
from recipe.definition.definition import RecipeDefinition
from recipe.diff.diff import RecipeDiff
from recipe.diff.forced_nodes import ForcedNodes
from recipe.diff.node import NodeDiff


class TestRecipeDiff(TestCase):

    def setUp(self):
        django.setup()

    def test_init_identical(self):
        """Tests creating a RecipeDiff between two identical recipe definitions"""

        interface_1 = Interface()
        interface_1.add_parameter(FileParameter('file_param_1', ['image/gif']))
        interface_1.add_parameter(JsonParameter('json_param_1', 'object'))
        interface_2 = Interface()
        interface_2.add_parameter(FileParameter('file_param_1', ['image/gif']))
        interface_2.add_parameter(JsonParameter('json_param_1', 'object'))

        cond_interface_1 = Interface()
        cond_interface_1.add_parameter(FileParameter('cond_file', ['image/gif']))
        # TODO: eventually implement two "real" and identical filters
        filter_1 = DataFilter(False)
        cond_interface_2 = Interface()
        cond_interface_2.add_parameter(FileParameter('cond_file', ['image/gif']))
        filter_2 = DataFilter(False)

        definition_1 = RecipeDefinition(interface_1)
        definition_1.add_job_node('A', 'job_type_1', '1.0', 1)
        definition_1.add_job_node('B', 'job_type_2', '2.0', 1)
        definition_1.add_job_node('C', 'job_type_3', '1.0', 2)
        definition_1.add_recipe_node('D', 'recipe_type_1', 1)
        definition_1.add_condition_node('E', cond_interface_1, filter_1)
        definition_1.add_job_node('F', 'job_type_4', '1.0', 1)
        definition_1.add_dependency('A', 'B')
        definition_1.add_dependency('A', 'C')
        definition_1.add_dependency('C', 'D')
        definition_1.add_dependency('A', 'E')
        definition_1.add_dependency('E', 'F')
        definition_1.add_recipe_input_connection('A', 'input_1', 'file_param_1')
        definition_1.add_dependency_input_connection('B', 'b_input_1', 'A', 'a_output_1')
        definition_1.add_dependency_input_connection('C', 'c_input_1', 'A', 'a_output_2')
        definition_1.add_dependency_input_connection('D', 'd_input_1', 'C', 'c_output_1')
        definition_1.add_recipe_input_connection('D', 'd_input_2', 'json_param_1')
        definition_1.add_dependency_input_connection('E', 'cond_file', 'A', 'a_output_1')
        definition_1.add_dependency_input_connection('F', 'f_input_1', 'E', 'cond_file')

        definition_2 = RecipeDefinition(interface_2)
        definition_2.add_job_node('A', 'job_type_1', '1.0', 1)
        definition_2.add_job_node('B', 'job_type_2', '2.0', 1)
        definition_2.add_job_node('C', 'job_type_3', '1.0', 2)
        definition_2.add_recipe_node('D', 'recipe_type_1', 1)
        definition_2.add_condition_node('E', cond_interface_2, filter_2)
        definition_2.add_job_node('F', 'job_type_4', '1.0', 1)
        definition_2.add_dependency('A', 'B')
        definition_2.add_dependency('A', 'C')
        definition_2.add_dependency('C', 'D')
        definition_2.add_dependency('A', 'E')
        definition_2.add_dependency('E', 'F')
        definition_2.add_recipe_input_connection('A', 'input_1', 'file_param_1')
        definition_2.add_dependency_input_connection('B', 'b_input_1', 'A', 'a_output_1')
        definition_2.add_dependency_input_connection('C', 'c_input_1', 'A', 'a_output_2')
        definition_2.add_dependency_input_connection('D', 'd_input_1', 'C', 'c_output_1')
        definition_2.add_recipe_input_connection('D', 'd_input_2', 'json_param_1')
        definition_2.add_dependency_input_connection('E', 'cond_file', 'A', 'a_output_1')
        definition_2.add_dependency_input_connection('F', 'f_input_1', 'E', 'cond_file')

        diff = RecipeDiff(definition_1, definition_2)

        self.assertTrue(diff.can_be_reprocessed)
        self.assertListEqual(diff.reasons, [])
        # Every node should be unchanged and all should be copied during a reprocess
        nodes_to_copy = diff.get_nodes_to_copy()
        self.assertSetEqual(set(nodes_to_copy.keys()), {'A', 'B', 'C', 'D', 'E', 'F'})
        for node_diff in nodes_to_copy.values():
            self.assertEqual(node_diff.status, NodeDiff.UNCHANGED)
            self.assertFalse(node_diff.reprocess_new_node)
            self.assertListEqual(node_diff.changes, [])
        self.assertDictEqual(diff.get_nodes_to_supersede(), {})
        self.assertDictEqual(diff.get_nodes_to_unpublish(), {})

    def test_init_new_required_input(self):
        """Tests creating a RecipeDiff when the newer definition has a new required input parameter"""

        interface_1 = Interface()
        interface_1.add_parameter(FileParameter('file_param_1', ['image/gif']))
        interface_1.add_parameter(JsonParameter('json_param_1', 'object'))
        interface_2 = Interface()
        interface_2.add_parameter(FileParameter('file_param_1', ['image/gif']))
        interface_2.add_parameter(JsonParameter('json_param_1', 'object'))
        interface_2.add_parameter(JsonParameter('json_param_2', 'object', required=True))

        definition_1 = RecipeDefinition(interface_1)
        definition_1.add_job_node('A', 'job_type_1', '1.0', 1)
        definition_1.add_job_node('B', 'job_type_2', '2.0', 1)
        definition_1.add_job_node('C', 'job_type_3', '1.0', 2)
        definition_1.add_recipe_node('D', 'recipe_type_1', 1)
        definition_1.add_dependency('A', 'B')
        definition_1.add_dependency('A', 'C')
        definition_1.add_dependency('C', 'D')
        definition_1.add_recipe_input_connection('A', 'input_1', 'file_param_1')
        definition_1.add_dependency_input_connection('B', 'b_input_1', 'A', 'a_output_1')
        definition_1.add_dependency_input_connection('C', 'c_input_1', 'A', 'a_output_2')
        definition_1.add_dependency_input_connection('D', 'd_input_1', 'C', 'c_output_1')
        definition_1.add_recipe_input_connection('D', 'd_input_2', 'json_param_1')

        definition_2 = RecipeDefinition(interface_2)
        definition_2.add_job_node('A', 'job_type_1', '1.0', 1)
        definition_2.add_job_node('B', 'job_type_2', '2.0', 1)
        definition_2.add_job_node('C', 'job_type_3', '1.1', 1)  # Change to job type version and revision
        definition_2.add_recipe_node('D', 'recipe_type_1', 1)
        definition_2.add_dependency('A', 'B')
        definition_2.add_dependency('A', 'C')
        definition_2.add_dependency('C', 'D')
        definition_2.add_recipe_input_connection('A', 'input_1', 'file_param_1')
        definition_2.add_dependency_input_connection('B', 'b_input_1', 'A', 'a_output_1')
        definition_2.add_dependency_input_connection('C', 'c_input_1', 'A', 'a_output_2')
        definition_2.add_dependency_input_connection('D', 'd_input_1', 'C', 'c_output_1')
        definition_2.add_recipe_input_connection('D', 'd_input_2', 'json_param_1')

        diff = RecipeDiff(definition_1, definition_2)

        self.assertFalse(diff.can_be_reprocessed)
        self.assertEqual(len(diff.reasons), 1)
        self.assertEqual(diff.reasons[0].name, 'INPUT_CHANGE')
        # Cannot be reprocessed, so no nodes to copy, supersede, or unpublish
        self.assertDictEqual(diff.get_nodes_to_copy(), {})
        self.assertDictEqual(diff.get_nodes_to_supersede(), {})
        self.assertDictEqual(diff.get_nodes_to_unpublish(), {})
        # Ensure no nodes have reprocess_new_node set to true
        for node_diff in diff.graph.values():
            self.assertFalse(node_diff.reprocess_new_node)

    def test_init_changes(self):
        """Tests creating a RecipeDiff when the newer definition has a variety of changes in it"""

        interface_1 = Interface()
        interface_1.add_parameter(FileParameter('file_param_1', ['image/gif']))
        interface_1.add_parameter(JsonParameter('json_param_1', 'object'))
        interface_2 = Interface()
        interface_2.add_parameter(FileParameter('file_param_1', ['image/gif']))
        interface_2.add_parameter(JsonParameter('json_param_1', 'object'))
        interface_2.add_parameter(JsonParameter('json_param_2', 'object', required=False))

        cond_interface_1 = Interface()
        cond_interface_1.add_parameter(FileParameter('cond_file', ['image/gif']))
        # TODO: eventually implement two "real" and different filters
        filter_1 = DataFilter(False)
        cond_interface_2 = Interface()
        cond_interface_2.add_parameter(FileParameter('cond_file', ['image/gif']))
        filter_2 = DataFilter(True)

        definition_1 = RecipeDefinition(interface_1)
        definition_1.add_job_node('A', 'job_type_1', '1.0', 1)
        definition_1.add_job_node('B', 'job_type_2', '2.0', 1)
        definition_1.add_job_node('C', 'job_type_3', '1.0', 2)
        definition_1.add_recipe_node('D', 'recipe_type_1', 1)
        definition_1.add_job_node('E', 'job_type_4', '1.0', 1)
        definition_1.add_condition_node('G', cond_interface_1, filter_1)
        definition_1.add_job_node('H', 'job_type_4', '1.0', 1)
        definition_1.add_dependency('A', 'B')
        definition_1.add_dependency('A', 'C')
        definition_1.add_dependency('B', 'E')
        definition_1.add_dependency('C', 'D')
        definition_1.add_dependency('A', 'G')
        definition_1.add_dependency('G', 'H')
        definition_1.add_recipe_input_connection('A', 'input_1', 'file_param_1')
        definition_1.add_dependency_input_connection('B', 'b_input_1', 'A', 'a_output_1')
        definition_1.add_dependency_input_connection('C', 'c_input_1', 'A', 'a_output_2')
        definition_1.add_dependency_input_connection('D', 'd_input_1', 'C', 'c_output_1')
        definition_1.add_recipe_input_connection('D', 'd_input_2', 'json_param_1')
        definition_1.add_dependency_input_connection('G', 'cond_file', 'A', 'a_output_1')
        definition_1.add_dependency_input_connection('H', 'h_input_1', 'G', 'cond_file')

        definition_2 = RecipeDefinition(interface_2)
        # Nodes B and E are deleted
        definition_2.add_job_node('A', 'job_type_1', '1.0', 1)
        definition_2.add_job_node('C', 'job_type_3', '2.1', 1)  # Change to job type version and revision
        definition_2.add_recipe_node('D', 'recipe_type_1', 1)
        definition_2.add_condition_node('G', cond_interface_2, filter_2)
        definition_2.add_job_node('H', 'job_type_4', '1.0', 1)
        definition_2.add_recipe_node('F', 'recipe_type_2', 5)  # New node
        definition_2.add_dependency('A', 'C')
        definition_2.add_dependency('C', 'D')
        definition_2.add_dependency('D', 'F')
        definition_2.add_dependency('A', 'G')
        definition_2.add_dependency('G', 'H')
        definition_2.add_recipe_input_connection('A', 'input_1', 'file_param_1')
        definition_2.add_dependency_input_connection('C', 'c_input_1', 'A', 'a_output_2')
        definition_2.add_dependency_input_connection('D', 'd_input_1', 'C', 'c_output_1')
        definition_2.add_recipe_input_connection('D', 'd_input_2', 'json_param_1')
        definition_2.add_recipe_input_connection('F', 'f_input_1', 'json_param_2')
        definition_2.add_dependency_input_connection('G', 'cond_file', 'A', 'a_output_1')
        definition_2.add_dependency_input_connection('H', 'h_input_1', 'G', 'cond_file')

        diff = RecipeDiff(definition_1, definition_2)

        # Non-breaking recipe input changes so recipe can be reprocessed
        self.assertTrue(diff.can_be_reprocessed)
        self.assertListEqual(diff.reasons, [])
        # Check each node for correct fields
        node_a = diff.graph['A']
        self.assertEqual(node_a.status, NodeDiff.UNCHANGED)
        self.assertFalse(node_a.reprocess_new_node)
        self.assertListEqual(node_a.changes, [])
        node_b = diff.graph['B']
        self.assertEqual(node_b.status, NodeDiff.DELETED)
        self.assertFalse(node_b.reprocess_new_node)
        self.assertListEqual(node_b.changes, [])
        node_c = diff.graph['C']
        self.assertEqual(node_c.status, NodeDiff.CHANGED)
        self.assertTrue(node_c.reprocess_new_node)
        self.assertEqual(len(node_c.changes), 2)
        self.assertEqual(node_c.changes[0].name, 'JOB_TYPE_VERSION_CHANGE')
        self.assertEqual(node_c.changes[1].name, 'JOB_TYPE_REVISION_CHANGE')
        node_d = diff.graph['D']
        self.assertEqual(node_d.status, NodeDiff.CHANGED)
        self.assertTrue(node_d.reprocess_new_node)
        self.assertEqual(len(node_d.changes), 1)
        self.assertEqual(node_d.changes[0].name, 'PARENT_CHANGED')
        node_e = diff.graph['E']
        self.assertEqual(node_e.status, NodeDiff.DELETED)
        self.assertFalse(node_e.reprocess_new_node)
        self.assertListEqual(node_e.changes, [])
        node_f = diff.graph['F']
        self.assertEqual(node_f.status, NodeDiff.NEW)
        self.assertTrue(node_f.reprocess_new_node)
        self.assertListEqual(node_f.changes, [])
        node_g = diff.graph['G']
        self.assertEqual(node_g.status, NodeDiff.CHANGED)
        self.assertTrue(node_g.reprocess_new_node)
        self.assertEqual(len(node_g.changes), 1)
        self.assertEqual(node_g.changes[0].name, 'FILTER_CHANGE')
        node_h = diff.graph['H']
        self.assertEqual(node_h.status, NodeDiff.CHANGED)
        self.assertTrue(node_h.reprocess_new_node)
        self.assertEqual(len(node_h.changes), 1)
        self.assertEqual(node_h.changes[0].name, 'PARENT_CHANGED')
        # Check nodes to copy, supersede, and unpublish
        self.assertSetEqual(set(diff.get_nodes_to_copy().keys()), {'A'})
        self.assertSetEqual(set(diff.get_nodes_to_supersede().keys()), {'B', 'C', 'D', 'E', 'G', 'H'})
        self.assertSetEqual(set(diff.get_nodes_to_unpublish().keys()), {'B', 'E'})

    def test_init_changes_in_middle_of_chains(self):
        """Tests creating a RecipeDiff where nodes are deleted from and inserted into the middle of a chain"""

        interface_1 = Interface()
        interface_1.add_parameter(FileParameter('file_param_1', ['image/gif']))
        interface_1.add_parameter(JsonParameter('json_param_1', 'object'))
        interface_2 = Interface()
        interface_2.add_parameter(FileParameter('file_param_1', ['image/gif']))
        interface_2.add_parameter(JsonParameter('json_param_1', 'object'))

        definition_1 = RecipeDefinition(interface_1)
        definition_1.add_job_node('A', 'job_type_1', '1.0', 1)
        definition_1.add_job_node('B', 'job_type_2', '2.0', 1)
        definition_1.add_job_node('C', 'job_type_3', '1.0', 2)
        definition_1.add_recipe_node('D', 'recipe_type_1', 1)
        definition_1.add_dependency('A', 'B')
        definition_1.add_dependency('A', 'C')
        definition_1.add_dependency('C', 'D')
        definition_1.add_recipe_input_connection('A', 'input_1', 'file_param_1')
        definition_1.add_dependency_input_connection('B', 'b_input_1', 'A', 'a_output_1')
        definition_1.add_dependency_input_connection('C', 'c_input_1', 'A', 'a_output_2')
        definition_1.add_dependency_input_connection('D', 'd_input_1', 'C', 'c_output_1')
        definition_1.add_recipe_input_connection('D', 'd_input_2', 'json_param_1')

        definition_2 = RecipeDefinition(interface_2)
        definition_2.add_job_node('A', 'job_type_1', '1.0', 1)
        definition_2.add_job_node('B', 'job_type_2', '2.0', 1)
        # Node C is deleted
        definition_2.add_recipe_node('D', 'recipe_type_1', 1)
        definition_2.add_job_node('E', 'job_type_4', '5.0', 2)  # New node inbetween A and B
        definition_2.add_dependency('A', 'E')
        definition_2.add_dependency('E', 'B')
        definition_2.add_dependency('A', 'D')
        definition_2.add_recipe_input_connection('A', 'input_1', 'file_param_1')
        definition_2.add_dependency_input_connection('E', 'e_input_1', 'A', 'a_output_1')
        definition_2.add_dependency_input_connection('B', 'b_input_1', 'A', 'a_output_1')
        definition_2.add_dependency_input_connection('D', 'd_input_1', 'A', 'a_output_2')
        definition_2.add_recipe_input_connection('D', 'd_input_2', 'json_param_1')

        diff = RecipeDiff(definition_1, definition_2)

        # No recipe input changes so recipe can be reprocessed
        self.assertTrue(diff.can_be_reprocessed)
        self.assertListEqual(diff.reasons, [])
        # Check each node for correct fields
        node_a = diff.graph['A']
        self.assertEqual(node_a.status, NodeDiff.UNCHANGED)
        self.assertFalse(node_a.reprocess_new_node)
        self.assertListEqual(node_a.changes, [])
        node_b = diff.graph['B']
        self.assertEqual(node_b.status, NodeDiff.CHANGED)
        self.assertTrue(node_b.reprocess_new_node)
        self.assertEqual(len(node_b.changes), 2)
        self.assertEqual(node_b.changes[0].name, 'PARENT_NEW')
        self.assertEqual(node_b.changes[1].name, 'PARENT_REMOVED')
        node_c = diff.graph['C']
        self.assertEqual(node_c.status, NodeDiff.DELETED)
        self.assertFalse(node_c.reprocess_new_node)
        self.assertListEqual(node_c.changes, [])
        node_d = diff.graph['D']
        self.assertEqual(node_d.status, NodeDiff.CHANGED)
        self.assertTrue(node_d.reprocess_new_node)
        self.assertEqual(len(node_d.changes), 3)
        self.assertEqual(node_d.changes[0].name, 'PARENT_NEW')
        self.assertEqual(node_d.changes[1].name, 'PARENT_REMOVED')
        self.assertEqual(node_d.changes[2].name, 'INPUT_CHANGE')
        node_e = diff.graph['E']
        self.assertEqual(node_e.status, NodeDiff.NEW)
        self.assertTrue(node_e.reprocess_new_node)
        self.assertListEqual(node_e.changes, [])
        # Check nodes to copy, supersede, and unpublish
        self.assertSetEqual(set(diff.get_nodes_to_copy().keys()), {'A'})
        self.assertSetEqual(set(diff.get_nodes_to_supersede().keys()), {'B', 'C', 'D'})
        self.assertSetEqual(set(diff.get_nodes_to_unpublish().keys()), {'C'})

    def test_set_force_reprocess(self):
        """Tests calling RecipeDiff.set_force_reprocess()"""

        interface_1 = Interface()
        interface_1.add_parameter(FileParameter('file_param_1', ['image/gif']))
        interface_1.add_parameter(JsonParameter('json_param_1', 'object'))
        interface_2 = Interface()
        interface_2.add_parameter(FileParameter('file_param_1', ['image/gif']))
        interface_2.add_parameter(JsonParameter('json_param_1', 'object'))

        definition_1 = RecipeDefinition(interface_1)
        definition_1.add_job_node('A', 'job_type_1', '1.0', 1)
        definition_1.add_job_node('B', 'job_type_2', '2.0', 1)
        definition_1.add_job_node('C', 'job_type_3', '1.0', 2)
        definition_1.add_recipe_node('D', 'recipe_type_1', 1)
        definition_1.add_job_node('E', 'job_type_4', '1.0', 1)
        definition_1.add_dependency('A', 'B')
        definition_1.add_dependency('A', 'C')
        definition_1.add_dependency('C', 'D')
        definition_1.add_dependency('C', 'E')
        definition_1.add_recipe_input_connection('A', 'input_1', 'file_param_1')
        definition_1.add_dependency_input_connection('B', 'b_input_1', 'A', 'a_output_1')
        definition_1.add_dependency_input_connection('C', 'c_input_1', 'A', 'a_output_2')
        definition_1.add_dependency_input_connection('D', 'd_input_1', 'C', 'c_output_1')
        definition_1.add_recipe_input_connection('D', 'd_input_2', 'json_param_1')
        definition_1.add_dependency_input_connection('E', 'e_input_1', 'C', 'c_output_1')

        # No changes in definition 2
        definition_2 = RecipeDefinition(interface_2)
        definition_2.add_job_node('A', 'job_type_1', '1.0', 1)
        definition_2.add_job_node('B', 'job_type_2', '2.0', 1)
        definition_2.add_job_node('C', 'job_type_3', '1.0', 2)
        definition_2.add_recipe_node('D', 'recipe_type_1', 1)
        definition_2.add_job_node('E', 'job_type_4', '1.0', 1)
        definition_2.add_dependency('A', 'B')
        definition_2.add_dependency('A', 'C')
        definition_2.add_dependency('C', 'D')
        definition_2.add_dependency('C', 'E')
        definition_2.add_recipe_input_connection('A', 'input_1', 'file_param_1')
        definition_2.add_dependency_input_connection('B', 'b_input_1', 'A', 'a_output_1')
        definition_2.add_dependency_input_connection('C', 'c_input_1', 'A', 'a_output_2')
        definition_2.add_dependency_input_connection('D', 'd_input_1', 'C', 'c_output_1')
        definition_2.add_recipe_input_connection('D', 'd_input_2', 'json_param_1')
        definition_2.add_dependency_input_connection('E', 'e_input_1', 'C', 'c_output_1')

        recipe_d_forced_nodes = ForcedNodes()
        recipe_d_forced_nodes.add_node('1')
        recipe_d_forced_nodes.add_node('2')
        top_forced_nodes = ForcedNodes()
        top_forced_nodes.add_node('C')
        top_forced_nodes.add_subrecipe('D', recipe_d_forced_nodes)
        diff = RecipeDiff(definition_1, definition_2)
        diff.set_force_reprocess(top_forced_nodes)

        # No recipe input changes so recipe can be reprocessed
        self.assertTrue(diff.can_be_reprocessed)
        self.assertListEqual(diff.reasons, [])
        # Check each node for correct fields
        node_a = diff.graph['A']
        self.assertEqual(node_a.status, NodeDiff.UNCHANGED)
        self.assertFalse(node_a.reprocess_new_node)
        self.assertListEqual(node_a.changes, [])
        node_b = diff.graph['B']
        self.assertEqual(node_b.status, NodeDiff.UNCHANGED)
        self.assertFalse(node_b.reprocess_new_node)
        self.assertListEqual(node_b.changes, [])
        node_c = diff.graph['C']
        self.assertEqual(node_c.status, NodeDiff.UNCHANGED)
        self.assertTrue(node_c.reprocess_new_node)  # Force reprocess
        self.assertListEqual(node_c.changes, [])
        node_d = diff.graph['D']
        self.assertEqual(node_d.status, NodeDiff.UNCHANGED)
        self.assertTrue(node_d.reprocess_new_node)  # Force reprocess
        self.assertListEqual(node_d.changes, [])
        # Check forced nodes object that got passed to recipe node D
        self.assertEqual(node_d.force_reprocess_nodes, recipe_d_forced_nodes)
        node_e = diff.graph['E']
        self.assertEqual(node_e.status, NodeDiff.UNCHANGED)
        self.assertTrue(node_e.reprocess_new_node)  # Force reprocess due to C being forced
        self.assertListEqual(node_e.changes, [])
        # Check nodes to copy, supersede, and unpublish
        self.assertSetEqual(set(diff.get_nodes_to_copy().keys()), {'A', 'B'})
        self.assertSetEqual(set(diff.get_nodes_to_supersede().keys()), {'C', 'D', 'E'})
        self.assertSetEqual(set(diff.get_nodes_to_unpublish().keys()), set())
