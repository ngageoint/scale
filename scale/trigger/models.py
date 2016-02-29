'''Defines the models for trigger rules and events'''
from __future__ import unicode_literals

import djorm_pgjson.fields
from django.db import models, transaction
from django.utils.timezone import now


class TriggerEventManager(models.Manager):
    '''Provides additional methods for handling trigger events
    '''

    def create_trigger_event(self, trigger_type, rule, description, occurred):
        '''Creates a new trigger event and returns the event model. The given rule model, if not None, must have already
        been saved in the database (it must have an ID). The returned trigger event model will be saved in the database.

        :param trigger_type: The type of the trigger that occurred
        :type trigger_type: str
        :param rule: The rule that triggered the event, possibly None
        :type rule: :class:`trigger.models.TriggerRule`
        :param description: The JSON description of the event as a dict
        :type description: dict
        :param occurred: When the event occurred
        :type occurred: :class:`datetime.datetime`
        :returns: The new trigger event
        :rtype: :class:`trigger.models.TriggerEvent`
        '''

        if trigger_type is None:
            raise Exception('Trigger event must have a type')
        if description is None:
            raise Exception('Trigger event must have a JSON description')
        if occurred is None:
            raise Exception('Trigger event must have a timestamp')

        event = TriggerEvent()
        event.type = trigger_type
        event.rule = rule
        event.description = description
        event.occurred = occurred
        event.save()

        return event


class TriggerEvent(models.Model):
    '''Represents an event where a trigger occurred

    :keyword type: The type of the trigger that occurred
    :type type: :class:`django.db.models.CharField`
    :keyword rule: The rule that triggered this event, possibly None (some events are not triggered by rules)
    :type rule: :class:`django.db.models.ForeignKey`
    :keyword description: JSON description of the event. This will contain fields specific to the type of the trigger
        that occurred.
    :type description: :class:`djorm_pgjson.fields.JSONField`
    :keyword occurred: When the event occurred
    :type occurred: :class:`django.db.models.DateTimeField`
    '''

    type = models.CharField(db_index=True, max_length=50)
    rule = models.ForeignKey('trigger.TriggerRule', blank=True, null=True, on_delete=models.PROTECT)
    description = djorm_pgjson.fields.JSONField()
    occurred = models.DateTimeField(db_index=True)

    objects = TriggerEventManager()

    class Meta(object):
        '''meta information for the db'''
        db_table = 'trigger_event'


class TriggerRuleManager(models.Manager):
    '''Provides additional methods for handling trigger rules
    '''

    @transaction.atomic
    def archive_trigger_rule(self, trigger_rule_id):
        '''Archives the trigger rule (will no longer be active) with the given ID

        :param trigger_rule_id: The ID of the trigger rule to archive
        :type trigger_rule_id: int
        '''

        rule = TriggerRule.objects.select_for_update().get(pk=trigger_rule_id)
        rule.is_active = False
        rule.archived = now()
        rule.save()

    def create_trigger_rule(self, trigger_type, configuration, name='', is_active=True):
        '''Creates a new trigger rule and returns the rule model. The returned trigger rule model will be saved in the
        database.

        :param trigger_type: The type of this trigger rule
        :type trigger_type: str
        :param configuration: The rule configuration
        :type configuration: :class:`trigger.configuration.TriggerRuleConfiguration`
        :param name: An optional name for the trigger
        :type name: str
        :param is_active: Whether or not the trigger should be active
        :type is_active: bool
        :returns: The new trigger rule
        :rtype: :class:`trigger.models.TriggerRule`

        :raises trigger.configuration.exceptions.InvalidTriggerRule: If the configuration is invalid
        '''

        if not trigger_type:
            raise Exception('Trigger rule must have a type')
        if not configuration:
            raise Exception('Trigger rule must have a configuration')

        configuration.validate()

        rule = TriggerRule()
        rule.type = trigger_type
        rule.name = name
        rule.is_active = is_active
        rule.configuration = configuration.get_dict()
        rule.save()

        return rule

    def get_by_natural_key(self, name):
        '''Django method to retrieve a trigger rule for the given natural key. NOTE: All trigger rule names are NOT
        unique. This is implemented to allow the loading of defined system trigger rules which do have unique names.

        :param name: The name of the trigger rule
        :type name: str
        :returns: The trigger rule defined by the natural key
        :rtype: :class:`error.models.Error`
        '''

        return self.get(name=name)


class TriggerRule(models.Model):
    '''Represents a rule that, when triggered, creates a trigger event

    :keyword type: The type of the trigger for the rule
    :type type: :class:`django.db.models.CharField`
    :keyword name: The stable name of the trigger rule used by clients for queries
    :type name: :class:`django.db.models.CharField`

    :keyword configuration: JSON configuration for the rule. This will contain fields specific to the type of the
        trigger.
    :type configuration: :class:`djorm_pgjson.fields.JSONField`
    :keyword is_active: Whether the rule is still active (false once rule is archived)
    :type is_active: :class:`django.db.models.BooleanField`

    :keyword created: When the rule was created
    :type created: :class:`django.db.models.DateTimeField`
    :keyword archived: When the rule was archived (no longer active)
    :type archived: :class:`django.db.models.DateTimeField`
    :keyword last_modified: When the rule was last modified
    :type last_modified: :class:`django.db.models.DateTimeField`
    '''
    type = models.CharField(max_length=50, db_index=True)
    name = models.CharField(blank=True, max_length=50)

    configuration = djorm_pgjson.fields.JSONField()
    is_active = models.BooleanField(default=True, db_index=True)

    created = models.DateTimeField(auto_now_add=True)
    archived = models.DateTimeField(blank=True, null=True)
    last_modified = models.DateTimeField(auto_now=True)

    objects = TriggerRuleManager()

    def get_configuration(self):
        '''Returns the configuration for this trigger rule

        :returns: The configuration for this trigger rule
        :rtype: :class:`trigger.configuration.trigger_rule.TriggerRuleConfiguration`

        :raises :class:`trigger.configuration.exceptions.InvalidTriggerType`: If the trigger type is invalid
        '''

        from trigger.handler import get_trigger_rule_handler

        handler = get_trigger_rule_handler(self.type)
        return handler.create_configuration(self.configuration)

    def natural_key(self):
        '''Django method to define the natural key for a trigger rule as the name

        :returns: A tuple representing the natural key
        :rtype: tuple(str,)
        '''

        return (self.name,)

    class Meta(object):
        '''meta information for the db'''
        db_table = 'trigger_rule'
