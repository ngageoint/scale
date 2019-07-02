from __future__ import unicode_literals

import django
from django.test import TestCase

from data.filter.filter import DataFilter
from data.interface.interface import Interface
from data.interface.parameter import FileParameter, JsonParameter
from job.models import JobType
from job.test import utils as job_test_utils
from recipe.definition.definition import RecipeDefinition
from recipe.diff.forced_nodes import ForcedNodes
from recipe.diff.exceptions import InvalidDiff
from recipe.diff.json.forced_nodes_v6 import convert_forced_nodes_to_v6, ForcedNodesV6


class TestForcedNodesV6(TestCase):

    def setUp(self):
        django.setup()

    def test_convert_forced_nodes_to_v6_empty(self):
        """Tests calling convert_forced_nodes_to_v6() with an empty forced nodes object"""

        empty = ForcedNodes()
        v6 = convert_forced_nodes_to_v6(empty)
        self.assertDictEqual(v6.get_dict(), {'version': '7', 'all': False})

    def test_convert_forced_nodes_to_v6_full(self):
        """Tests calling convert_forced_nodes_to_v6() with a full diff with all types (deleted, new, changed, etc) of nodes"""

        recipe_d_forced_nodes = ForcedNodes()
        recipe_d_forced_nodes.add_node('1')
        recipe_d_forced_nodes.add_node('2')
        top_forced_nodes = ForcedNodes()
        top_forced_nodes.add_node('C')
        top_forced_nodes.add_subrecipe('D', recipe_d_forced_nodes)
        v6 = convert_forced_nodes_to_v6(top_forced_nodes)
        full = {
            'version': '7',
            'all': False,
            'nodes': [u'C', u'D'],
            'sub_recipes': {
                'D': {
                    'version': '7',
                    'all': False,
                    'nodes': ['1', '2']}}}
        self.assertDictEqual(v6.get_dict(), full)

    def test_missing_all(self):
        """Tests calling ForcedNodesV6() with json that doesn't match the schema"""

        json_data = {
            'nodes': ['missing-all']
        }
        #no error without validate call, raises error when validating
        ForcedNodesV6(forced_nodes=json_data, do_validate=False)
        self.assertRaises(InvalidDiff, ForcedNodesV6, json_data, True)

    def test_invalid_additional_property(self):
        """Tests calling ForcedNodesV6() with json that doesn't match the schema"""

        json_data = {
            'all': False,
            'invalid': 'test'
        }
        #no error without validate call, raises error when validating
        ForcedNodesV6(forced_nodes=json_data, do_validate=False)
        self.assertRaises(InvalidDiff, ForcedNodesV6, json_data, True)

    def test_invalid_version(self):
        """Tests calling ForcedNodesV6() with json that doesn't match the schema"""

        json_data = {
            'version': '999',
            'all': False
        }
        self.assertRaises(InvalidDiff, ForcedNodesV6, json_data, False)

    def test_minimal(self):
        """Tests calling ForcedNodesV6() with no args"""

        min = ForcedNodesV6()
        self.assertDictEqual(min.get_dict(), {'version': '7', 'all': False})

    def test_full_json(self):
        """Tests calling ForcedNodesV6() with full valid json"""

        json_data = {
            'version': '6',
            'all': False,
            'nodes': ['job_a_1', 'job_a_2', 'recipe_b', 'recipe_c'],
            'sub_recipes': {
                'recipe_b': {
                    'all': True
                },
                'recipe_c': {
                    'all': False,
                    'nodes': ['job_c_1', 'job_c_2']
                }
            }
        }
        #no error without validate call, raises error when validating
        fn = ForcedNodesV6(forced_nodes=json_data, do_validate=True)
        self.assertDictEqual(fn.get_dict(), json_data)