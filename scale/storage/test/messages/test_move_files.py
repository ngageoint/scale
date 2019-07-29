from __future__ import unicode_literals

import os

import django
from django.test import TestCase

from storage.messages.move_files import create_move_file_message, MoveFile
from storage.models import ScaleFile
from storage.test import utils as storage_test_utils


class TestMoveFiles(TestCase):

    def setUp(self):
        django.setup()

        self.workspace = storage_test_utils.create_workspace(base_url="http:/scale.com/")
        self.file = storage_test_utils.create_file(workspace=self.workspace)

    def test_json(self):
        """Tests coverting a MoveFiles message to and from JSON"""

        message = MoveFile()
        message.file_id = self.file.id

        # Convert message to JSON and back, and then execute
        message_json_dict = message.to_json()
        new_message = MoveFile.from_json(message_json_dict)
        result = new_message.execute()
        self.assertTrue(result)

        # check updated metadata
        updated_file = ScaleFile.objects.get(pk=self.file.id)
        self.assertEqual(updated_file.meta_data['url'], 'http:/scale.com/file/path/my_test_file.txt')

    def test_execute(self):
        """Tests calling MoveFile.execute() successfully"""

        message = MoveFile()
        message.file_id = self.file.id

        result = message.execute()
        self.assertTrue(result)

        # check updated metadata
        updated_file = ScaleFile.objects.get(pk=self.file.id)
        self.assertEqual(updated_file.meta_data['url'], 'http:/scale.com/file/path/my_test_file.txt')

    def test_create_message(self):
        """
        Tests calling the create message function for MoveFile
        """

        message = create_move_file_message(file_id=1)
        self.assertEqual(message.file_id, 1)

