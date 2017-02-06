from __future__ import unicode_literals

import django
from django.test import TestCase
from django.utils.timezone import now

import job.test.utils as job_test_utils
from error.exceptions import ScaleDatabaseError, ScaleIOError, ScaleOperationalError
from job.configuration.results.exceptions import InvalidResultsManifest, MissingRequiredOutput
from job.execution.tasks.post_task import PostTask
from job.tasks.update import TaskStatusUpdate


class TestPostTask(TestCase):
    """Tests the PostTask class"""

    fixtures = ['basic_errors.json', 'basic_job_errors.json']

    def setUp(self):
        django.setup()

        self.job_exe = job_test_utils.create_job_exe()

    def test_determine_error(self):
        """Tests that a post-task successfully determines the correct error"""

        scale_errors = [ScaleDatabaseError(), ScaleIOError(), ScaleOperationalError(), InvalidResultsManifest(''),
                        MissingRequiredOutput('')]

        for scale_error in scale_errors:
            task = PostTask(self.job_exe)
            update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.RUNNING, now())
            task.update(update)
            update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.FAILED, now(),
                                                              exit_code=scale_error.exit_code)
            error = task.determine_error(update)
            self.assertEqual(scale_error.error_name, error.name)
