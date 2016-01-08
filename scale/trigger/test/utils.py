'''Defines utility methods for testing trigger rules and events.'''
import django.utils.timezone as timezone

import storage.test.utils as storage_test_utils
from trigger.models import TriggerEvent, TriggerRule

EVENT_TYPE_COUNTER = 1

RULE_NAME_COUNTER = 1


def create_trigger_event(trigger_type=None, rule=None, description=None, occurred=None):
    '''Creates a trigger event model for unit testing

    :returns: The trigger event model
    :rtype: :class:`trigger.models.TriggerEvent`
    '''

    if not trigger_type:
        global EVENT_TYPE_COUNTER
        trigger_type = 'TEST_TYPE_%i' % EVENT_TYPE_COUNTER
        EVENT_TYPE_COUNTER = EVENT_TYPE_COUNTER + 1

    if not rule:
        rule = create_trigger_rule(trigger_type=trigger_type)
    if not description:
        description = {
            'version': '1.0',
        }
    if not occurred:
        occurred = timezone.now()

    return TriggerEvent.objects.create(type=trigger_type, rule=rule, description=description, occurred=occurred)


def create_trigger_rule(name=None, trigger_type='PARSE', configuration=None, is_active=True):
    '''Creates a trigger rule model for unit testing

    :returns: The trigger rule model
    :rtype: :class:`trigger.models.TriggerRule`
    '''

    if not name:
        global RULE_NAME_COUNTER
        name = 'test-name-%i' % RULE_NAME_COUNTER
        RULE_NAME_COUNTER = RULE_NAME_COUNTER + 1

    if not configuration:
        configuration = {
            'version': '1.0',
            'condition': {
                'media_type': 'text/plain',
            },
            'data': {
                'input_data_name': 'input_file',
                'workspace_name': storage_test_utils.create_workspace().name,
            }
        }

    return TriggerRule.objects.create(name=name, type=trigger_type, configuration=configuration, is_active=is_active)
