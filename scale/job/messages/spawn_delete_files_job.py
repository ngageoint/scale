"""Defines a command message that creates and queues a system job for deleting files"""
from __future__ import unicode_literals

import json
import logging

from data.data.data import Data
from data.data.json.data_v6 import convert_data_to_v6_json
from data.data.value import JsonValue

from job.messages.create_jobs import create_jobs_message
from messaging.messages.message import CommandMessage
from storage.models import ScaleFile


logger = logging.getLogger(__name__)


def create_spawn_delete_files_job(job_id, trigger_id, source_file_id, purge):
    """Creates a spawn delete files job message

    :param job_id: The job ID whose files will be deleted
    :type job_id: int
    :param trigger_id: The trigger event id for the purge operation
    :type trigger_id: int
    :param purge: Boolean value to determine if files should be purged from workspace
    :type purge: bool
    :param source_file_id: The source file id for the original file being purged
    :type source_file_id: int
    :return: The spawn delete files job message
    :rtype: :class:`job.messages.spawn_delete_files_job.SpawnDeleteFilesJob`
    """

    message = SpawnDeleteFilesJob()
    message.job_id = job_id
    message.trigger_id = trigger_id
    message.source_file_id = source_file_id
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
        self.trigger_id = None
        self.source_file_id = None
        self.purge = False

    def to_json(self):
        """See :meth:`messaging.messages.message.CommandMessage.to_json`
        """

        return {'job_id': self.job_id,
                'trigger_id': self.trigger_id,
                'source_file_id': self.source_file_id,
                'purge': str(self.purge)
               }

    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`
        """

        message = SpawnDeleteFilesJob()
        message.job_id = json_dict['job_id']
        message.trigger_id = json_dict['trigger_id']
        message.source_file_id = json_dict['source_file_id']
        message.purge = bool(json_dict['purge'])
        return message

    def execute(self):
        """See :meth:`messaging.messages.message.CommandMessage.execute`
        """

        files_to_delete = ScaleFile.objects.filter_files(job_ids=[self.job_id])

        if files_to_delete:
            # Construct input data
            files = []
            workspaces = []

            for f in files_to_delete:
                files.append({'id': f.id,
                              'file_path': f.file_path,
                              'workspace': f.workspace.name})
                if f.workspace.name not in [k for wrkspc in workspaces for k in wrkspc.keys()]:
                    workspaces.append({f.workspace.name: f.workspace.json_config})

            inputs = Data()
            inputs.add_value(JsonValue('job_id', str(self.job_id)))
            inputs.add_value(JsonValue('trigger_id', str(self.trigger_id)))
            inputs.add_value(JsonValue('source_file_id', str(self.source_file_id)))
            inputs.add_value(JsonValue('purge', str(self.purge)))
            inputs.add_value(JsonValue('files', json.dumps(files)))
            inputs.add_value(JsonValue('workspaces', json.dumps(workspaces)))
            inputs_json = convert_data_to_v6_json(inputs)

            # Send message to create system job to delete files
            msg = create_jobs_message(job_type_name="scale-delete-files", job_type_version="1.0.0",
                                      event_id=self.trigger_id, job_type_rev_num=1,
                                      input_data_dict=inputs_json.get_dict())
            self.new_messages.append(msg)

        return True
