'''Defines the class that represents an ingest trigger rule condition'''
from __future__ import unicode_literals

import logging


logger = logging.getLogger(__name__)


class IngestTriggerCondition(object):
    '''Represents the condition for an ingest trigger rule
    '''

    def __init__(self, media_type, data_types):
        '''Creates an ingest trigger condition

        :param media_type: The media type that an ingested file must match, possibly None
        :type media_type: str
        :param data_types: The set of data types that an ingested file must matched, possibly None
        :type data_types: set of str
        '''

        self._media_type = media_type
        self._data_types = data_types if data_types is not None else set()

    def get_media_type(self):
        '''Returns the file media type for this ingest trigger condition

        :return: The media type
        :rtype: str
        '''

        return self._media_type

    def get_triggered_message(self):
        '''Returns the message that should be logged when this condition is triggered

        :return: The triggered message
        :rtype: str
        '''

        media_type = 'media type %s' % self._media_type if self._media_type else 'all media types'
        data_types = 'data type(s) %s' % str(list(self._data_types)) if self._data_types else 'all data types'
        return 'Ingest rule for %s and %s was triggered' % (media_type, data_types)

    def is_condition_met(self, source_file):
        '''Indicates whether the given ingested source file meets this ingest trigger condition

        :param source_file: The source file that was ingested
        :type source_file: :class:`source.models.SourceFile`
        :return: True if the condition is met, False otherwise
        :rtype: bool
        '''

        if self._media_type and self._media_type != source_file.media_type:
            return False

        return self._data_types <= source_file.get_data_type_tags()
