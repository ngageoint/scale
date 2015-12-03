'''Defines the parse trigger event'''
from trigger.models import TriggerEvent


TRIGGER_TYPE = u'PARSE'


class ParseTriggerEvent(object):
    '''Represents a parse event where a source file was ingested
    '''

    def __init__(self, rule, parse_file):
        '''Constructor

        :param rule: The model for the rule that triggered this event
        :type rule: :class:`trigger.models.TriggerRule`
        :param parse_file: The file that caused this event to trigger
        :type parse_file: :class:`source.models.SourceFile`
        '''

        if not rule:
            raise Exception(u'Rule must be provided')

        self._rule = rule
        self._description = {u'version': u'1.0', u'parse_id': parse_file.id, u'file_name': parse_file.file_name}
        self._occurred = parse_file.parsed
        self._already_in_db = False

    def save_to_db(self):
        '''Saves the parse trigger event to the database

        :returns: The new trigger event model
        :rtype: :class:`trigger.models.TriggerEvent`
        '''

        if self._already_in_db:
            raise Exception(u'Event is already saved in the database')

        event = TriggerEvent.objects.create_trigger_event(TRIGGER_TYPE, self._rule, self._description, self._occurred)
        self._already_in_db = True
        return event
