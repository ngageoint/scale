'''Defines the ingest trigger event'''
from trigger.models import TriggerEvent


TRIGGER_TYPE = u'INGEST'


class IngestTriggerEvent(object):
    '''Represents a trigger event where a source file was ingested
    '''

    def __init__(self, rule, ingest):
        '''Constructor

        :param rule: The model for the rule that triggered this event
        :type rule: :class:`trigger.models.TriggerRule`
        :param ingest: The ingest that caused this event to trigger
        :type ingest: :class:`ingest.models.Ingest`
        '''

        if not rule:
            raise Exception(u'Rule must be provided')

        self._rule = rule
        self._description = {u'version': u'1.0', u'ingest_id': ingest.id, u'file_name': ingest.file_name}
        self._occurred = ingest.ingest_ended
        self._already_in_db = False

    def save_to_db(self):
        '''Saves the ingest trigger event to the database

        :returns: The new trigger event model
        :rtype: :class:`trigger.models.TriggerEvent`
        '''

        if self._already_in_db:
            raise Exception(u'Event is already saved in the database')

        event = TriggerEvent.objects.create_trigger_event(TRIGGER_TYPE, self._rule, self._description, self._occurred)
        self._already_in_db = True
        return event
