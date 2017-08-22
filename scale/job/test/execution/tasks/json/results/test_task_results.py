from __future__ import unicode_literals

import django
from django.test import TestCase

from job.execution.exceptions import InvalidTaskResults
from job.execution.tasks.json.results.task_results import TaskResults


class TestTaskResults(TestCase):

    def setUp(self):
        django.setup()

    def test_init_validation(self):
        """Tests the validation done in __init__"""

        # Try minimal acceptable configuration
        TaskResults()

        # Invalid version
        config = {'version': 'BAD'}
        self.assertRaises(InvalidTaskResults, TaskResults, config)
