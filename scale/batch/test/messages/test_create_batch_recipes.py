from __future__ import unicode_literals

import django
from django.test import TestCase

from batch.definition.definition import BatchDefinition
from batch.messages.create_batch_recipes import create_batch_recipes_message, CreateBatchRecipes
from batch.test import utils as batch_test_utils
from job.test import utils as job_test_utils
from recipe.diff.forced_nodes import ForcedNodes
from recipe.messages.create_recipes import SubRecipe
from recipe.test import utils as recipe_test_utils


class TestCreateBatchRecipes(TestCase):

    def setUp(self):
        django.setup()

    def test_json_new(self):
        """Tests coverting a CreateBatchRecipes message to and from JSON"""
        
        jt_1 = job_test_utils.create_seed_job_type()
        jt_2 = job_test_utils.create_seed_job_type()
        jt_3 = job_test_utils.create_seed_job_type()
        jt_4 = job_test_utils.create_seed_job_type()
        
        recipe_def = {'version': '7',
                            'input': {'files': [{'name': 'INPUT_IMAGE', 'media_types': ['image/png'], 'required': True,
                                                 'multiple': False}],
                                      'json': []},
                            'nodes': {'node_a': {'dependencies': [],
                                                 'input': {'input_a': {'type': 'recipe', 'input': 'INPUT_IMAGE'}},
                                                 'node_type': {'node_type': 'job', 
                                                               'job_type_name': jt_1.name,
                                                               'job_type_version': jt_1.version,
                                                               'job_type_revision': jt_1.revision_num}},
                                      'node_b': {'dependencies':[],
                                                 'input': {'input_a': {'type': 'recipe', 'input': 'INPUT_IMAGE'}},
                                                 'node_type': {'node_type': 'job', 
                                                               'job_type_name': jt_2.name,
                                                               'job_type_version': jt_2.version,
                                                               'job_type_revision': jt_2.revision_num}}}}
        sub_recipe_type = recipe_test_utils.create_recipe_type_v6(definition=recipe_def)
        sub_recipe = recipe_test_utils.create_recipe(recipe_type=sub_recipe_type)
        
        # Recipe with two jobs and one subrecipe (c -> d -> r) 
        recipe_def = {'version': '7',
                            'input': {'files': [{'name': 'INPUT_IMAGE', 'media_types': ['image/png'], 'required': True,
                                                 'multiple': False}],
                                      'json': []},
                            'nodes': {'recipe_node': {'dependencies': [{'name': 'node_d', 'acceptance': True}],
                                                 'input': {'input_a': {'type': 'dependency', 'node': 'node_d',
                                                                           'output': 'OUTPUT_IMAGE'}},
                                                 'node_type': {'node_type': 'recipe', 'recipe_type_name': sub_recipe_type.name,
                                                               'recipe_type_revision':  sub_recipe_type.revision_num}},
                                      'node_c': {'dependencies': [],
                                                 'input': {'INPUT_IMAGE': {'type': 'recipe', 'input': 'INPUT_IMAGE'}},
                                                 'node_type': {'node_type': 'job', 'job_type_name': jt_3.name,
                                                               'job_type_version': jt_3.version,
                                                               'job_type_revision': jt_3.revision_num}},
                                      'node_d': {'dependencies': [{'name': 'node_c', 'acceptance': True}],
                                                 'input': {'INPUT_IMAGE': {'type': 'dependency', 'node': 'node_c',
                                                                           'output': 'OUTPUT_IMAGE'}},
                                                  'node_type': {'node_type': 'job', 'job_type_name': jt_4.name,
                                                               'job_type_version': jt_4.version,
                                                               'job_type_revision': jt_4.revision_num}}}}
        recipe_type = recipe_test_utils.create_recipe_type_v6(definition=recipe_def)
        subs = []
        subs.append(SubRecipe(sub_recipe_type.name, sub_recipe_type.revision_num, 'recipe_node', False))
        
        # Create 6 previous recipes - each with two sub-recipes (18 total)
        recipe_1 = recipe_test_utils.create_recipe(recipe_type=recipe_type)
        recipe_test_utils.create_subrecipes(recipe_1, subs)
        recipe_2 = recipe_test_utils.create_recipe(recipe_type=recipe_type)
        recipe_test_utils.create_subrecipes(recipe_2, subs)
        recipe_3 = recipe_test_utils.create_recipe(recipe_type=recipe_type)
        recipe_test_utils.create_subrecipes(recipe_3, subs)
        
        # Create the batch 
        batch_definition = BatchDefinition()
        batch_definition.dataset = 1
        forced_nodes = ForcedNodes()
        forced_nodes.all_nodes = True
        batch_definition.forced_nodes = forced_nodes
        batch = batch_test_utils.create_batch(recipe_type=recipe_type, definition=batch_definition)
        
        # Create the message
        message = create_batch_recipes_message(batch.id)
        
        # Convert message to JSON and back, and then execute
        message_json_dict = message.to_json()
        new_message = CreateBatchRecipes.from_json(message_json_dict)
        result = new_message.execute()
    
        self.assertTrue(result)
        # Should be one create_recipes message for the three recipes
        self.assertEqual(len(new_message.new_messages), 1)
        message = new_message.new_messages[0]
        self.assertEqual(message.type, 'create_recipes')
        self.assertSetEqual(set(message.root_recipe_ids), {recipe_1.id, recipe_2.id, recipe_3.id})
    
    def test_json_previous(self):
        """Tests coverting a CreateBatchRecipes message to and from JSON"""

        # Previous batch with three recipes
        recipe_type = recipe_test_utils.create_recipe_type_v6()
        prev_batch = batch_test_utils.create_batch(recipe_type=recipe_type, is_creation_done=True, recipes_total=3)
        recipe_1 = recipe_test_utils.create_recipe(batch=prev_batch)
        recipe_2 = recipe_test_utils.create_recipe(batch=prev_batch)
        recipe_3 = recipe_test_utils.create_recipe(batch=prev_batch)

        definition = BatchDefinition()
        definition.root_batch_id = prev_batch.root_batch_id
        batch = batch_test_utils.create_batch(recipe_type=recipe_type, definition=definition)

        # Create message
        message = create_batch_recipes_message(batch.id)

        # Convert message to JSON and back, and then execute
        message_json_dict = message.to_json()
        new_message = CreateBatchRecipes.from_json(message_json_dict)
        result = new_message.execute()

        self.assertTrue(result)
        # Should be one create_recipes message for the three recipes
        self.assertEqual(len(new_message.new_messages), 1)
        message = new_message.new_messages[0]
        self.assertEqual(message.type, 'create_recipes')
        self.assertSetEqual(set(message.root_recipe_ids), {recipe_1.id, recipe_2.id, recipe_3.id})

    def test_execute_new(self):
        """Tests calling CreateBatchRecipes.execute() successfully"""
        
        # Importing module here to patch the max recipe num
        import batch.messages.create_batch_recipes
        batch.messages.create_batch_recipes.MAX_RECIPE_NUM = 5
        
        jt_1 = job_test_utils.create_seed_job_type()
        jt_2 = job_test_utils.create_seed_job_type()
        jt_3 = job_test_utils.create_seed_job_type()
        jt_4 = job_test_utils.create_seed_job_type()
        
        recipe_def = {'version': '7',
                            'input': {'files': [{'name': 'INPUT_IMAGE', 'media_types': ['image/png'], 'required': True,
                                                 'multiple': False}],
                                      'json': []},
                            'nodes': {'node_a': {'dependencies': [],
                                                 'input': {'input_a': {'type': 'recipe', 'input': 'INPUT_IMAGE'}},
                                                 'node_type': {'node_type': 'job', 
                                                               'job_type_name': jt_1.name,
                                                               'job_type_version': jt_1.version,
                                                               'job_type_revision': jt_1.revision_num}},
                                      'node_b': {'dependencies':[],
                                                 'input': {'input_a': {'type': 'recipe', 'input': 'INPUT_IMAGE'}},
                                                 'node_type': {'node_type': 'job', 
                                                               'job_type_name': jt_2.name,
                                                               'job_type_version': jt_2.version,
                                                               'job_type_revision': jt_2.revision_num}}}}
        sub_recipe_type_1 = recipe_test_utils.create_recipe_type_v6(definition=recipe_def)
        sub_recipe_1 = recipe_test_utils.create_recipe(recipe_type=sub_recipe_type_1)
        
        recipe_def = {'version': '7',
                            'input': {'files': [{'name': 'INPUT_IMAGE', 'media_types': ['image/png'], 'required': True,
                                                 'multiple': False}],
                                      'json': []},
                            'nodes': {'node_a': {'dependencies': [],
                                                 'input': {'input_a': {'type': 'recipe', 'input': 'INPUT_IMAGE'}},
                                                 'node_type': {'node_type': 'job', 
                                                               'job_type_name': jt_3.name,
                                                               'job_type_version': jt_3.version,
                                                               'job_type_revision': jt_3.revision_num}},
                                      'node_b': {'dependencies':[],
                                                 'input': {'input_a': {'type': 'recipe', 'input': 'INPUT_IMAGE'}},
                                                 'node_type': {'node_type': 'job', 
                                                               'job_type_name': jt_4.name,
                                                               'job_type_version': jt_4.version,
                                                               'job_type_revision': jt_4.revision_num}}}}
        sub_recipe_type_2 = recipe_test_utils.create_recipe_type_v6(definition=recipe_def)
        sub_recipe_2 = recipe_test_utils.create_recipe(recipe_type=sub_recipe_type_2)
        
        jt_5 = job_test_utils.create_seed_job_type()
        jt_6 = job_test_utils.create_seed_job_type()
        recipe_def = {'version': '7',
                            'input': {'files': [{'name': 'INPUT_IMAGE', 'media_types': ['image/png'], 'required': True,
                                                 'multiple': False}],
                                      'json': []},
                            'nodes': {'recipe_node_a': {'dependencies': [],
                                                 'input': {'input_a': {'type': 'recipe', 'input': 'INPUT_IMAGE'}},
                                                 'node_type': {'node_type': 'recipe', 'recipe_type_name': sub_recipe_type_1.name,
                                                               'recipe_type_revision':  sub_recipe_type_1.revision_num}},
                                      'recipe_node_b': {'dependencies': [{'name': 'node_d', 'acceptance': True}],
                                                 'input': {'input_a': {'type': 'dependency', 'node': 'node_d',
                                                                           'output': 'OUTPUT_IMAGE'}},
                                                 'node_type': {'node_type': 'recipe', 'recipe_type_name': sub_recipe_type_2.name,
                                                               'recipe_type_revision':  sub_recipe_type_2.revision_num}},
                                      'node_c': {'dependencies': [],
                                                 'input': {'INPUT_IMAGE': {'type': 'recipe', 'input': 'INPUT_IMAGE'}},
                                                 'node_type': {'node_type': 'job', 'job_type_name': jt_5.name,
                                                               'job_type_version': jt_5.version,
                                                               'job_type_revision': jt_5.revision_num}},
                                      'node_d': {'dependencies': [{'name': 'node_c', 'acceptance': True}],
                                                 'input': {'INPUT_IMAGE': {'type': 'dependency', 'node': 'node_c',
                                                                           'output': 'OUTPUT_IMAGE'}},
                                                  'node_type': {'node_type': 'job', 'job_type_name': jt_6.name,
                                                               'job_type_version': jt_6.version,
                                                               'job_type_revision': jt_6.revision_num}}}}
        recipe_type = recipe_test_utils.create_recipe_type_v6(definition=recipe_def)
        subs = []
        subs.append(SubRecipe(sub_recipe_type_1.name, sub_recipe_type_1.revision_num, 'recipe_node_a', False))
        subs.append(SubRecipe(sub_recipe_type_2.name, sub_recipe_type_2.revision_num, 'recipe_node_b', False))
        
        # Create 6 previous recipes - each with two sub-recipes (18 total)
        recipe_1 = recipe_test_utils.create_recipe(recipe_type=recipe_type)
        recipe_test_utils.create_subrecipes(recipe_1, subs)
        recipe_2 = recipe_test_utils.create_recipe(recipe_type=recipe_type)
        recipe_test_utils.create_subrecipes(recipe_2, subs)
        recipe_3 = recipe_test_utils.create_recipe(recipe_type=recipe_type)
        recipe_test_utils.create_subrecipes(recipe_3, subs)
        recipe_4 = recipe_test_utils.create_recipe(recipe_type=recipe_type)
        recipe_test_utils.create_subrecipes(recipe_4, subs)
        recipe_5 = recipe_test_utils.create_recipe(recipe_type=recipe_type)
        recipe_test_utils.create_subrecipes(recipe_5, subs)
        recipe_6 = recipe_test_utils.create_recipe(recipe_type=recipe_type)
        recipe_test_utils.create_subrecipes(recipe_6, subs)
        
        batch_definition = BatchDefinition()
        batch_definition.dataset = 1
        forced_nodes = ForcedNodes()
        forced_nodes.all_nodes = True
        batch_definition.forced_nodes = forced_nodes
        
        new_batch = batch_test_utils.create_batch(recipe_type=recipe_type, definition=batch_definition)
        
        # Create message
        message = batch.messages.create_batch_recipes.CreateBatchRecipes()
        message.batch_id = new_batch.id

        # Copy JSON for running same message again later
        message_json = message.to_json()

        # Execute message
        result = message.execute()
        self.assertTrue(result)
        
        # Should be two messages, one for next create_batch_recipes and one for re-processing recipes
        self.assertEqual(len(message.new_messages), 2)
        batch_recipes_message = message.new_messages[0]
        create_recipes_message = message.new_messages[1]
        
        # create_batch_recipes message
        self.assertEqual(batch_recipes_message.type, 'create_batch_recipes')
        self.assertEqual(batch_recipes_message.batch_id, new_batch.id)
        self.assertFalse(batch_recipes_message.is_prev_batch_done)
        self.assertEqual(batch_recipes_message.current_recipe_id, recipe_2.id)
        
        # create_recipes message
        self.assertEqual(create_recipes_message.type, 'create_recipes')
        self.assertSetEqual(set(create_recipes_message.root_recipe_ids), {recipe_2.id, recipe_3.id, recipe_4.id,
                                                                          recipe_5.id, recipe_6.id})
        self.assertEqual(create_recipes_message.batch_id, new_batch.id)
        
        # Execute next create_batch_recipes messages
        result = batch_recipes_message.execute()
        self.assertTrue(result)
        
        # Should only have one last rcreate_recipes message
        self.assertEqual(len(batch_recipes_message.new_messages), 1)
        create_recipes_message = batch_recipes_message.new_messages[0]
        self.assertTrue(batch_recipes_message.is_prev_batch_done)
        self.assertEqual(create_recipes_message.type, 'create_recipes')
        self.assertSetEqual(set(create_recipes_message.root_recipe_ids), {recipe_1.id})
        self.assertEqual(create_recipes_message.batch_id, new_batch.id)
        self.assertEqual(create_recipes_message.event_id, new_batch.event_id)
        self.assertEqual(create_recipes_message.recipe_type_name, new_batch.recipe_type.name)
        self.assertEqual(create_recipes_message.recipe_type_rev_num, new_batch.recipe_type.revision_num)
        

    def test_execute_previous(self):
        """Tests calling CreateBatchRecipes.execute() successfully"""

        # Importing module here to patch the max recipe num
        import batch.messages.create_batch_recipes
        batch.messages.create_batch_recipes.MAX_RECIPE_NUM = 5

        # Previous batch with six recipes
        recipe_type = recipe_test_utils.create_recipe_type_v6()
        prev_batch = batch_test_utils.create_batch(recipe_type=recipe_type, is_creation_done=True, recipes_total=6)
        recipe_1 = recipe_test_utils.create_recipe(batch=prev_batch)
        recipe_2 = recipe_test_utils.create_recipe(batch=prev_batch)
        recipe_3 = recipe_test_utils.create_recipe(batch=prev_batch)
        recipe_4 = recipe_test_utils.create_recipe(batch=prev_batch)
        recipe_5 = recipe_test_utils.create_recipe(batch=prev_batch)
        recipe_6 = recipe_test_utils.create_recipe(batch=prev_batch)

        definition = BatchDefinition()
        definition.root_batch_id = prev_batch.root_batch_id
        new_batch = batch_test_utils.create_batch(recipe_type=recipe_type, definition=definition)

        # Create message
        message = batch.messages.create_batch_recipes.CreateBatchRecipes()
        message.batch_id = new_batch.id

        # Copy JSON for running same message again later
        message_json = message.to_json()

        # Execute message
        result = message.execute()
        self.assertTrue(result)

        # Should be two messages, one for next create_batch_recipes and one for re-processing recipes
        self.assertEqual(len(message.new_messages), 2)
        batch_recipes_message = message.new_messages[0]
        create_recipes_message = message.new_messages[1]
        self.assertEqual(batch_recipes_message.type, 'create_batch_recipes')
        self.assertEqual(batch_recipes_message.batch_id, new_batch.id)
        self.assertFalse(batch_recipes_message.is_prev_batch_done)
        self.assertEqual(batch_recipes_message.current_recipe_id, recipe_2.id)
        self.assertEqual(create_recipes_message.type, 'create_recipes')
        self.assertSetEqual(set(create_recipes_message.root_recipe_ids), {recipe_2.id, recipe_3.id, recipe_4.id,
                                                                          recipe_5.id, recipe_6.id})
        self.assertEqual(create_recipes_message.batch_id, new_batch.id)
        self.assertEqual(create_recipes_message.event_id, new_batch.event_id)
        self.assertIsNone(create_recipes_message.forced_nodes)
        self.assertEqual(create_recipes_message.recipe_type_name, new_batch.recipe_type.name)
        self.assertEqual(create_recipes_message.recipe_type_rev_num, new_batch.recipe_type.revision_num)

        # Test executing message again
        message = batch.messages.create_batch_recipes.CreateBatchRecipes.from_json(message_json)
        result = message.execute()
        self.assertTrue(result)

        # Should have same messages returned
        self.assertEqual(len(message.new_messages), 2)
        batch_recipes_message = message.new_messages[0]
        create_recipes_message = message.new_messages[1]
        self.assertEqual(batch_recipes_message.type, 'create_batch_recipes')
        self.assertEqual(batch_recipes_message.batch_id, new_batch.id)
        self.assertFalse(batch_recipes_message.is_prev_batch_done)
        self.assertEqual(batch_recipes_message.current_recipe_id, recipe_2.id)
        self.assertEqual(create_recipes_message.type, 'create_recipes')
        self.assertSetEqual(set(create_recipes_message.root_recipe_ids), {recipe_2.id, recipe_3.id, recipe_4.id,
                                                                          recipe_5.id, recipe_6.id})
        self.assertEqual(create_recipes_message.batch_id, new_batch.id)
        self.assertEqual(create_recipes_message.event_id, new_batch.event_id)
        self.assertIsNone(create_recipes_message.forced_nodes)
        self.assertEqual(create_recipes_message.recipe_type_name, new_batch.recipe_type.name)
        self.assertEqual(create_recipes_message.recipe_type_rev_num, new_batch.recipe_type.revision_num)

        # Execute next create_batch_recipes messages
        result = batch_recipes_message.execute()
        self.assertTrue(result)

        # Should only have one last rcreate_recipes message
        self.assertEqual(len(batch_recipes_message.new_messages), 1)
        create_recipes_message = batch_recipes_message.new_messages[0]
        self.assertTrue(batch_recipes_message.is_prev_batch_done)
        self.assertEqual(create_recipes_message.type, 'create_recipes')
        self.assertSetEqual(set(create_recipes_message.root_recipe_ids), {recipe_1.id})
        self.assertEqual(create_recipes_message.batch_id, new_batch.id)
        self.assertEqual(create_recipes_message.event_id, new_batch.event_id)
        self.assertIsNone(create_recipes_message.forced_nodes)
        self.assertEqual(create_recipes_message.recipe_type_name, new_batch.recipe_type.name)
        self.assertEqual(create_recipes_message.recipe_type_rev_num, new_batch.recipe_type.revision_num)
