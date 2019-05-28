from __future__ import unicode_literals
from __future__ import absolute_import

import datetime

import django
from django.test import TransactionTestCase
from django.utils.timezone import utc
from mock import call, patch

from data.data.json.data_v6 import convert_data_to_v6_json
import job.test.utils as job_test_utils
from metrics.daily_metrics import DailyMetricsProcessor


class TestDailyMetricsProcessor(TransactionTestCase):
    """Tests the DailyMetricsProcessor clock event class."""

    def setUp(self):
        django.setup()
        manifest = job_test_utils.create_seed_manifest(name='scale-daily-metrics')
        self.job_type = job_test_utils.create_seed_job_type(manifest=manifest)
        self.processor = DailyMetricsProcessor()

    @patch('metrics.daily_metrics.Queue')
    @patch('metrics.daily_metrics.timezone.now', lambda: datetime.datetime(2015, 1, 10, tzinfo=utc))
    def test_process_event_first(self, mock_Queue):
        """Tests processing an event that was never triggered before."""
        event = job_test_utils.create_clock_event(occurred=datetime.datetime(2015, 1, 10, 12, tzinfo=utc))

        self.processor.process_event(event, None)

        call_args = mock_Queue.objects.queue_new_job_v6.call_args[0]
        inputs = convert_data_to_v6_json(call_args[1])
        self.assertEqual(self.job_type, call_args[0])
        self.assertDictEqual({u'files': {}, u'json': {u'DAY': '2015-01-09'}, u'version': u'6'}, inputs.get_dict())
        self.assertEqual(event, call_args[2])

    @patch('metrics.daily_metrics.Queue')
    @patch('metrics.daily_metrics.timezone.now', lambda: datetime.datetime(2015, 1, 10, tzinfo=utc))
    def test_process_event_last(self, mock_Queue):
        """Tests processing an event that was triggered before."""
        event = job_test_utils.create_clock_event(occurred=datetime.datetime(2015, 1, 10, 12, second=9, tzinfo=utc))
        last = job_test_utils.create_clock_event(occurred=datetime.datetime(2015, 1, 9, 12, second=10, tzinfo=utc))

        self.processor.process_event(event, last)

        call_args = mock_Queue.objects.queue_new_job_v6.call_args[0]
        self.assertEqual(self.job_type, call_args[0])
        inputs = convert_data_to_v6_json(call_args[1])
        self.assertDictEqual({u'files': {}, u'json': {u'DAY': '2015-01-09'}, u'version': u'6'}, inputs.get_dict())
        self.assertEqual(event, call_args[2])

    @patch('metrics.daily_metrics.Queue')
    @patch('metrics.daily_metrics.timezone.now', lambda: datetime.datetime(2015, 1, 10, tzinfo=utc))
    def test_process_event_range(self, mock_Queue):
        """Tests processing an event that requires catching up for a range of previous days."""
        event = job_test_utils.create_clock_event(occurred=datetime.datetime(2015, 1, 10, 10, tzinfo=utc))
        last = job_test_utils.create_clock_event(occurred=datetime.datetime(2015, 1, 7, 12, tzinfo=utc))

        self.processor.process_event(event, last)

        i = 1
        for call_args in mock_Queue.objects.queue_new_job_v6.call_args_list:
            args = call_args[0]
            self.assertEqual(self.job_type, args[0])
            self.assertEqual(event, args[2])

            inputs = convert_data_to_v6_json(args[1])
            if i == 1:
                self.assertDictEqual({u'files': {}, u'json': {u'DAY': '2015-01-07'}, u'version': u'6'}, inputs.get_dict())
            if i == 2:
                self.assertDictEqual({u'files': {}, u'json': {u'DAY': '2015-01-08'}, u'version': u'6'}, inputs.get_dict())
            if i == 3:
                self.assertDictEqual({u'files': {}, u'json': {u'DAY': '2015-01-09'}, u'version': u'6'}, inputs.get_dict())
            i += 1

        self.assertEqual(mock_Queue.objects.queue_new_job_v6.call_count, 3)

    @patch('metrics.daily_metrics.Queue')
    @patch('metrics.daily_metrics.timezone.now', lambda: datetime.datetime(2015, 1, 10, tzinfo=utc))
    def test_process_event_duplicate(self, mock_Queue):
        """Tests processing an event that was previously handled."""
        event = job_test_utils.create_clock_event(occurred=datetime.datetime(2015, 1, 10, 12, tzinfo=utc))
        last = job_test_utils.create_clock_event(occurred=datetime.datetime(2015, 1, 10, 10, tzinfo=utc))

        self.processor.process_event(event, last)

        self.assertFalse(mock_Queue.objects.queue_new_job_v6.called)
