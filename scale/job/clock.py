"""Contains the functionality of the Scale clock process"""
from __future__ import unicode_literals
import abc
import datetime
import logging
import math

import django.utils.timezone as timezone
from django.db import transaction

import util.parse as parse
from trigger.models import TriggerEvent, TriggerRule

logger = logging.getLogger(__name__)


# Mapping of clock event processor name to processor class definition
_PROCESSORS = {}


class ClockEventError(Exception):
    """Error class used when a clock event processor encounters a problem."""
    pass


class ClockEventProcessor(object):
    """Base class used to process triggered clock events."""
    __metaclass__ = abc.ABCMeta

    def process_event(self, event, last_event=None):
        """Callback when a new event is triggered that sub-classes have registered to process.

        :param event: The new event that requires processing.
        :type event: :class:`trigger.models.TriggerEvent`
        :param last_event: The last event that was processed. Could be None if this is the first ever execution.
        :type last_event: :class:`trigger.models.TriggerEvent`

        :raises :class:`job.clock.ClockEventError`: If the event should be cancelled for any reason.
        """
        raise NotImplemented()


def perform_tick():
    """Performs an iteration of the Scale clock.

    A clock iteration consists of inspecting any trigger rules and corresponding events to see if there are any that
    have exceeded their scheduled time threshold. For rules that are due to run, a new event is created of the
    configured type and the registered clock function is executed.
    """

    # Check all the clock trigger rules
    rules = TriggerRule.objects.filter(type='CLOCK', is_active=True)
    for rule in rules:
        try:
            _check_rule(rule)
        except ClockEventError:
            logger.exception('Clock scheduler caught known rule error: %s', rule.id)
        except:
            logger.exception('Clock scheduler encountered unexpected rule error: %s', rule.id)


def register_processor(name, processor_class):
    """Registers the given processor class definition to be called by the Scale clock at the given interval.

    Processors from other applications can be registered during their ready() method.

    :param name: The system name of the processor, which is used in trigger rule configurations.
    :type name: string
    :param processor_class: The processor class to invoke when the associated event is triggered.
    :type processor_class: :class:`job.clock.ClockProcessor`
    """
    if name not in _PROCESSORS:
        _PROCESSORS[name] = []
    logger.debug('Registering clock processor: %s -> %s', name, processor_class)
    _PROCESSORS[name].append(processor_class)


def _check_rule(rule):
    """Checks the given rule for validation errors and then triggers an event for processing if the schedule requires.

    :param rule: The system name of the processor, which is used in trigger rule configurations.
    :type rule: :class:`trigger.models.TriggerRule`

    :raises :class:`job.clock.ClockEventError`: If there is a configuration problem with the rule.
    """

    # Validate the processor name attribute
    if rule.name not in _PROCESSORS:
        raise ClockEventError('Clock trigger rule references unknown processor name: %s -> %s' % (rule.id, rule.name))

    # Validate the event type attribute
    if 'event_type' not in rule.configuration or not rule.configuration['event_type']:
        raise ClockEventError('Clock trigger rule missing "event_type" attribute: ' % rule.id)

    # Validate the clock schedule
    if 'schedule' not in rule.configuration or not rule.configuration['schedule']:
        raise ClockEventError('Clock trigger rule missing "schedule" attribute: ' % rule.id)
    schedule = rule.configuration['schedule']
    duration = parse.parse_duration(schedule)
    if not duration:
        raise ClockEventError('Invalid format for clock trigger "schedule" attribute: %s -> %s' % (rule.id, schedule))

    # Trigger a new event when the schedule is surpassed
    last_event = TriggerEvent.objects.filter(rule=rule).order_by('-occurred').first()
    logger.debug('Checking rule schedule: %s -> %s since %s', rule.type, duration, last_event)
    if _check_schedule(duration, last_event):
        _trigger_event(rule, last_event)


def _check_schedule(duration, last_event=None):
    """Checks the given rule schedule and previously triggered event to determine whether a new event should trigger.

    :param duration: The scheduled duration used to determine when to fire the next trigger event.
    :type duration: datetime.timedelta
    :param last_event: The last event that was triggered for the rule associated with this schedule. May be None if the
        rule has never triggered an event.
    :type last_event: :class:`trigger.models.TriggerEvent`
    :returns: True if a new event should be triggered, false otherwise.
    :rtype: bool
    """
    # The master clock smallest unit is 1 minute so clear anything smaller to avoid schedule drift
    current = timezone.now().replace(second=0, microsecond=0)
    base = datetime.datetime(year=current.year, month=current.month, day=current.day, tzinfo=timezone.utc)

    # Trigger when the first ever event threshold is reached
    # This handles an hourly schedule within the context of the current day or runs immediately for a daily
    if not last_event:
        if duration < datetime.timedelta(days=1):
            return base + duration <= current
        return True

    # Trigger when the elapsed time exceeds the relative duration
    # This recovers infrequent jobs after the system has been down for longer than the schedule
    elapsed = current - last_event.occurred
    if ((duration >= datetime.timedelta(days=1) and elapsed >= datetime.timedelta(days=1) or
            duration >= datetime.timedelta(hours=1) and elapsed >= datetime.timedelta(hours=1)) and
            elapsed >= duration):
        return True

    # Trigger based on absolute time within the current day
    # This is designed to avoid hourly schedules slowly drifting away over time
    steps = math.ceil((current - base).total_seconds() / duration.total_seconds())
    target = base + datetime.timedelta(seconds=duration.total_seconds() * steps)
    return last_event.occurred + duration >= target and target <= current


@transaction.atomic
def _trigger_event(rule, last_event=None):
    """Creates a new event based on the given rule and invokes the registered processor to handle it.

    :param rule: The rule form which to derive the new event.
    :type rule: :class:`trigger.models.TriggerRule`
    :param last_event: The last event that was triggered for the rule associated with this schedule. May be None if the
        rule has never triggered an event.
    :type last_event: :class:`trigger.models.TriggerEvent`

    :raises :class:`job.clock.ClockEventError`: If the registered processor rejects the event.
    """

    # Create a new trigger event for the rule
    event_type = rule.configuration['event_type']
    event = TriggerEvent.objects.create_trigger_event(event_type, rule, {}, timezone.now())

    # Allow each registered processor to handle the event
    for processor_class in _PROCESSORS[rule.name]:
        try:
            processor = processor_class()
            processor.process_event(event, last_event)
        except ClockEventError:
            logger.exception('Clock processor raised known rule error: %s', rule.id)
        except:
            logger.exception('Clock processor encountered unexpected rule error: %s', rule.id)
