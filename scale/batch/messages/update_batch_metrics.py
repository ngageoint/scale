"""Defines a command message that updates batch metrics"""
from __future__ import unicode_literals

import logging

from batch.models import Batch
from messaging.messages.message import CommandMessage

# This is the maximum number of batch models that can fit in one message. This maximum ensures that every message of
# this type is less than 25 KiB long and that each message can be processed quickly.
MAX_NUM = 100


logger = logging.getLogger(__name__)


def create_update_batch_metrics_messages(batch_ids):
    """Creates messages to update the metrics for the given batches

    :param batch_ids: The batch IDs
    :type batch_ids: list
    :return: The list of messages
    :rtype: list
    """

    messages = []

    message = None
    for batch_id in batch_ids:
        if not message:
            message = UpdateBatchMetrics()
        elif not message.can_fit_more():
            messages.append(message)
            message = UpdateBatchMetrics()
        message.add_batch(batch_id)
    if message:
        messages.append(message)

    return messages


class UpdateBatchMetrics(CommandMessage):
    """Command message that updates recipe metrics
    """

    def __init__(self):
        """Constructor
        """

        super(UpdateBatchMetrics, self).__init__('update_batch_metrics')

        self._batch_ids = []

    def add_batch(self, batch_id):
        """Adds the given batch ID to this message

        :param batch_id: The batch ID
        :type batch_id: int
        """

        self._batch_ids.append(batch_id)

    def can_fit_more(self):
        """Indicates whether more batches can fit in this message

        :return: True if more batches can fit, False otherwise
        :rtype: bool
        """

        return len(self._batch_ids) < MAX_NUM

    def to_json(self):
        """See :meth:`messaging.messages.message.CommandMessage.to_json`
        """

        return {'batch_ids': self._batch_ids}

    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`
        """

        message = UpdateBatchMetrics()
        for batch_id in json_dict['batch_ids']:
            message.add_batch(batch_id)

        return message

    def execute(self):
        """See :meth:`messaging.messages.message.CommandMessage.execute`
        """

        Batch.objects.update_batch_metrics(self._batch_ids)
        return True
