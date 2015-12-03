'''Defines the models for trigger rules and events'''
import djorm_pgjson.fields
from django.db import models


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
            raise Exception(u'Trigger event must have a type')
        if description is None:
            raise Exception(u'Trigger event must have a JSON description')
        if occurred is None:
            raise Exception(u'Trigger event must have a timestamp')

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
    rule = models.ForeignKey(u'trigger.TriggerRule', blank=True, null=True, on_delete=models.PROTECT)
    description = djorm_pgjson.fields.JSONField()
    occurred = models.DateTimeField(db_index=True)

    objects = TriggerEventManager()

    class Meta(object):
        '''meta information for the db'''
        db_table = u'trigger_event'


class TriggerRuleManager(models.Manager):
    '''Provides additional methods for handling trigger rules
    '''

    def create_trigger_rule(self, trigger_type, configuration):
        '''Creates a new trigger rule and returns the rule model. The returned trigger rule model will be saved in the
        database.

        :param trigger_type: The type of this trigger rule
        :type trigger_type: str
        :param configuration: The JSON configuration of the rule as a dict
        :type configuration: dict
        :returns: The new trigger rule
        :rtype: :class:`trigger.models.TriggerRule`
        '''

        if trigger_type is None:
            raise Exception(u'Trigger rule must have a type')
        if configuration is None:
            raise Exception(u'Trigger rule must have a JSON configuration')

        rule = TriggerRule()
        rule.type = trigger_type
        rule.configuration = configuration
        rule.save()

        return rule

    def get_active_trigger_rules(self, trigger_type):
        '''Returns the active trigger rules in the database with the given trigger type

        :param trigger_type: The trigger rule type
        :type trigger_type: str
        :returns: The active trigger rules for the type
        :rtype: list of :class:`trigger.models.TriggerRule`
        '''

        return list(TriggerRule.objects.filter(type=trigger_type, is_active=True).iterator())

    def get_by_natural_key(self, name):
        '''Django method to retrieve the model for the given natural key

        :param name: The name of the model.
        :type name: str
        :returns: The model defined by the natural key
        :rtype: :class:`trigger.models.TriggerRule`
        '''

        return self.get(name=name)


class TriggerRule(models.Model):
    '''Represents a rule that, when triggered, creates a trigger event

    :keyword name: The stable name of the trigger rule used by clients for queries
    :type name: :class:`django.db.models.CharField`
    :keyword type: The type of the trigger for the rule
    :type type: :class:`django.db.models.CharField`
    :keyword title: The human-readable name of the trigger rule
    :type title: :class:`django.db.models.CharField`

    :keyword description: A longer description of the trigger rule
    :type description: :class:`django.db.models.CharField`
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

    name = models.CharField(max_length=50, unique=True)
    type = models.CharField(max_length=50, db_index=True)
    title = models.CharField(blank=True, max_length=50, null=True)
    description = models.CharField(blank=True, max_length=250, null=True)

    configuration = djorm_pgjson.fields.JSONField()
    is_active = models.BooleanField(default=True)

    created = models.DateTimeField(auto_now_add=True)
    archived = models.DateTimeField(blank=True, null=True)
    last_modified = models.DateTimeField(auto_now=True)

    objects = TriggerRuleManager()

    def natural_key(self):
        '''Django method to define the natural key for the model based on the name field.

        :returns: A tuple representing the natural key
        :rtype: tuple(str,)
        '''

        return (self.name,)

    class Meta(object):
        '''meta information for the db'''
        db_table = u'trigger_rule'
