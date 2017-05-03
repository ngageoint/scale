from __future__ import unicode_literals

import django
from django.test import TestCase

from scheduler.sync.job_type_manager import JobTypeManager


class TestJobTypeManager(TestCase):

    fixtures = ['basic_system_job_types.json']

    def setUp(self):
        django.setup()

    def test_successful_update_and_create_json(self):
        """Tests doing a successful database update and creating status JSON"""

        manager = JobTypeManager()
        manager.sync_with_database()
        status_dict = {}
        manager.generate_status_json(status_dict)

        self.assertEqual(len(status_dict['job_types']), 1)
