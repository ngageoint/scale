from __future__ import unicode_literals

import django
from django.test import TransactionTestCase

from ingest.models import Ingest
from job.test import utils as job_test_utils
from recipe.models import Recipe, RecipeInputFile, RecipeNode
from recipe.test import utils as recipe_test_utils
from source.messages.purge_source_file import create_purge_source_file_message, PurgeSourceFile
from source.models import ScaleFile
from storage.models import PurgeResults
from storage.test import utils as storage_test_utils
from trigger.test import utils as trigger_test_utils


class TestPurgeSourceFile(TransactionTestCase):

    def setUp(self):
        django.setup()

        self.trigger = trigger_test_utils.create_trigger_event()

    def test_json(self):
        """Tests coverting a PurgeSourceFile message to and from JSON"""

        # Create a file
        source_file = storage_test_utils.create_file(file_type='SOURCE')
        # Create message
        message = create_purge_source_file_message(source_file_id=source_file.id,
                                                   trigger_id=self.trigger.id)

        # Convert message to JSON and back, and then execute
        message_json_dict = message.to_json()
        new_message = PurgeSourceFile.from_json(message_json_dict)
        result = new_message.execute()

        self.assertTrue(result)

    def test_execute(self):
        """Tests calling PurgeSourceFile.execute() successfully"""

        # Create a file
        source_file = storage_test_utils.create_file(file_type='SOURCE')

        # Create message
        message = create_purge_source_file_message(source_file_id=source_file.id,
                                                   trigger_id=self.trigger.id)
        # Execute message
        result = message.execute()
        self.assertTrue(result)

        # Test to see that the ScaleFile and Ingest records were deleted
        self.assertEqual(ScaleFile.objects.filter(id=source_file.id).count(), 0)
        self.assertEqual(Ingest.objects.filter(source_file=source_file.id).count(), 0)

    def test_execute_results_check(self):
        """Tests calling PurgeSourceFile.execute() successfully"""

        # Create a file
        source_file = storage_test_utils.create_file(file_type='SOURCE')

        # Create PurgeResults entry
        PurgeResults.objects.create(source_file_id=source_file.id, trigger_event=self.trigger)
        self.assertIsNone(PurgeResults.objects.values_list('purge_completed', flat=True).get(
            source_file_id=source_file.id))

        # Create message
        message = create_purge_source_file_message(source_file_id=source_file.id,
                                                   trigger_id=self.trigger.id)
        # Execute message
        result = message.execute()
        self.assertTrue(result)

        # Test to see that the PurgeResults was completed
        self.assertIsNotNone(PurgeResults.objects.values_list('purge_completed', flat=True).get(
            source_file_id=source_file.id))

    def test_execute_with_job(self):
        """Tests calling PurgeSourceFile.execute() successfully"""

        # Create a file
        source_file = storage_test_utils.create_file(file_type='SOURCE')

        # Create a job and other models
        job = job_test_utils.create_job()
        job_test_utils.create_input_file(job=job, input_file=source_file)

        # Create message
        message = create_purge_source_file_message(source_file_id=source_file.id,
                                                   trigger_id=self.trigger.id)
        # Execute message
        result = message.execute()
        self.assertTrue(result)

        # Test to see that a message to purge the job was created
        self.assertEqual(len(message.new_messages), 1)
        for msg in message.new_messages:
            self.assertEqual(msg.job_id, job.id)
            self.assertEqual(msg.type, 'spawn_delete_files_job')

    def test_execute_with_recipe(self):
        """Tests calling PurgeSourceFile.execute() successfully"""

        # Create a file
        source_file = storage_test_utils.create_file(file_type='SOURCE')

        # Create a recipe and other models
        recipe = recipe_test_utils.create_recipe()
        recipe_test_utils.create_input_file(recipe=recipe, input_file=source_file)

        # Create message
        message = create_purge_source_file_message(source_file_id=source_file.id,
                                                   trigger_id=self.trigger.id)

        # Execute message
        result = message.execute()
        self.assertTrue(result)

        # Test to see that a message to purge the recipe was created
        self.assertEqual(len(message.new_messages), 1)
        for msg in message.new_messages:
            self.assertEqual(msg.recipe_id, recipe.id)
            self.assertEqual(msg.type, 'purge_recipe')
