from __future__ import unicode_literals

import datetime

import django
import django.utils.timezone as timezone
import mock
from django.test import TestCase

import util.parse as parse_util


class TestParse(TestCase):
    def setUp(self):
        django.setup()

    def test_parse_duration(self):
        """Tests parsing a valid ISO duration."""
        self.assertEqual(parse_util.parse_duration('PT3H0M0S'), datetime.timedelta(0, 10800))

    def test_parse_duration_invalid(self):
        """Tests parsing an invalid ISO duration."""
        self.assertIsNone(parse_util.parse_duration('BAD'))

    def test_parse_datetime(self):
        """Tests parsing a valid ISO datetime."""
        self.assertEqual(parse_util.parse_datetime('2015-01-01T00:00:00Z'),
                         datetime.datetime(2015, 1, 1, tzinfo=timezone.utc))

    def test_parse_datetime_invalid(self):
        """Tests parsing an invalid ISO datetime."""
        self.assertIsNone(parse_util.parse_datetime('20150101T00:00:00Z'))

    def test_parse_datetime_missing_timezone(self):
        """Tests parsing an ISO datetime missing a timezone."""
        self.assertRaises(ValueError, parse_util.parse_datetime, '2015-01-01T00:00:00')

    @mock.patch('django.utils.timezone.now')
    def test_parse_timestamp_duration(self, mock_now):
        """Tests parsing a valid ISO duration."""
        mock_now.return_value = datetime.datetime(2015, 1, 1, 10, tzinfo=timezone.utc)
        self.assertEqual(parse_util.parse_timestamp('PT3H0M0S'), datetime.datetime(2015, 1, 1, 7, tzinfo=timezone.utc))

    def test_parse_timestamp_datetime(self):
        """Tests parsing a valid ISO datetime."""
        self.assertEqual(parse_util.parse_timestamp('2015-01-01T00:00:00Z'),
                         datetime.datetime(2015, 1, 1, tzinfo=timezone.utc))
