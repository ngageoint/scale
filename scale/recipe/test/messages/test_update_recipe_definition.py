from __future__ import unicode_literals

import django
from django.test import TestCase

from job.models import JobType
from job.test import utils as job_test_utils
from recipe.messages.update_recipe_definition import (create_sub_update_recipe_definition_message, 
                                                      create_job_update_recipe_definition_message, 
                                                      UpdateRecipeDefinition)
from recipe.models import RecipeType
from recipe.test import utils as recipe_test_utils


class TestUpdateRecipeDefinition(TestCase):

    def setUp(self):
        django.setup()
        
        self.jt = job_test_utils.create_seed_job_type()
        self.jt2 = job_test_utils.create_seed_job_type(manifest=job_test_utils.MINIMUM_MANIFEST)

        def_v6_dict_sub = {'version': '6',
                       'input': { 'files': [],
                                  'json': []},
                       'nodes': {'node_a': {'dependencies': [],
                                            'input': {},
                                            'node_type': {'node_type': 'job', 'job_type_name': self.jt2.name,
                                                          'job_type_version': self.jt2.version, 'job_type_revision': self.jt2.revision_num}}}}
        
        self.sub = recipe_test_utils.create_recipe_type_v6(definition=def_v6_dict_sub)
        
        def_v6_dict_main = {'version': '6',
                       'input': {'files': [{'name': 'INPUT_IMAGE', 'media_types': ['image/tiff'], 'required': True,
                                            'multiple': False}],
                                 'json': [{'name': 'bar', 'type': 'string', 'required': False}]},
                       'nodes': {'node_a': {'dependencies': [],
                                            'input': {'INPUT_IMAGE': {'type': 'recipe', 'input': 'INPUT_IMAGE'}},
                                            'node_type': {'node_type': 'job', 'job_type_name': self.jt.name,
                                                          'job_type_version': self.jt.version, 'job_type_revision': self.jt.revision_num}},
                                 'node_b': {'dependencies': [{'name': 'node_a'}],
                                            'input': {'INPUT_IMAGE': {'type': 'dependency', 'node': 'node_a',
                                                                  'output': 'OUTPUT_IMAGE'}},
                                            'node_type': {'node_type': 'job', 'job_type_name': self.jt.name,
                                                          'job_type_version': self.jt.version, 'job_type_revision': self.jt.revision_num}},
                                 'node_c': {'dependencies': [{'name': 'node_b'}],
                                            'input': {'input_a': {'type': 'recipe', 'input': 'bar'},
                                                      'input_b': {'type': 'dependency', 'node': 'node_b',
                                                                  'output': 'OUTPUT_IMAGE'}},
                                            'node_type': {'node_type': 'recipe', 'recipe_type_name': self.sub.name,
                                                          'recipe_type_revision': self.sub.revision_num}}}}
                                                          
        self.rt = recipe_test_utils.create_recipe_type_v6(definition=def_v6_dict_main)
        
    def test_json(self):
        """Tests converting an UpdateRecipeDefinition message to and from JSON"""

        # Create message
        sub_message = create_sub_update_recipe_definition_message(self.sub.id, self.sub.id)
        job_message = create_job_update_recipe_definition_message(self.rt.id, self.jt.id)

        # Convert message to JSON and back, and then execute
        sub_message_json_dict = sub_message.to_json()
        new_sub_message = UpdateRecipeDefinition.from_json(sub_message_json_dict)
        result = new_sub_message.execute()
        self.assertTrue(result)
        
        # Convert message to JSON and back, and then execute
        job_message_json_dict = job_message.to_json()
        new_job_message = UpdateRecipeDefinition.from_json(job_message_json_dict)
        result = new_job_message.execute()
        self.assertTrue(result)


    def test_execute(self):
        """Tests calling UpdateRecipeDefinition.execute() successfully"""
        
        # Create new revisions of job types
        job_test_utils.edit_job_type_v6(job_type=self.jt, manifest_dict=self.jt.manifest)
        job_test_utils.edit_job_type_v6(job_type=self.jt2, manifest_dict=self.jt2.manifest)
        
        # Create messages
        job_message = create_job_update_recipe_definition_message(self.rt.id, self.jt.id)
        job_message2 = create_job_update_recipe_definition_message(self.sub.id, self.jt2.id)
        
        result = job_message.execute()
        self.assertTrue(result)
        updated_rt = RecipeType.objects.get(id=self.rt.id)
        nodes = updated_rt.get_definition().get_job_nodes(job_type_name=self.jt.name,
                                                               job_type_version=self.jt.version)
        self.assertEqual(nodes[0].revision_num, self.jt.revision_num + 1)

        result = job_message2.execute()
        self.assertTrue(result)
        #ensure we have a new message to update the parent recipe
        self.assertEqual(len(job_message2.new_messages), 1)
        result = job_message2.new_messages[0].execute()
        self.assertTrue(result)

        updated_rt = RecipeType.objects.get(id=self.rt.id)
        nodes = updated_rt.get_definition().get_recipe_nodes(recipe_type_name=self.sub.name)
        self.assertEqual(nodes[0].revision_num, self.sub.revision_num + 1)
