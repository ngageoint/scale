"""Defines a command message that deletes files from ScaleFile"""
from __future__ import unicode_literals

import logging

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from job.messages.purge_jobs import create_purge_jobs_messages
from messaging.messages.message import CommandMessage
from product.models import FileAncestryLink
from storage.models import PurgeResults, ScaleFile

# This is the maximum number of file models that can fit in one message. This maximum ensures that every message of this
# type is less than 25 KiB long.
MAX_NUM = 100


logger = logging.getLogger(__name__)


def create_delete_files_messages(files, job_id, trigger_id, source_file_id, purge):
    """Creates messages to delete the given files

    :param files: The list of file IDs to delete
    :type files: [collections.namedtuple]
    :param job_id: The id of the job that produced the files
    :type job_id: int
    :param trigger_id: The trigger event id for the purge operation
    :type trigger_id: int
    :param source_file_id: The source file id for the original file being purged
    :type source_file_id: int
    :param purge: Boolean value to determine if files should be purged from workspace
    :type purge: bool
    :return: The list of messages
    :rtype: :func:`list`
    """

    messages = []

    message = None
    for scale_file in files:
        if not message:
            message = DeleteFiles()
        elif not message.can_fit_more():
            messages.append(message)
            message = DeleteFiles()
        message.add_file(scale_file.id)
        message.job_id = job_id
        message.trigger_id = trigger_id
        message.source_file_id = source_file_id
        message.purge = purge
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
        self.job_id = None
        self.trigger_id = None
        self.source_file_id = None
        self.purge = False

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
            'job_id': self.job_id,
            'trigger_id': self.trigger_id,
            'source_file_id': self.source_file_id,
            'purge': str(self.purge)
        }

    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`
        """

        message = DeleteFiles()
        message.job_id = json_dict['job_id']
        message.trigger_id = json_dict['trigger_id']
        message.source_file_id = json_dict['source_file_id']
        message.purge = bool(json_dict['purge'])
        for file_id in json_dict['file_ids']:
            message.add_file(file_id)
        return message

    def execute(self):
        """See :meth:`messaging.messages.message.CommandMessage.execute`
        """

        # Check to see if a force stop was placed on this purge process
        results = PurgeResults.objects.get(trigger_event=self.trigger_id)
        if results.force_stop_purge:
            return True

        when = timezone.now()
        files_to_delete = ScaleFile.objects.filter(id__in=self._file_ids)

        if self.purge:
            FileAncestryLink.objects.filter(descendant__in=files_to_delete).delete()
            files_to_delete.delete()

            # Update results
            PurgeResults.objects.filter(trigger_event=self.trigger_id).update(
                num_products_deleted = F('num_products_deleted') + len(self._file_ids))

            # Kick off purge_jobs for the given job_id
            self.new_messages.extend(create_purge_jobs_messages(purge_job_ids=[self.job_id],
                                                                trigger_id=self.trigger_id,
                                                                source_file_id=self.source_file_id))
        else:
            files_to_delete.update(is_deleted=True, deleted=when, is_published=False, unpublished=when)

        return True
