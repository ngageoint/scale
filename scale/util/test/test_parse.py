from __future__ import unicode_literals

import datetime

import django
import mock
from django.test import TestCase
from django.utils.timezone import utc

import util.parse as parse_util


class TestParse(TestCase):
    def setUp(self):
        django.setup()

    def test_duration_to_string(self):
        """Tests converting timedelta duration to ISO duration string"""
        duration_1 = datetime.timedelta(seconds=0)
        self.assertEqual(parse_util.duration_to_string(duration_1), 'PT0S')
        duration_2 = datetime.timedelta(days=4, seconds=58426)
        self.assertEqual(parse_util.duration_to_string(duration_2), 'P4DT16H13M46S')
        duration_3 = datetime.timedelta(seconds=542.0894)
        self.assertEqual(parse_util.duration_to_string(duration_3), 'PT9M2S')
        duration_4 = datetime.timedelta(seconds=542.5894)
        self.assertEqual(parse_util.duration_to_string(duration_4), 'PT9M3S')

    def test_parse_duration(self):
        """Tests parsing a valid ISO duration."""
        self.assertEqual(parse_util.parse_duration('PT3H0M0S'), datetime.timedelta(0, 10800))

    def test_parse_duration_invalid(self):
        """Tests parsing an invalid ISO duration."""
        self.assertIsNone(parse_util.parse_duration('BAD'))

    def test_parse_datetime(self):
        """Tests parsing a valid ISO datetime."""
        self.assertEqual(parse_util.parse_datetime('2015-01-01T00:00:00Z'),
                         datetime.datetime(2015, 1, 1, tzinfo=utc))

    def test_parse_datetime_invalid(self):
        """Tests parsing an invalid ISO datetime."""
        self.assertIsNone(parse_util.parse_datetime('20150101T00:00:00Z'))

    def test_parse_datetime_missing_timezone(self):
        """Tests parsing an ISO datetime missing a timezone."""
        self.assertRaises(ValueError, parse_util.parse_datetime, '2015-01-01T00:00:00')

    @mock.patch('django.utils.timezone.now')
    def test_parse_timestamp_duration(self, mock_now):
        """Tests parsing a valid ISO duration."""
        mock_now.return_value = datetime.datetime(2015, 1, 1, 10, tzinfo=utc)
        self.assertEqual(parse_util.parse_timestamp('PT3H0M0S'), datetime.datetime(2015, 1, 1, 7, tzinfo=utc))

    def test_parse_timestamp_datetime(self):
        """Tests parsing a valid ISO datetime."""
        self.assertEqual(parse_util.parse_timestamp('2015-01-01T00:00:00Z'),
                         datetime.datetime(2015, 1, 1, tzinfo=utc))
