"""Defines a command message that sets BLOCKED status for job models"""
from __future__ import unicode_literals

import json
import logging

from django.db import transaction

from data.data.json.data_v6 import DataV6
from messaging.messages.message import CommandMessage
from dataset.models import DataSet
from util.parse import datetime_to_string, parse_datetime

# This is the maximum number of bytes can fit in one message. This maximum ensures that every message of this
# type is less than 25 KiB long.
MAX_NUM = 25000


logger = logging.getLogger(__name__)


def create_dataset_members_messages(dataset_id, data_list):
    """Creates messages to create dataset members

    :param dataset_id: The identifier for the new members' dataset
    :type dataset: integer
    :param data_list: The data for the dataset members
    :type data_list: [:class:`data.data.data.Data`]
    :return: The list of messages
    :rtype: list
    """

    messages = []

    message = None
    for dl in data_list:
        if not message:
            message = CreateDatasetMember()
            message._dataset_id = dataset_id
        elif not message.can_fit_more(dl):
            messages.append(message)
            message = CreateDatasetMember()
            message._dataset_id = dataset_id
        message.add_data(dl)
    if message:
        messages.append(message)

    return messages


class CreateDatasetMember(CommandMessage):
    """Command message that sets BLOCKED status for job models
    """

    def __init__(self):
        """Constructor
        """

        super(CreateDatasetMember, self).__init__('create_dataset_members')

        self._count = 0
        self._dataset_id = 0
        self._data_list = []

    def add_data(self, data):
        """Adds the given data to this message

        :param data: The data object
        :type data: :class:`data.data.data.Data`
        """

        self._count += len(json.dumps(data.get_dict()))
        self._data_list.append(data)

    def can_fit_more(self, data):
        """Indicates whether more data can fit in this message

        :param data: The data object to add
        :type data: :class:`data.data.data.Data`

        :return: True if more data can fit, False otherwise
        :rtype: bool
        """

        return self._count + len(json.dumps(data.get_dict())) < MAX_NUM

    def to_json(self):
        """See :meth:`messaging.messages.message.CommandMessage.to_json`
        """

        data_dicts = []
        for d in self._data_list:
            data_dicts.append(d.get_dict())
        return {'dataset_id': self.dataset_id, 'data_list': data_dicts}

    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`
        """


        message = CreateDatasetMember()
        message._dataset_id = message['dataset_id']
        for dl in json_dict['data_list']:
            message.add_data(DataV6(data=dl).get_data())

        return message

    def execute(self):
        """See :meth:`messaging.messages.message.CommandMessage.execute`
        """

        with transaction.atomic():
            dataset = DataSet.objects.get(pk=self._dataset_id)
            dataset_member = DataSetMember()
            dataset_member.dataset = dataset
            dataset_member.data = convert_data_to_v6_json(data).get_dict()
            datasetfiles, file_ids = DataSetFile.objects.create_dataset_files(dataset, data)
            dataset_member.file_ids = file_ids
            DataSetFile.objects.bulk_create(datasetfiles)
            # Retrieve locked job models
            for job_model in Job.objects.get_locked_jobs(self._blocked_job_ids):
                if not job_model.last_status_change or job_model.last_status_change < self.status_change:
                    # Status update is not old, so perform the update
                    jobs_to_blocked.append(job_model)

            # Update jobs that need status set to BLOCKED
            if jobs_to_blocked:
                job_ids = Job.objects.update_jobs_to_blocked(jobs_to_blocked, self.status_change)
                logger.info('Set %d job(s) to BLOCKED status', len(job_ids))

        # Send messages to update recipe metrics
        from recipe.messages.update_recipe_metrics import create_update_recipe_metrics_messages_from_jobs
        self.new_messages.extend(create_update_recipe_metrics_messages_from_jobs(self._blocked_job_ids))

        return True
