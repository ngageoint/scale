from __future__ import unicode_literals

import django
from django.test import TransactionTestCase
from mock import patch

from batch.management.commands.scale_batch_creator import Command as BatchCommand
from batch.test import utils as batch_test_utils
from messaging.backends.amqp import AMQPMessagingBackend
from messaging.backends.factory import add_message_backend
from recipe.test import utils as recipe_test_utils


class TestBatchCreator(TransactionTestCase):

    fixtures = ['batch_job_types.json']

    def setUp(self):
        django.setup()

        add_message_backend(AMQPMessagingBackend)

        # mock out threading.start

        self.recipe_type = recipe_test_utils.create_recipe_type_v6()
        self.batch = batch_test_utils.create_batch(recipe_type=self.recipe_type)

    def test_missing_batch(self):
        """Tests calling command for an invalid batch"""

        cmd = BatchCommand()
        self.assertRaises(SystemExit, cmd.run_from_argv, ['manage.py', 'scale_batch_creator', '-i', '123'])

    @patch('batch.views.CommandMessageManager')
    @patch('batch.management.commands.scale_batch_creator.Batch.objects')
    def test_successful(self, mock_msg_mgr, mock_batch_manager):
        """Tests calling command for a valid batch"""

        cmd = BatchCommand()
        cmd.run_from_argv(['manage.py', 'scale_batch_creator', '-i', str(self.batch.id)])

        batches = mock_batch_manager.get_batches_v6()

        # mock_batch_manager.schedule_recipes.assert_called_with(self.batch.id)
