from __future__ import unicode_literals

import datetime

import django
import django.utils.timezone as timezone
from django.test import TestCase

from batch.configuration.definition.exceptions import InvalidDefinition
from batch.configuration.definition.batch_definition import BatchDefinition


class TestBatchDefinition(TestCase):

    def setUp(self):
        django.setup()

    def test_minimum(self):
        """Tests the bare minimum schema definition"""

        definition = {
            'version': '1.0',
        }

        # No exception means success
        BatchDefinition(definition)

    def test_date_range(self):
        """Tests defining a date range"""

        definition = {
            'version': '1.0',
            'date_range': {
                'started': '2016-01-01T00:00:00.000Z',
                'ended': '2016-12-31T00:00:00.000Z',
            },
        }

        # No exception means success
        batch_def = BatchDefinition(definition)
        self.assertEqual(batch_def.started, datetime.datetime(2016, 1, 1, tzinfo=timezone.utc))
        self.assertEqual(batch_def.ended, datetime.datetime(2016, 12, 31, tzinfo=timezone.utc))

    def test_date_range_started(self):
        """Tests defining a date range with only a start date"""

        definition = {
            'version': '1.0',
            'date_range': {
                'started': '2016-01-01T00:00:00.000Z',
            },
        }

        # No exception means success
        batch_def = BatchDefinition(definition)
        self.assertEqual(batch_def.started, datetime.datetime(2016, 1, 1, tzinfo=timezone.utc))

    def test_date_range_ended(self):
        """Tests defining a date range with only an end date"""

        definition = {
            'version': '1.0',
            'date_range': {
                'ended': '2016-12-31T00:00:00.000Z',
            },
        }

        # No exception means success
        batch_def = BatchDefinition(definition)
        self.assertEqual(batch_def.ended, datetime.datetime(2016, 12, 31, tzinfo=timezone.utc))

    def test_date_range_type_invalid(self):
        """Tests defining a date range with an invalid enumerated type"""

        definition = {
            'version': '1.0',
            'date_range': {
                'type': 'BAD',
            },
        }

        self.assertRaises(InvalidDefinition, BatchDefinition, definition)

    def test_date_range_invalid(self):
        """Tests defining a date range with an invalid format"""

        definition = {
            'version': '1.0',
            'date_range': {
                'started': 'BAD',
            },
        }

        self.assertRaises(InvalidDefinition, BatchDefinition, definition)

    def test_job_names(self):
        """Tests defining a list of job names"""

        definition = {
            'version': '1.0',
            'job_names': [
                'job1',
                'job2',
            ],
        }

        # No exception means success
        BatchDefinition(definition)

    def test_all_job(self):
        """Tests defining all jobs"""

        definition = {
            'version': '1.0',
            'all_jobs': True,
        }

        # No exception means success
        BatchDefinition(definition)

    def test_priority(self):
        """Tests defining override priority."""

        definition = {
            'version': '1.0',
            'priority': 1111,
        }

        # No exception means success
        BatchDefinition(definition)

    def test_priority_invalid(self):
        """Tests defining override priority with an invalid format."""

        definition = {
            'version': '1.0',
            'priority': 'BAD',
        }

        self.assertRaises(InvalidDefinition, BatchDefinition, definition)
