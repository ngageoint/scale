#@PydevCodeAnalysisIgnore
from __future__ import unicode_literals
import datetime

import django
import django.utils.timezone as timezone
from django.test import TestCase
from mock import MagicMock, patch

import job.clock as clock
import job.test.utils as job_test_utils
from job.clock import ClockEventError, ClockEventProcessor
from trigger.models import TriggerEvent


class TestClock(TestCase):
    '''Tests functions in the clock module.'''

    def setUp(self):
        django.setup()

        self.processor = MagicMock(ClockEventProcessor)
        clock.register_processor('test-name', lambda: self.processor)

    @patch('job.clock._check_rule')
    def test_perform_tick(self, mock_check_rule):
        '''Tests performing a single clock tick.'''
        job_test_utils.create_clock_rule()
        job_test_utils.create_clock_rule()

        clock.perform_tick()

        self.assertEqual(mock_check_rule.call_count, 2)

    @patch('job.clock._check_rule')
    def test_perform_tick_skip(self, mock_check_rule):
        '''Tests performing a single clock tick with rules that should be skipped.'''
        job_test_utils.create_clock_rule(is_active=False)
        job_test_utils.create_clock_rule(rule_type='NOT_CLOCK')

        clock.perform_tick()

        self.assertFalse(mock_check_rule.called)

    @patch('job.clock._check_rule')
    def test_perform_tick_error(self, mock_check_rule):
        '''Tests performing a clock tick will continue even when rules fail.'''
        mock_check_rule.side_effect = ClockEventError()

        job_test_utils.create_clock_rule()
        job_test_utils.create_clock_rule()

        clock.perform_tick()

        self.assertEqual(mock_check_rule.call_count, 2)

    @patch('job.clock._trigger_event')
    @patch('job.clock._check_schedule')
    def test_check_rule(self, mock_check_schedule, mock_trigger_event):
        '''Tests a valid rule triggers a new event.'''
        mock_check_schedule.return_value = True

        rule = job_test_utils.create_clock_rule(name='test-name', schedule='PT1H0M0S')

        clock._check_rule(rule)

        mock_check_schedule.assert_called_with(datetime.timedelta(hours=1), None)
        self.assertTrue(mock_trigger_event.called)

    @patch('job.clock._trigger_event')
    @patch('job.clock._check_schedule')
    def test_check_rule_last_event(self, mock_check_schedule, mock_trigger_event):
        '''Tests a valid rule checks the most recent matching event type.'''
        rule = job_test_utils.create_clock_rule(name='test-name', schedule='PT1H0M0S')
        job_test_utils.create_clock_event(rule=rule, occurred=datetime.datetime(2013, 1, 1, tzinfo=timezone.utc))
        job_test_utils.create_clock_event(rule=rule, occurred=datetime.datetime(2012, 1, 1, tzinfo=timezone.utc))
        last = job_test_utils.create_clock_event(rule=rule, occurred=datetime.datetime(2014, 1, 1, tzinfo=timezone.utc))
        job_test_utils.create_clock_event(rule=rule, occurred=datetime.datetime(2011, 1, 1, tzinfo=timezone.utc))
        job_test_utils.create_clock_event(occurred=datetime.datetime(2015, 1, 1, tzinfo=timezone.utc))

        clock._check_rule(rule)

        mock_check_schedule.assert_called_with(datetime.timedelta(hours=1), last)

    @patch('job.clock._trigger_event')
    @patch('job.clock._check_schedule')
    def test_check_rule_skip(self, mock_check_schedule, mock_trigger_event):
        '''Tests a valid rule does not trigger a new event when the schedule threshold has not been met.'''
        mock_check_schedule.return_value = False

        rule = job_test_utils.create_clock_rule(name='test-name')

        clock._check_rule(rule)

        self.assertTrue(mock_check_schedule.called)
        self.assertFalse(mock_trigger_event.called)

    def test_check_rule_name_error(self):
        '''Tests checking a rule with a name configuration problem.'''
        rule1 = job_test_utils.create_clock_rule(name='')
        self.assertRaises(ClockEventError, clock._check_rule, rule1)

        rule2 = job_test_utils.create_clock_rule(name='missing')
        self.assertRaises(ClockEventError, clock._check_rule, rule2)

    def test_check_rule_event_type_error(self):
        '''Tests checking a rule with an event type configuration problem.'''
        rule = job_test_utils.create_clock_rule(event_type='')
        self.assertRaises(ClockEventError, clock._check_rule, rule)

    def test_check_rule_schedule_error(self):
        '''Tests checking a rule with a schedule configuration problem.'''
        rule1 = job_test_utils.create_clock_rule(schedule='')
        self.assertRaises(ClockEventError, clock._check_rule, rule1)

        rule2 = job_test_utils.create_clock_rule(schedule='invalid')
        self.assertRaises(ClockEventError, clock._check_rule, rule2)

        rule3 = job_test_utils.create_clock_rule(schedule='1H0M0S')
        self.assertRaises(ClockEventError, clock._check_rule, rule1)

    @patch('job.clock.timezone.now', lambda: datetime.datetime(2015, 1, 1, 1, 30, 30, tzinfo=timezone.utc))
    def test_check_schedule_hour_first(self):
        '''Tests checking an hourly schedule that was never triggered before and is due now.'''
        self.assertTrue(clock._check_schedule(datetime.timedelta(hours=1), None))

    @patch('job.clock.timezone.now', lambda: datetime.datetime(2015, 1, 1, 0, 30, 30, tzinfo=timezone.utc))
    def test_check_schedule_hour_first_skip(self):
        '''Tests checking an hourly schedule that was never triggered before and is not due.'''
        self.assertFalse(clock._check_schedule(datetime.timedelta(hours=1), None))

    @patch('job.clock.timezone.now', lambda: datetime.datetime(2015, 1, 1, 12, 30, 30, tzinfo=timezone.utc))
    def test_check_schedule_hour_last(self):
        '''Tests checking an hourly schedule that was triggered before and is due now.'''
        last = job_test_utils.create_clock_event(occurred=datetime.datetime(2015, 1, 1, 11, tzinfo=timezone.utc))

        self.assertTrue(clock._check_schedule(datetime.timedelta(hours=1), last))

    @patch('job.clock.timezone.now', lambda: datetime.datetime(2015, 1, 1, 12, 30, 30, tzinfo=timezone.utc))
    def test_check_schedule_hour_last_skip(self):
        '''Tests checking an hourly schedule that was triggered before and is not due.'''
        last = job_test_utils.create_clock_event(occurred=datetime.datetime(2015, 1, 1, 12, tzinfo=timezone.utc))

        self.assertFalse(clock._check_schedule(datetime.timedelta(hours=1), last))

    @patch('job.clock.timezone.now', lambda: datetime.datetime(2015, 1, 1, 10, 30, tzinfo=timezone.utc))
    def test_check_schedule_hour_exact(self):
        '''Tests checking a schedule for once an hour.'''
        last = job_test_utils.create_clock_event(occurred=datetime.datetime(2015, 1, 1, 9, tzinfo=timezone.utc))

        self.assertTrue(clock._check_schedule(datetime.timedelta(hours=1), last))

    @patch('job.clock.timezone.now', lambda: datetime.datetime(2015, 1, 1, 23, 30, tzinfo=timezone.utc))
    def test_check_schedule_hour_recover(self):
        '''Tests checking a schedule to recover after being down for several hours.'''
        last = job_test_utils.create_clock_event(occurred=datetime.datetime(2015, 1, 1, 5, tzinfo=timezone.utc))

        self.assertTrue(clock._check_schedule(datetime.timedelta(hours=1), last))

    @patch('job.clock.timezone.now', lambda: datetime.datetime(2015, 1, 10, 10, 30, tzinfo=timezone.utc))
    def test_check_schedule_hour_drift_min(self):
        '''Tests checking a schedule for once an hour without slowly drifting away from the target time.'''
        last = job_test_utils.create_clock_event(occurred=datetime.datetime(2015, 1, 10, 8, tzinfo=timezone.utc))

        self.assertTrue(clock._check_schedule(datetime.timedelta(hours=1), last))

    @patch('job.clock.timezone.now', lambda: datetime.datetime(2015, 1, 1, 12, 0, 30, tzinfo=timezone.utc))
    def test_check_schedule_day_first(self):
        '''Tests checking a daily schedule that was never triggered before and is due now.'''
        self.assertTrue(clock._check_schedule(datetime.timedelta(hours=24), None))

    @patch('job.clock.timezone.now', lambda: datetime.datetime(2015, 1, 10, 1, 0, 30, tzinfo=timezone.utc))
    def test_check_schedule_day_last(self):
        '''Tests checking a daily schedule that was triggered before and is due now.'''
        last = job_test_utils.create_clock_event(occurred=datetime.datetime(2015, 1, 9, tzinfo=timezone.utc))

        self.assertTrue(clock._check_schedule(datetime.timedelta(hours=24), last))

    @patch('job.clock.timezone.now', lambda: datetime.datetime(2015, 1, 10, 12, 30, 30, tzinfo=timezone.utc))
    def test_check_schedule_day_last_skip(self):
        '''Tests checking a daily schedule that was triggered before and is not due.'''
        last = job_test_utils.create_clock_event(occurred=datetime.datetime(2015, 1, 10, tzinfo=timezone.utc))

        self.assertFalse(clock._check_schedule(datetime.timedelta(hours=24), last))

    @patch('job.clock.timezone.now', lambda: datetime.datetime(2015, 1, 10, 0, 0, 30, tzinfo=timezone.utc))
    def test_check_schedule_day_exact(self):
        '''Tests checking a schedule for once a day.'''
        last = job_test_utils.create_clock_event(occurred=datetime.datetime(2015, 1, 9, tzinfo=timezone.utc))

        self.assertTrue(clock._check_schedule(datetime.timedelta(hours=24), last))

    @patch('job.clock.timezone.now', lambda: datetime.datetime(2015, 1, 10, 10, 0, 30, tzinfo=timezone.utc))
    def test_check_schedule_day_recover(self):
        '''Tests checking a schedule to recover after being down for several days.'''
        last = job_test_utils.create_clock_event(occurred=datetime.datetime(2015, 1, 5, 0, 5, 50, tzinfo=timezone.utc))

        self.assertTrue(clock._check_schedule(datetime.timedelta(hours=24), last))

    @patch('job.clock.timezone.now', lambda: datetime.datetime(2015, 1, 10, 0, 0, 30, tzinfo=timezone.utc))
    def test_check_schedule_day_drift(self):
        '''Tests checking a schedule for once a day without slowly drifting away from the target time.'''
        last = job_test_utils.create_clock_event(occurred=datetime.datetime(2015, 1, 9, 0, 45, 30, tzinfo=timezone.utc))

        self.assertTrue(clock._check_schedule(datetime.timedelta(hours=24), last))

    def test_trigger_event_first(self):
        '''Tests triggering a new event the first time for a rule.'''
        rule = job_test_utils.create_clock_rule(name='test-name', event_type='TEST_TYPE')

        clock._trigger_event(rule, None)

        events = TriggerEvent.objects.filter(type='TEST_TYPE')
        self.assertEqual(len(events), 1)
        self.processor.process_event.assert_called_with(events[0], None)

    def test_trigger_event_last(self):
        '''Tests triggering a new event after the rule has processed an event previously.'''
        rule = job_test_utils.create_clock_rule(name='test-name', event_type='TEST_TYPE')
        last = job_test_utils.create_clock_event(rule=rule, occurred=datetime.datetime(2015, 1, 1, tzinfo=timezone.utc))

        clock._trigger_event(rule, last)

        events = TriggerEvent.objects.filter(type='TEST_TYPE').order_by('-occurred')
        self.assertEqual(len(events), 2)
        self.assertNotEqual(events[0], last)
        self.processor.process_event.assert_called_with(events[0], last)

    def test_multiple_processors(self):
        '''Tests running multiple processors for the same trigger rule.'''
        clock.register_processor('test-name', lambda: self.processor)

        rule = job_test_utils.create_clock_rule(name='test-name', event_type='TEST_TYPE')
        clock._trigger_event(rule)

        self.assertEqual(self.processor.process_event.call_count, 2)
