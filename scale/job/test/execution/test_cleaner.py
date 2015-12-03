#@PydevCodeAnalysisIgnore
import datetime

import django
import django.utils.timezone as timezone
from django.test import TestCase
from mock import MagicMock, patch

import job.clock as clock
import job.test.utils as job_test_utils
from job.clock import ClockEventError, ClockEventProcessor
from trigger.models import TriggerEvent


class TestNormalJobExecutionCleaner(TestCase):
    '''Tests functions in the normal job execution cleaner module.'''

    def setUp(self):
        django.setup()

    def test_stats_collection(self):
        '''Tests collecting statistics.'''
        pass
