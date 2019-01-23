"""Defines a command message that moves files to a different workspace/location"""
from __future__ import unicode_literals

import logging

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from messaging.messages.message import CommandMessage
from storage.models import ScaleFile

# This is the maximum number of file models that can fit in one message. This maximum ensures that every message of this
# type is less than 25 KiB long.
MAX_NUM = 100


logger = logging.getLogger(__name__)


def create_move_files_messages(files, new_workspace=None, new_uri=None):
    """Creates messages to move the given files

    :param files: The list of file IDs to move
    :type files: [collections.namedtuple]
    :param new_workspace: The name of the workspace to move the files to
    :type new_workspace: string
    :param new_uri: The uri to move the files to
    :type new_uri: string
    :return: The list of messages
    :rtype: list
    """

    messages = []

    message = None
    for scale_file in files:
        if not message:
            message = MoveFiles()
        elif not message.can_fit_more():
            messages.append(message)
            message = MoveFiles()
        message.add_file(scale_file.id)
        message.new_workspace = new_workspace
        message.new_uri = new_uri
    if message:
        messages.append(message)

    return messages

class MoveFiles(CommandMessage):
    """Command message that deletes scale_file models
    """

    def __init__(self):
        """Constructor
        """

        super(MoveFiles, self).__init__('move_files')

        self._file_ids = []
        self.new_workspace = None
        self.new_uri = None

    def add_file(self, file_id):
        """Adds the given file to this message

        :param file_id: The file ID
        :type file_id: int
        """

        self._file_ids.append(file_id)

    def can_fit_more(self):
        """Indicates whether more files can fit in this message

        :return: True if more jobs can fit, False otherwise
        :rtype: bool
        """

        return len(self._file_ids) < MAX_NUM

    def to_json(self):
        """See :meth:`messaging.messages.message.CommandMessage.to_json`
        """

        return {
            'file_ids': self._file_ids,
            'new_workspace': self.new_workspace,
            'new_uri': self.new_uri
        }

    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`
        """

        message = MoveFiles()
        message.new_workspace = json_dict['new_workspace']
        message.new_uri = json_dict['new_uri']
        for file_id in json_dict['file_ids']:
            message.add_file(file_id)
        return message

    def execute(self):
        """See :meth:`messaging.messages.message.CommandMessage.execute`
        """

        # Add stop mechanism like purgeresults?

        when = timezone.now()
        files_to_move = ScaleFile.objects.filter(id__in=self._file_ids)
        
        #update url metadata?
        files_to_move.update(file_path=self.new_uri,workspace=self.new_workspace)

        return True
