from __future__ import unicode_literals

import django
from django.test import TestCase

from scheduler.manager import SchedulerManager
from scheduler.models import Scheduler


class TestSchedulerManager(TestCase):

    def setUp(self):
        django.setup()

    def test_successful_update(self):
        """Tests doing a successful database update"""

        manager = SchedulerManager()
        manager.sync_with_database()
