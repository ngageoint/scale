from __future__ import unicode_literals

import django
from django.test import TestCase
from django.utils.timezone import now

import job.test.utils as job_test_utils
from error.exceptions import ScaleDatabaseError, ScaleIOError, ScaleOperationalError
from error.models import reset_error_cache
from job.execution.configuration.exceptions import MissingSetting
from job.execution.configuration.json.exe_config import ExecutionConfiguration
from job.execution.tasks.pre_task import PreTask
from job.tasks.update import TaskStatusUpdate


class TestPreTask(TestCase):
    """Tests the PreTask class"""

    fixtures = ['basic_errors.json', 'basic_job_errors.json']

    def setUp(self):
        django.setup()

        self.job_exe = job_test_utils.create_job_exe()

        # Clear error cache so tests work correctly
        reset_error_cache()

    def test_determine_error(self):
        """Tests that a pre-task successfully determines the correct error"""

        scale_errors = [ScaleDatabaseError(), ScaleIOError(), ScaleOperationalError(), MissingSetting('')]

        for scale_error in scale_errors:
            config = ExecutionConfiguration()
            config.create_tasks(['pre'])
            config.set_task_ids(self.job_exe.get_cluster_id())
            task = PreTask('agent_1', self.job_exe, self.job_exe.job_type, config)
            update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.RUNNING, now())
            task.update(update)
            update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.FAILED, now(),
                                                              exit_code=scale_error.exit_code)
            error = task.determine_error(update)
            self.assertEqual(scale_error.error_name, error.name)
