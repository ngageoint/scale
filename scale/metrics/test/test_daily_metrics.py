#@PydevCodeAnalysisIgnore
import datetime

import django
import django.utils.timezone as timezone
from django.test import TestCase
from mock import call, patch

import job.test.utils as job_test_utils
from metrics.daily_metrics import DailyMetricsProcessor


class TestDailyMetricsProcessor(TestCase):
    '''Tests the DailyMetricsProcessor clock event class.'''

    def setUp(self):
        django.setup()

        self.job_type = job_test_utils.create_job_type(name=u'scale-daily-metrics')
        self.processor = DailyMetricsProcessor()

    @patch('metrics.daily_metrics.Queue')
    @patch('metrics.daily_metrics.timezone.now', lambda: datetime.datetime(2015, 1, 10, tzinfo=timezone.utc))
    def test_process_event_first(self, mock_Queue):
        '''Tests processing an event that was never triggered before.'''
        event = job_test_utils.create_clock_event(occurred=datetime.datetime(2015, 1, 10, 12, tzinfo=timezone.utc))

        self.processor.process_event(event, None)

        job_data = {u'input_data': [{u'name': u'Day', u'value': u'2015-01-09'}]}
        mock_Queue.objects.queue_new_job.assert_called_with(self.job_type, job_data, event)

    @patch('metrics.daily_metrics.Queue')
    @patch('metrics.daily_metrics.timezone.now', lambda: datetime.datetime(2015, 1, 10, tzinfo=timezone.utc))
    def test_process_event_last(self, mock_Queue):
        '''Tests processing an event that was triggered before.'''
        event = job_test_utils.create_clock_event(occurred=datetime.datetime(2015, 1, 10, 12, second=9, tzinfo=timezone.utc))
        last = job_test_utils.create_clock_event(occurred=datetime.datetime(2015, 1, 9, 12, second=10, tzinfo=timezone.utc))

        self.processor.process_event(event, last)

        job_data = {u'input_data': [{u'name': u'Day', u'value': u'2015-01-09'}]}
        mock_Queue.objects.queue_new_job.assert_called_with(self.job_type, job_data, event)

    @patch('metrics.daily_metrics.Queue')
    @patch('metrics.daily_metrics.timezone.now', lambda: datetime.datetime(2015, 1, 10, tzinfo=timezone.utc))
    def test_process_event_range(self, mock_Queue):
        '''Tests processing an event that requires catching up for a range of previous days.'''
        event = job_test_utils.create_clock_event(occurred=datetime.datetime(2015, 1, 10, 10, tzinfo=timezone.utc))
        last = job_test_utils.create_clock_event(occurred=datetime.datetime(2015, 1, 7, 12, tzinfo=timezone.utc))

        self.processor.process_event(event, last)

        calls = [
            call(self.job_type, {u'input_data': [{u'name': u'Day', u'value': u'2015-01-07'}]}, event),
            call(self.job_type, {u'input_data': [{u'name': u'Day', u'value': u'2015-01-08'}]}, event),
            call(self.job_type, {u'input_data': [{u'name': u'Day', u'value': u'2015-01-09'}]}, event),
        ]
        mock_Queue.objects.queue_new_job.assert_has_calls(calls)
        self.assertEqual(mock_Queue.objects.queue_new_job.call_count, 3)

    @patch('metrics.daily_metrics.Queue')
    @patch('metrics.daily_metrics.timezone.now', lambda: datetime.datetime(2015, 1, 10, tzinfo=timezone.utc))
    def test_process_event_duplicate(self, mock_Queue):
        '''Tests processing an event that was previously handled.'''
        event = job_test_utils.create_clock_event(occurred=datetime.datetime(2015, 1, 10, 12, tzinfo=timezone.utc))
        last = job_test_utils.create_clock_event(occurred=datetime.datetime(2015, 1, 10, 10, tzinfo=timezone.utc))

        self.processor.process_event(event, last)

        self.assertFalse(mock_Queue.objects.queue_new_job.called)
