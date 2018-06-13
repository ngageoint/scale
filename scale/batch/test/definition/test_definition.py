from __future__ import unicode_literals

import django
from django.test import TestCase
from mock import patch

from batch.definition.exceptions import InvalidDefinition
from batch.definition.json.definition_v6 import BatchDefinitionV6
from batch.test import utils as batch_test_utils
from recipe.test import utils as recipe_test_utils


class TestBatchDefinition(TestCase):

    def setUp(self):
        django.setup()

    def test_create_from_json(self):
        """Tests creating a BatchDefinition from a JSON"""

        # Valid previous batch definition
        definition = {'version': '6', 'previous_batch': {'root_batch_id': 1234, 'job_names': ['job_a', 'job_b'],
                                                         'all_jobs': True}}
        json = BatchDefinitionV6(definition=definition, do_validate=True)
        self.assertIsNotNone(json.get_definition())

    def test_validate(self):
        """Tests calling BatchDefinition.validate()"""

        recipe_type_1 = recipe_test_utils.create_recipe_type()
        recipe_type_2 = recipe_test_utils.create_recipe_type()

        bad_recipe_type_prev_batch = batch_test_utils.create_batch(recipe_type=recipe_type_1)
        still_creating_prev_batch = batch_test_utils.create_batch(recipe_type=recipe_type_2)
        prev_batch = batch_test_utils.create_batch(recipe_type=recipe_type_2, is_creation_done=True, recipes_total=10)
        batch = batch_test_utils.create_batch(recipe_type=recipe_type_2)
        

        # No recipes would be created
        json_dict = {'version': '6'}
        json = BatchDefinitionV6(definition=json_dict)
        definition = json.get_definition()
        batch.superseded_batch = None
        self.assertRaises(InvalidDefinition, definition.validate, batch)

        # Mismatched recipe types
        json_dict = {'version': '6', 'previous_batch': {'root_batch_id': bad_recipe_type_prev_batch.root_batch_id}}
        json = BatchDefinitionV6(definition=json_dict)
        definition = json.get_definition()
        batch.superseded_batch = bad_recipe_type_prev_batch
        self.assertRaises(InvalidDefinition, definition.validate, batch)

        # Previous batch not done creating recipes
        json_dict = {'version': '6', 'previous_batch': {'root_batch_id': still_creating_prev_batch.root_batch_id}}
        json = BatchDefinitionV6(definition=json_dict)
        definition = json.get_definition()
        batch.superseded_batch = still_creating_prev_batch
        self.assertRaises(InvalidDefinition, definition.validate, batch)

        # Previous batch cannot be reprocessed
        json_dict = {'version': '6', 'previous_batch': {'root_batch_id': prev_batch.root_batch_id}}
        json = BatchDefinitionV6(definition=json_dict)
        definition = json.get_definition()
        batch.superseded_batch = prev_batch

        with patch('batch.definition.definition.RecipeGraphDelta') as mock_delta:
            instance = mock_delta.return_value
            instance.can_be_reprocessed = False
            self.assertRaises(InvalidDefinition, definition.validate, batch)

        # Valid definition with previous batch
        json_dict = {'version': '6', 'previous_batch': {'root_batch_id': prev_batch.root_batch_id}}
        json = BatchDefinitionV6(definition=json_dict)
        definition = json.get_definition()
        batch.superseded_batch = prev_batch
        definition.validate(batch)
