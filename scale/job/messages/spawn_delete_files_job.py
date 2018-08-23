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
            # Construct input data list
            workspaces = []
            inputs = [JsonValue('job_id', self.job_id),
                      JsonValue('purge', self.purge)]
            for f in files_to_delete:
                inputs.append(JsonValue('file', {'id': f.id, 'file_path': f.file_path, 'workspace': f.workspace.name}))
                if f.workspace.name not in workspaces:
                    inputs.append(JsonValue('workspace', {f.workspace.name: f.workspace.json_config}))
                    workspaces.append(f.workspace.name)

            print inputs

        return True
