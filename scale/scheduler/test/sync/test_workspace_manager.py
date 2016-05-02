from __future__ import unicode_literals

import django
from django.test import TestCase

from scheduler.sync.workspace_manager import WorkspaceManager


class TestWorkspaceManager(TestCase):

    def setUp(self):
        django.setup()

    def test_successful_update(self):
        """Tests doing a successful database update"""

        manager = WorkspaceManager()
        manager.sync_with_database()
