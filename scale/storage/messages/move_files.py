"""Defines a command message that moves files to a different workspace/location"""
from __future__ import unicode_literals

import logging

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from messaging.messages.message import CommandMessage
from storage.models import ScaleFile


logger = logging.getLogger(__name__)


def create_move_file_message(file_id):
    """Creates message to move the given file

    :param file_id: The id of the file to update
    :type file_id: int
    :return: The message
    :rtype: :class:`storage.messages.move_files.MoveFiles`
    """

    message = MoveFile()
    message.file_id = file_id

    return message

class MoveFile(CommandMessage):
    """Command message that moves a scale_file model
    """

    def __init__(self):
        """Constructor
        """

        super(MoveFile, self).__init__('move_files')

        self.file_id = None

    def to_json(self):
        """See :meth:`messaging.messages.message.CommandMessage.to_json`
        """

        return {
            'file_id': self.file_id
        }

    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`
        """

        message = MoveFile()
        message.file_id = json_dict['file_id']

        return message

    def execute(self):
        """See :meth:`messaging.messages.message.CommandMessage.execute`
        """

        file_to_move = ScaleFile.objects.get(pk=self.file_id)
        
        file_to_move.meta_data['url'] = file_to_move.url
        file_to_move.save()

        return True
