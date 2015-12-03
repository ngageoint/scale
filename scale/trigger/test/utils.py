'''Defines utility methods for testing trigger rules and events.'''
import django.utils.timezone as timezone

from trigger.models import TriggerEvent, TriggerRule

EVENT_TYPE_COUNTER = 1

RULE_NAME_COUNTER = 1
RULE_TYPE_COUNTER = 1


def create_trigger_event(trigger_type=None, rule=None, description=None, occurred=None):
    '''Creates a trigger event model for unit testing

    :returns: The trigger event model
    :rtype: :class:`trigger.models.TriggerEvent`
    '''

    if not trigger_type:
        global EVENT_TYPE_COUNTER
        trigger_type = u'TEST_TYPE_%i' % EVENT_TYPE_COUNTER
        EVENT_TYPE_COUNTER = EVENT_TYPE_COUNTER + 1

    if not rule:
        rule = create_trigger_rule(trigger_type=trigger_type)
    if not description:
        description = {
            u'version': u'1.0',
        }
    if not occurred:
        occurred = timezone.now()

    return TriggerEvent.objects.create(type=trigger_type, rule=rule, description=description, occurred=occurred)


def create_trigger_rule(name=None, trigger_type=None, title=u'Test Trigger', description=u'Test trigger description.',
                        configuration=None, is_active=True):
    '''Creates a trigger rule model for unit testing

    :returns: The trigger rule model
    :rtype: :class:`trigger.models.TriggerRule`
    '''

    if not name:
        global RULE_NAME_COUNTER
        name = u'test-name-%i' % RULE_NAME_COUNTER
        RULE_NAME_COUNTER = RULE_NAME_COUNTER + 1

    if not trigger_type:
        global RULE_TYPE_COUNTER
        trigger_type = u'TEST_TYPE_%i' % RULE_TYPE_COUNTER
        RULE_TYPE_COUNTER = RULE_TYPE_COUNTER + 1

    if not configuration:
        configuration = {
            u'version': u'1.0',
            u'trigger': {
                u'media_type': u'text/plain',
            },
        }

    return TriggerRule.objects.create(name=name, type=trigger_type, title=title, description=description,
                                      configuration=configuration, is_active=is_active)
