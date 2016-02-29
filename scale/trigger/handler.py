'''Defines the base class for handling trigger rules and provides apps a way to register handler sub-classes'''
from __future__ import unicode_literals

from abc import ABCMeta, abstractmethod

from trigger.configuration.exceptions import InvalidTriggerType
from trigger.models import TriggerRule


# Registered handlers for trigger rules
# {"Trigger Rule Type": Handler Object}
TRIGGER_RULE_HANDLERS = {}


def get_trigger_rule_handler(trigger_rule_type):
    '''Returns the trigger rule handler that is registered with the given type

    :param trigger_rule_type: The trigger rule type
    :type trigger_rule_type: str
    :returns: The trigger rule handler, possibly None
    :rtype: :class:`trigger.handler.TriggerRuleHandler`

    :raises :class:`trigger.configuration.exceptions.InvalidTriggerType`: If the trigger type is invalid
    '''

    if not trigger_rule_type in TRIGGER_RULE_HANDLERS:
        raise InvalidTriggerType('%s is an invalid trigger rule type' % trigger_rule_type)

    return TRIGGER_RULE_HANDLERS[trigger_rule_type]


def register_trigger_rule_handler(trigger_rule_handler):
    '''Registers the given trigger rule handler with the given type

    :param trigger_rule_handler: The trigger rule handler
    :type trigger_rule_handler: :class:`trigger.handler.TriggerRuleHandler`
    '''

    TRIGGER_RULE_HANDLERS[trigger_rule_handler.trigger_rule_type] = trigger_rule_handler


class TriggerRuleHandler(object):
    '''Base class for handling trigger rules
    '''

    __metaclass__ = ABCMeta

    def __init__(self, trigger_rule_type):
        '''Constructor

        :param trigger_rule_type: The trigger rule type
        :type trigger_rule_type: str
        '''

        self.trigger_rule_type = trigger_rule_type

    @abstractmethod
    def create_configuration(self, config_dict):
        '''Creates and returns a trigger rule configuration from the given dict

        :param config_dict: The configuration as a dict
        :type config_dict: dict
        :returns: The trigger rule configuration
        :rtype: :class:`trigger.configuration.trigger_rule.TriggerRuleConfiguration`

        :raises :class:`trigger.configuration.exceptions.InvalidTriggerRule`: If the configuration is invalid
        '''

        raise NotImplementedError()

    def create_trigger_rule(self, config_dict, name=None, is_active=True):
        '''Creates and returns a trigger rule model with the given configuration. The returned trigger rule model will
        be saved in the database.

        :param config_dict: The configuration as a dict
        :type config_dict: dict
        :param name: An optional name for the trigger
        :type name: str
        :param is_active: Whether or not the trigger should be active
        :type is_active: bool
        :returns: The new trigger rule
        :rtype: :class:`trigger.models.TriggerRule`

        :raises trigger.configuration.exceptions.InvalidTriggerRule: If the configuration is invalid
        '''

        configuration = self.create_configuration(config_dict)
        return TriggerRule.objects.create_trigger_rule(self.trigger_rule_type, configuration, name, is_active)
