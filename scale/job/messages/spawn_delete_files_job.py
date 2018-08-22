"""Defines a command message that creates and queues a system job for deleting files"""
from __future__ import unicode_literals

import logging

from django.db import transaction

from data.data.value import JsonValue
from job.messages.create_jobs import create_jobs_message
from messaging.messages.message import CommandMessage
from storage.models import ScaleFile


logger = logging.getLogger(__name__)


def create_spawn_delete_files_job(job_id, purge):
    """Creates a spawn delete files job message

    :param job_id: The job ID whose files will be deleted
    :type job_id: int
    :param purge: Boolean value to determine if the files should be purged
    :type purge: bool
    :return: The spawn delete files job message
    :rtype: :class:`job.messages.spawn_delete_files_job.SpawnDeleteFilesJob`
    """

    message = SpawnDeleteFilesJob()
    message.job_id = job_id
    message.purge = purge
    return message


class SpawnDeleteFilesJob(CommandMessage):
    """Command message that spawns a delete files system job
    """

    def __init__(self):
        """Constructor
        """

        super(SpawnDeleteFilesJob, self).__init__('spawn_delete_files_job')

        self.job_id = None
        self.purge = False

    def to_json(self):
        """See :meth:`messaging.messages.message.CommandMessage.to_json`
        """

        return {'job_id': self.job_id, 'purge': str(self.purge)}

    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`
        """

        message = SpawnDeleteFilesJob()
        message.job_id = json_dict['job_id']
        message.purge = bool(json_dict['purge'])
        return message

    def execute(self):
        """See :meth:`messaging.messages.message.CommandMessage.execute`
        """

        # This message will look at the job's files and create and 
        # queue a system job to delete those files in the workspace 
        # (passing along the purge flag). This messages does not affect 
        # any database models.
        files_to_delete = ScaleFile.objects.filter_files(job_ids=[self.job_id])
        # data.data.~ -> JobData -> dict -> create_job message
        if files_to_delete:
            mappings = self._build_mappings(files_to_delete)
            
            # Construct input data list
            input_data = [JsonValue('job_id', self.job_id),
                          JsonValue('purge', self.purge)]
            for f in mappings['files']:
                input_data.append(JsonValue('file', f))
            for w in mappings['workspaces']:
                input_data.append(JsonValue('workspaces', w))

            print input_data
        return True

    def _build_mappings(self, files_to_delete):
        """Parses the files that are to be deleted and builds a mapping for
        files and workspaces that will be used as the job input.

        :param files_to_delete: The files to be deleted
        :type files_to_delete: :class:`django.db.models.QuerySet`
        :return: A mapping of the files and workspaces
        :rtype: dict
        """

        files = [{'id': f.id, 'file_path': f.file_path, 'workspace': f.workspace.name} for f in files_to_delete]
        workspaces = set([{f.workspace.name: f.workspace} for f in files_to_delete])

        return {'files': files, 'workspaces': workspaces}
