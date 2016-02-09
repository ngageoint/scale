from __future__ import unicode_literals

import django
from django.test import TestCase

from scheduler.sync.job_type_manager import JobTypeManager


class TestJobTypeManager(TestCase):

    def setUp(self):
        django.setup()

    def test_successful_update(self):
        """Tests doing a successful database update"""

        manager = JobTypeManager()
        manager.sync_with_database()
