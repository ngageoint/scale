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


def create_move_files_messages(files, workspace, uri):
    """Creates messages to move the given files

    :param files: The list of file IDs to move
    :type files: [collections.namedtuple]
    :param workspace: The name of the workspace to move the files to
    :type workspace: string
    :param uri: The uri to move the files to
    :type uri: string
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
        message.workspace = workspace
        message.uri = uri
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
        self.workspace = None
        self.uri = None

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
            'workspace': self.workspace,
            'uri': self.uri
        }

    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`
        """

        message = MoveFiles()
        message.workspace = json_dict['workspace']
        message.uri = json_dict['uri']
        for file_id in json_dict['file_ids']:
            message.add_file(file_id)
        return message

    def execute(self):
        """See :meth:`messaging.messages.message.CommandMessage.execute`
        """

        # Add stop mechanism like purgeresults?

        when = timezone.now()
        files_to_move = ScaleFile.objects.filter(id__in=self._file_ids)
        
        #check new uri and/or get new workspace id
        #move file(s) to new location, check for file io error
        #update file model
        files_to_move.update(file_path=self.uri,workspace=self.workspace)

        return True
