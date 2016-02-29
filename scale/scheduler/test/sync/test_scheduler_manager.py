from __future__ import unicode_literals

import django
from django.test import TestCase

from scheduler.models import Scheduler
from scheduler.sync.scheduler_manager import SchedulerManager


class TestSchedulerManager(TestCase):

    def setUp(self):
        django.setup()

    def test_successful_update(self):
        """Tests doing a successful database update"""

        manager = SchedulerManager(Scheduler())
        manager.sync_with_database()
