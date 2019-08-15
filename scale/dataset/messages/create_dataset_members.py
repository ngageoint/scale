"""Defines a command message that sets BLOCKED status for job models"""
from __future__ import unicode_literals

import json
import logging

from django.db import transaction

from data.data.json.data_v6 import DataV6, convert_data_to_v6_json
from data.data import data_util
from messaging.messages.message import CommandMessage
from dataset.models import DataSet, DataSetMember, DataSetFile
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
            message.dataset_id = dataset_id
        elif not message.can_fit_more(dl):
            messages.append(message)
            message = CreateDatasetMember()
            message.dataset_id = dataset_id
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
        self.dataset_id = 0
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
        message.dataset_id = json_dict['dataset_id']
        for dl in json_dict['data_list']:
            message.add_data(DataV6(data=dl).get_data())

        return message

    def execute(self):
        """See :meth:`messaging.messages.message.CommandMessage.execute`
        """

        dataset_members = []
        datasetfiles = []
        # bulk create should lock the whole datasetfile table so we don't have duplicate file ids being added while we're building our list
        # this might make it not worth using messages, however
        with transaction.atomic():
            existing_scale_ids = DataSetFile.get_file_ids([self.dataset_id])
            dataset = DataSet.objects.get(pk=self._dataset_id)
            for d in self._data_list:
                dataset_member = DataSetMember()
                dataset_member.dataset = dataset
                dataset_member.data = convert_data_to_v6_json(d).get_dict()
                dataset_member.file_ids = data_util.get_file_ids(d)
                dataset_members.append(dataset_member)
                datasetfiles = DataSetFile.objects.create_dataset_files(dataset, d, existing_scale_ids)
            DataSetFile.objects.bulk_create(datasetfiles)
            DataSetMember.objects.bulk_create(dataset_members)

        return True
