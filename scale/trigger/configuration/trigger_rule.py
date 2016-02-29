'''Defines the base configuration class for a trigger rule'''
from __future__ import unicode_literals

from abc import ABCMeta, abstractmethod


class TriggerRuleConfiguration(object):
    '''The base class that represents the configuration for a trigger rule
    '''

    __metaclass__ = ABCMeta

    def __init__(self, trigger_rule_type, config_dict):
        '''Base Constructor

        :param trigger_rule_type: The trigger rule type
        :type trigger_rule_type: str
        :param config_dict: The configuration as a dict
        :type config_dict: dict
        '''

        self.trigger_rule_type = trigger_rule_type
        self._dict = config_dict

    def get_dict(self):
        '''Returns the configuration as a dict

        :return: The configuration
        :rtype: dict
        '''

        return self._dict

    @abstractmethod
    def validate(self):
        '''Validates the trigger rule configuration. This is a more thorough validation than the basic schema checks
        performed in trigger rule constructors and may include database queries.

        :raises trigger.configuration.exceptions.InvalidTriggerRule: If the configuration is invalid
        '''

        raise NotImplementedError()
