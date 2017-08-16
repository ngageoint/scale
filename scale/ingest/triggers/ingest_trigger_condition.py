"""Defines the class that represents an ingest trigger rule condition"""
from __future__ import unicode_literals

import logging

logger = logging.getLogger(__name__)


class IngestTriggerCondition(object):
    """Represents the condition for an ingest trigger rule
    """

    def __init__(self, media_type, data_types, any_data_types=None, not_data_types=None):
        """Creates an ingest trigger condition

        :param media_type: The media type that an ingested file must match, possibly None
        :type media_type: str
        :param data_types: The set of data types that an ingested file must matched, possibly None
        :type data_types: set of str
        :param any_data_types: The set of data types that an ingested file must match at least one, possibly None
        :type data_types: set of str
        :param not_data_types: The set of data types that an ingested file must not match any of, possibly None
        :type data_types: set of str
        """

        self._media_type = media_type
        self._data_types = data_types if data_types is not None else set()
        self._any_data_types = any_data_types if any_data_types is not None else set()
        self._not_data_types = not_data_types if not_data_types is not None else set()

    def get_media_type(self):
        """Returns the file media type for this ingest trigger condition

        :return: The media type
        :rtype: str
        """

        return self._media_type

    def get_triggered_message(self):
        """Returns the message that should be logged when this condition is triggered

        :return: The triggered message
        :rtype: str
        """

        data_types_str = 'data type(s) '
        data_types_str_len = len(data_types_str)

        if self._data_types:
            data_types_str += str(list(self._data_types))
        if self._any_data_types:
            if len(data_types_str) > data_types_str_len:
                data_types_str += ' and '
            data_types_str += '[' + ' or '.join(self._any_data_types) + ']'
        if self._not_data_types:
            if len(data_types_str) > data_types_str_len:
                data_types_str += ' and '
            data_types_str += '[' + ' or '.join(self._not_data_types) + ']'
        if len(data_types_str) == data_types_str_len:
            data_types_str = 'all media types'

        media_type = 'media type %s' % self._media_type if self._media_type else 'all media types'
        return 'Ingest rule for %s and %s was triggered' % (media_type, data_types_str)

    def is_condition_met(self, source_file):
        """Indicates whether the given ingested source file meets this ingest trigger condition

        :param source_file: The source file that was ingested
        :type source_file: :class:`source.models.SourceFile`
        :return: True if the condition is met, False otherwise
        :rtype: bool
        """

        if self._media_type and self._media_type != source_file.media_type:
            return False

        condition_met = True
        file_data_types = source_file.get_data_type_tags()

        if self._not_data_types:
            condition_met = True not in [tag in file_data_types for tag in self._not_data_types]
        if self._any_data_types:
            condition_met = True in [tag in file_data_types for tag in self._any_data_types]
        if self._data_types:
            condition_met = self._data_types <= file_data_types

        return condition_met
