from __future__ import unicode_literals

import django
from django.test import TestCase

from job.test import utils as job_test_utils
from recipe.messages.update_recipes import UpdateRecipes
from recipe.test import utils as recipe_test_utils


class TestBlockedJobs(TestCase):

    def setUp(self):
        django.setup()

    def test_json(self):
        """Tests coverting a UpdateRecipes message to and from JSON"""

        self.job_1_failed = job_test_utils.create_job(status='FAILED')
        self.job_1_pending = job_test_utils.create_job(status='PENDING')
        definition_1 = {
            'version': '1.0',
            'input_data': [],
            'jobs': [{
                'name': 'job_failed',
                'job_type': {
                    'name': self.job_1_failed.job_type.name,
                    'version': self.job_1_failed.job_type.version,
                },
            }, {
                'name': 'job_pending',
                'job_type': {
                    'name': self.job_1_pending.job_type.name,
                    'version': self.job_1_pending.job_type.version,
                },
                'dependencies': [{
                    'name': 'job_failed',
                }],
            }],
        }
        self.recipe_type_1 = recipe_test_utils.create_recipe_type(definition=definition_1)
        self.recipe_1 = recipe_test_utils.create_recipe(recipe_type=self.recipe_type_1)
        recipe_test_utils.create_recipe_job(recipe=self.recipe_1, job_name='job_failed', job=self.job_1_failed)
        recipe_test_utils.create_recipe_job(recipe=self.recipe_1, job_name='job_pending', job=self.job_1_pending)

        self.job_2_running = job_test_utils.create_job(status='RUNNING')
        self.job_2_blocked = job_test_utils.create_job(status='BLOCKED')
        definition_2 = {
            'version': '1.0',
            'input_data': [],
            'jobs': [{
                'name': 'job_running',
                'job_type': {
                    'name': self.job_2_running.job_type.name,
                    'version': self.job_2_running.job_type.version,
                },
            }, {
                'name': 'job_blocked',
                'job_type': {
                    'name': self.job_2_blocked.job_type.name,
                    'version': self.job_2_blocked.job_type.version,
                },
                'dependencies': [{
                    'name': 'job_running',
                }],
            }],
        }
        self.recipe_type_2 = recipe_test_utils.create_recipe_type(definition=definition_2)
        self.recipe_2 = recipe_test_utils.create_recipe(recipe_type=self.recipe_type_2)
        recipe_test_utils.create_recipe_job(recipe=self.recipe_2, job_name='job_running', job=self.job_2_running)
        recipe_test_utils.create_recipe_job(recipe=self.recipe_2, job_name='job_blocked', job=self.job_2_blocked)

        # Add recipes to message
        message = UpdateRecipes()
        if message.can_fit_more():
            message.add_recipe(self.recipe_1.id)
        if message.can_fit_more():
            message.add_recipe(self.recipe_2.id)

        # Convert message to JSON and back, and then execute
        message_json_dict = message.to_json()
        new_message = UpdateRecipes.from_json(message_json_dict)
        result = new_message.execute()

        self.assertTrue(result)
        self.assertEqual(len(new_message.new_messages), 2)

    def test_execute(self):
        """Tests calling UpdateRecipes.execute() successfully"""

        self.job_1_failed = job_test_utils.create_job(status='FAILED')
        self.job_1_pending = job_test_utils.create_job(status='PENDING')
        definition_1 = {
            'version': '1.0',
            'input_data': [],
            'jobs': [{
                'name': 'job_failed',
                'job_type': {
                    'name': self.job_1_failed.job_type.name,
                    'version': self.job_1_failed.job_type.version,
                },
            }, {
                'name': 'job_pending',
                'job_type': {
                    'name': self.job_1_pending.job_type.name,
                    'version': self.job_1_pending.job_type.version,
                },
                'dependencies': [{
                    'name': 'job_failed',
                }],
            }],
        }
        self.recipe_type_1 = recipe_test_utils.create_recipe_type(definition=definition_1)
        self.recipe_1 = recipe_test_utils.create_recipe(recipe_type=self.recipe_type_1)
        recipe_test_utils.create_recipe_job(recipe=self.recipe_1, job_name='job_failed', job=self.job_1_failed)
        recipe_test_utils.create_recipe_job(recipe=self.recipe_1, job_name='job_pending', job=self.job_1_pending)

        self.job_2_running = job_test_utils.create_job(status='RUNNING')
        self.job_2_blocked = job_test_utils.create_job(status='BLOCKED')
        definition_2 = {
            'version': '1.0',
            'input_data': [],
            'jobs': [{
                'name': 'job_running',
                'job_type': {
                    'name': self.job_2_running.job_type.name,
                    'version': self.job_2_running.job_type.version,
                },
            }, {
                'name': 'job_blocked',
                'job_type': {
                    'name': self.job_2_blocked.job_type.name,
                    'version': self.job_2_blocked.job_type.version,
                },
                'dependencies': [{
                    'name': 'job_running',
                }],
            }],
        }
        self.recipe_type_2 = recipe_test_utils.create_recipe_type(definition=definition_2)
        self.recipe_2 = recipe_test_utils.create_recipe(recipe_type=self.recipe_type_2)
        recipe_test_utils.create_recipe_job(recipe=self.recipe_2, job_name='job_running', job=self.job_2_running)
        recipe_test_utils.create_recipe_job(recipe=self.recipe_2, job_name='job_blocked', job=self.job_2_blocked)

        # Add recipes to message
        message = UpdateRecipes()
        if message.can_fit_more():
            message.add_recipe(self.recipe_1.id)
        if message.can_fit_more():
            message.add_recipe(self.recipe_2.id)

        # Execute message
        result = message.execute()
        self.assertTrue(result)

        self.assertEqual(len(message.new_messages), 2)
        # Check message types
        blocked_jobs_msg = False
        pending_jobs_msg = False
        for new_msg in message.new_messages:
            if new_msg.type == 'blocked_jobs':
                blocked_jobs_msg = True
            elif new_msg.type == 'pending_jobs':
                pending_jobs_msg = True
        self.assertTrue(blocked_jobs_msg)
        self.assertTrue(pending_jobs_msg)
