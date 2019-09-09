from __future__ import unicode_literals

import django
import copy
from django.test import TestCase

from batch.definition.definition import BatchDefinition
from batch.messages.create_batch_recipes import create_batch_recipes_message, CreateBatchRecipes
from batch.test import utils as batch_test_utils
from data.data.json.data_v6 import DataV6
from data.data.data import Data
from data.test import utils as data_test_utils
from job.test import utils as job_test_utils
from recipe.diff.forced_nodes import ForcedNodes
from recipe.test import utils as recipe_test_utils
from storage.test import utils as storage_test_utils


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

        # Create a dataset of 6 files
        dataset_def = {
            'parameters': {'files': [{'media_types': ['image/png'], 'required': True, 'multiple': False, 'name': 'INPUT_IMAGE'}],
            'json': []}
        }
        the_dataset = data_test_utils.create_dataset(definition=dataset_def)
        workspace = storage_test_utils.create_workspace()
        src_file_a = storage_test_utils.create_file(file_name='input_a.PNG', file_type='SOURCE', media_type='image/png',
                                              file_size=10, data_type_tags=['type'], file_path='the_path',
                                              workspace=workspace)
        src_file_b = storage_test_utils.create_file(file_name='input_b.PNG', file_type='SOURCE', media_type='image/png',
                                              file_size=10, data_type_tags=['type'], file_path='the_path',
                                              workspace=workspace)
        data_list = []
        data_dict = {
            'version': '6',
            'files': {'INPUT_IMAGE': [src_file_a.id]},
            'json': {}
        }
        data_list.append(DataV6(data=data_dict).get_dict())
        data_dict = {
            'version': '6',
            'files': {'INPUT_IMAGE': [src_file_b.id]},
            'json': {}
        }
        data_list.append(DataV6(data=data_dict).get_dict())
        member_2 = data_test_utils.create_dataset_members(dataset=the_dataset, data_list=data_list)
        
        # Create the batch 
        batch_definition = BatchDefinition()
        batch_definition.dataset = the_dataset.id
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
        # Should be two create_recipes message for the two files in the dataset
        self.assertEqual(len(new_message.new_messages), 2)
        
        # Verify each message has a different input
        src_ids = [src_file_a.id, src_file_b.id]
        for message in new_message.new_messages:
            self.assertEqual(message.type, 'create_recipes')
            self.assertEqual(message.create_recipes_type, 'new-recipe')
            file_id = DataV6(message.recipe_input_data).get_data().values['INPUT_IMAGE'].file_ids[0]
            self.assertTrue(file_id in src_ids)
            src_ids.remove(file_id)
            
        # Test re-processing existing recipes    
        data_dict = {
            'version': '6',
            'files': {'INPUT_IMAGE': [src_file_a.id]},
            'json': {}
        }
        
        recipe_1 = recipe_test_utils.create_recipe(recipe_type=recipe_type, input=data_dict)
        data_dict = {
            'version': '6',
            'files': {'INPUT_IMAGE': [src_file_b.id]},
            'json': {}
        }
        
        recipe_2 = recipe_test_utils.create_recipe(recipe_type=recipe_type, input=data_dict)
        recipe_test_utils.process_recipe_inputs([recipe_1.id, recipe_2.id])
        
        batch_definition_2 = BatchDefinition()
        batch_definition_2.dataset = the_dataset.id
        forced_nodes = ForcedNodes()
        forced_nodes.all_nodes = True
        batch_definition_2.forced_nodes = forced_nodes
        batch_2 = batch_test_utils.create_batch(recipe_type=recipe_type, definition=batch_definition_2)
        
        # Create the message
        message = create_batch_recipes_message(batch_2.id)
        
        # Convert message to JSON and back, and then execute
        message_json_dict_2 = message.to_json()
        new_message_2 = CreateBatchRecipes.from_json(message_json_dict_2)
        result_2 = new_message_2.execute()
    
        self.assertTrue(result_2)
        self.assertEqual(len(new_message_2.new_messages), 1)
        message = new_message_2.new_messages[0]
        self.assertEqual(message.type, 'create_recipes')
        self.assertEqual(message.create_recipes_type, 'reprocess')
        self.assertSetEqual(set(message.root_recipe_ids), {recipe_1.id, recipe_2.id})
        
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
        
        # Create a dataset of 6 files
        dataset_def = {
            'parameters': {'files': [{'media_types': ['image/png'], 'required': True, 'multiple': False, 'name': 'INPUT_IMAGE'}],
            'json': []}
        }
        the_dataset = data_test_utils.create_dataset(definition=dataset_def)
        workspace = storage_test_utils.create_workspace()
        
        # Create 6 files
        src_file_ids = []
        data_list = []
        for i in range(0,6):
            file_name = 'input_%d.png' % i
            src_file =  storage_test_utils.create_file(file_name=file_name, file_type='SOURCE', media_type='image/png',
                                              file_size=10, data_type_tags=['type'], file_path='the_path',
                                              workspace=workspace)
            src_file_ids.append(src_file.id)
            data_dict = {
                'version': '6',
                'files': {'INPUT_IMAGE': [src_file.id]},
                'json': {}
            }
            data_list.append(DataV6(data=data_dict).get_dict())
        members = data_test_utils.create_dataset_members(dataset=the_dataset, data_list=data_list)

        batch_definition = BatchDefinition()
        batch_definition.dataset = the_dataset.id
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
        
        # Should be 6 messages, one for next create_batch_recipes and 5 for creating new recipes
        self.assertEqual(len(message.new_messages), 6)
        
        # Create batch message
        batch_recipes_message = message.new_messages[0]
        self.assertEqual(batch_recipes_message.type, 'create_batch_recipes')
        self.assertEqual(batch_recipes_message.current_dataset_file_id, src_file_ids[1])
        self.assertFalse(batch_recipes_message.is_prev_batch_done)
        
        from recipe.models import Recipe
        # Verify each message has a different input and execute
        src_ids = copy.deepcopy(src_file_ids)
        for msg in message.new_messages[1:]:
            self.assertEqual(msg.type, 'create_recipes')
            self.assertEqual(msg.create_recipes_type, 'new-recipe')
            file_id = DataV6(msg.recipe_input_data).get_data().values['INPUT_IMAGE'].file_ids[0]
            self.assertTrue(file_id in src_ids)
            src_ids.remove(file_id)
            
            # Execute the create_recipes messages
            result = msg.execute()
            self.assertTrue(result)
        
        # Verify 5 recipes have been created and they have the proper input files:
        recipes = Recipe.objects.all()
        self.assertEqual(len(recipes), 5)
        src_ids = copy.deepcopy(src_file_ids)
        for recipe in recipes:
            self.assertEqual(recipe.recipe_type.name, new_batch.recipe_type.name)
            file_id = recipe.get_input_data().values['INPUT_IMAGE'].file_ids[0]
            self.assertTrue(file_id in src_ids)
            src_ids.remove(file_id)
        
        # Execute next create_batch_recipes messages
        result = batch_recipes_message.execute()
        self.assertTrue(result)
        # Should only have one last create_recipes message
        self.assertEqual(len(batch_recipes_message.new_messages), 1)
        create_recipes_message = batch_recipes_message.new_messages[0]
        self.assertTrue(batch_recipes_message.is_prev_batch_done)
        self.assertEqual(create_recipes_message.type, 'create_recipes')
        self.assertEqual(create_recipes_message.create_recipes_type, 'new-recipe')
        self.assertEqual(create_recipes_message.batch_id, new_batch.id)
        self.assertEqual(create_recipes_message.event_id, new_batch.event_id)
        self.assertEqual(create_recipes_message.recipe_type_name, new_batch.recipe_type.name)
        self.assertEqual(create_recipes_message.recipe_type_rev_num, new_batch.recipe_type.revision_num)
        
    def test_execute_reprocess(self):
        """Tests calling CreateBatchRecipes.execute() successfully when re-processing recipes"""
        
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
        sub_recipe_type = recipe_test_utils.create_recipe_type_v6(definition=recipe_def)
        
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

        # Create a dataset of 6 files
        dataset_def = {
            'parameters': {'files': [{'media_types': ['image/png'], 'required': True, 'multiple': False, 'name': 'INPUT_IMAGE'}],
            'json': []}
        }
        the_dataset = data_test_utils.create_dataset(definition=dataset_def)
        workspace = storage_test_utils.create_workspace()
        
        # Create 6 files & recipes to go along
        src_file_ids = []
        recipe_ids = []
        data_list = []
        for i in range(0,6):
            file_name = 'input_%d.png' % i
            src_file =  storage_test_utils.create_file(file_name=file_name, file_type='SOURCE', media_type='image/png',
                                              file_size=10, data_type_tags=['type'], file_path='the_path',
                                              workspace=workspace)
            src_file_ids.append(src_file.id)
            data_dict = {
                'version': '6',
                'files': {'INPUT_IMAGE': [src_file.id]},
                'json': {}
            }
            data_list.append(DataV6(data=data_dict).get_dict())
            recipe = recipe_test_utils.create_recipe(recipe_type=recipe_type, input=data_dict)
            recipe_ids.append(recipe.id)
        
        members = data_test_utils.create_dataset_members(dataset=the_dataset, data_list=data_list)
        recipe_test_utils.process_recipe_inputs(recipe_ids)

        batch_definition = BatchDefinition()
        batch_definition.dataset = the_dataset.id
        batch_definition.supersedes = True
        forced_nodes = ForcedNodes()
        forced_nodes.all_nodes = True
        batch_definition.forced_nodes = forced_nodes
        new_batch = batch_test_utils.create_batch(recipe_type=recipe_type, definition=batch_definition)
        
        # Create message
        message = batch.messages.create_batch_recipes.CreateBatchRecipes()
        message.batch_id = new_batch.id
        
        # Execute message
        result = message.execute()
        self.assertTrue(result)
        self.assertEqual(len(message.new_messages), 2)
        
        batch_recipes_message = message.new_messages[0]
        create_recipes_message = message.new_messages[1]
        self.assertEqual(batch_recipes_message.type, 'create_batch_recipes')
        self.assertEqual(batch_recipes_message.batch_id, new_batch.id)
        self.assertFalse(batch_recipes_message.is_prev_batch_done)
        self.assertEqual(batch_recipes_message.current_recipe_id, recipe_ids[1])
        
        # Test the create_recipes_message
        self.assertEqual(create_recipes_message.type, 'create_recipes')
        self.assertSetEqual(set(create_recipes_message.root_recipe_ids), {recipe_ids[5], recipe_ids[4], recipe_ids[3],
                                                                          recipe_ids[2], recipe_ids[1]})
        self.assertEqual(create_recipes_message.batch_id, new_batch.id)
        self.assertEqual(create_recipes_message.event_id, new_batch.event_id)
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
        self.assertSetEqual(set(create_recipes_message.root_recipe_ids), {recipe_ids[0]})
        self.assertEqual(create_recipes_message.batch_id, new_batch.id)
        self.assertEqual(create_recipes_message.event_id, new_batch.event_id)
        self.assertEqual(create_recipes_message.recipe_type_name, new_batch.recipe_type.name)
        self.assertEqual(create_recipes_message.recipe_type_rev_num, new_batch.recipe_type.revision_num)
        
        # Test setting supersedes to false and make sure we don't have any reprocess messages
        batch_definition_2 = BatchDefinition()
        batch_definition_2.dataset = the_dataset.id
        batch_definition_2.supersedes = False
        forced_nodes = ForcedNodes()
        forced_nodes.all_nodes = True
        batch_definition_2.forced_nodes = forced_nodes
        new_batch_2 = batch_test_utils.create_batch(recipe_type=recipe_type, definition=batch_definition_2)
        
        # Create message
        message_2 = batch.messages.create_batch_recipes.CreateBatchRecipes()
        message_2.batch_id = new_batch_2.id
        # Execute message
        result_2 = message_2.execute()
        self.assertTrue(result_2)
        self.assertEqual(len(message_2.new_messages), 6)
        
        batch_recipes_message_2 = message_2.new_messages[0]
        self.assertEqual(batch_recipes_message_2.type, 'create_batch_recipes')
        self.assertEqual(batch_recipes_message_2.batch_id, new_batch_2.id)
        self.assertFalse(batch_recipes_message_2.is_prev_batch_done)
        
        # Make sure we've got 5 create-new-recipe messages
        for msg in message_2.new_messages[1:]:
            self.assertEqual(msg.create_recipes_type, 'new-recipe')
            self.assertEqual(msg.batch_id, new_batch_2.id)
            self.assertEqual(msg.event_id, new_batch_2.event_id)
            self.assertEqual(msg.recipe_type_name, new_batch_2.recipe_type.name)
            self.assertEqual(msg.recipe_type_rev_num, new_batch_2.recipe_type.revision_num)
            
        # Execute next create_batch_recipes messages
        result_3 = batch_recipes_message_2.execute()
        self.assertTrue(result_3)

        # Should only have one last rcreate_recipes message
        self.assertEqual(len(batch_recipes_message_2.new_messages), 1)
        create_recipes_message_3 = batch_recipes_message_2.new_messages[0]
        self.assertTrue(batch_recipes_message_2.is_prev_batch_done)
        self.assertEqual(create_recipes_message_3.type, 'create_recipes')
        self.assertEqual(create_recipes_message_3.batch_id, new_batch_2.id)
        self.assertEqual(create_recipes_message_3.event_id, new_batch_2.event_id)
        self.assertEqual(create_recipes_message_3.recipe_type_name, new_batch_2.recipe_type.name)
        self.assertEqual(create_recipes_message_3.recipe_type_rev_num, new_batch_2.recipe_type.revision_num)
        
        
    def test_execute_forced_nodes(self):
        """Tests calling CreateBatchRecipes.execute() when only specific nodes are forced"""
        
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

        # Create a dataset of 6 files
        dataset_def = {
            'parameters': {'files': [{'media_types': ['image/png'], 'required': True, 'multiple': False, 'name': 'INPUT_IMAGE'}],
            'json': []}
        }
        the_dataset = data_test_utils.create_dataset(definition=dataset_def)
        workspace = storage_test_utils.create_workspace()
        
        # Create 6 files & recipes to go along
        src_file_ids = []
        recipe_ids = []
        data_list = []
        for i in range(0,6):
            file_name = 'input_%d.png' % i
            src_file =  storage_test_utils.create_file(file_name=file_name, file_type='SOURCE', media_type='image/png',
                                              file_size=10, data_type_tags=['type'], file_path='the_path',
                                              workspace=workspace)
            src_file_ids.append(src_file.id)
            data_dict = {
                'version': '6',
                'files': {'INPUT_IMAGE': [src_file.id]},
                'json': {}
            }
            data_list.append(DataV6(data=data_dict).get_dict())
            recipe = recipe_test_utils.create_recipe(recipe_type=recipe_type, input=data_dict)
            recipe_ids.append(recipe.id)
        members = data_test_utils.create_dataset_members(dataset=the_dataset, data_list=data_list)
        recipe_test_utils.process_recipe_inputs(recipe_ids)

        batch_definition = BatchDefinition()
        batch_definition.dataset = the_dataset.id
        forced_nodes = ForcedNodes()
        forced_nodes.add_node('node_d')
        forced_nodes.all_nodes = False
        batch_definition.forced_nodes = forced_nodes
        
        new_batch = batch_test_utils.create_batch(recipe_type=recipe_type, definition=batch_definition)

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
