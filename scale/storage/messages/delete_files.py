"""Defines a command message that deletes files from ScaleFile"""
from __future__ import unicode_literals

import logging

from django.db import transaction
from django.utils import timezone

from messaging.messages.message import CommandMessage
from storage.models import ScaleFile

# This is the maximum number of file models that can fit in one message. This maximum ensures that every message of this
# type is less than 25 KiB long.
MAX_NUM = 100


logger = logging.getLogger(__name__)


def create_delete_files_messages(files, purge):
    """Creates messages to delete the given files

    :param file_ids: The list of file IDs to delete
    :type file_ids: [collections.namedtuple]
    :param purge: Boolean value to determine if the files should be purged
    :type purge: bool
    :return: The list of messages
    :rtype: list
    """

    messages = []

    message = None
    for scale_file in files:
        if not message:
            message = DeleteFiles()
            message.purge = purge
        elif not message.can_fit_more():
            messages.append(message)
            message = DeleteFiles()
            message.purge = purge
        message.add_file(scale_file.id)
    if message:
        messages.append(message)

    return messages

class DeleteFiles(CommandMessage):
    """Command message that deletes scale_file models
    """

    def __init__(self):
        """Constructor
        """

        super(DeleteFiles, self).__init__('delete_files')

        self._file_ids = []
        self.purge = False

    def add_file(self, file_id):
        """Adds the given file to this message

        :param job_id: The file ID
        :type job_id: int
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

        return {'file_ids': self._file_ids, 'purge': str(self.purge)}

    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`
        """

        message = DeleteFiles()
        message.purge = bool(json_dict['purge'])
        for file_id in json_dict['file_ids']:
            message.add_file(file_id)
        return message

    def execute(self):
        """See :meth:`messaging.messages.message.CommandMessage.execute`
        """

        when = timezone.now()
        files_to_delete = ScaleFile.objects.filter(id__in=self._file_ids)

        if self.purge:
            files_to_delete.delete()
            jobs_to_purge = set(files_to_delete.values_list('job__id', flat=True))

            # Send messages to purge jobs
            from job.messages.purge_jobs import create_purge_jobs_messages
            try:
                self.new_messages.extend(create_purge_jobs_messages(jobs_to_purge, when))
            except:
                pass

        else:
            files_to_delete.update(is_deleted=True, deleted=when, is_published=False, unpublished=when)

        return True
