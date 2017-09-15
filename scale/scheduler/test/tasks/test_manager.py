from __future__ import unicode_literals

import datetime

import django
from django.test import TestCase
from django.utils.timezone import now

from job.tasks.manager import TaskManager
from job.tasks.update import TaskStatusUpdate
from job.test import utils as job_test_utils
from scheduler.manager import scheduler_mgr
from scheduler.tasks.db_update_task import DB_UPDATE_TASK_ID_PREFIX
from scheduler.tasks.manager import SystemTaskManager


class TestSystemTaskManager(TestCase):

    def setUp(self):
        django.setup()

        self.agent_id = 'agent_1'
        self.system_task_mgr = SystemTaskManager()
        self.task_mgr = TaskManager()

        # Make sure messaging service is "off" for these tests
        scheduler_mgr.config.num_message_handlers = 0

    def test_handle_completed_db_update_task(self):
        """Tests handling completed database update task"""

        # Get database update task
        when = now()
        self.assertFalse(self.system_task_mgr._is_db_update_completed)
        task = self.system_task_mgr.get_tasks_to_schedule(when)[0]
        self.assertTrue(task.id.startswith(DB_UPDATE_TASK_ID_PREFIX))
        task_1_id = task.id

        # Schedule database update task and make sure there are no more system tasks 
        task.agent_id = self.agent_id
        self.task_mgr.launch_tasks([task], now())
        self.assertListEqual([], self.system_task_mgr.get_tasks_to_schedule(now()))

        # Complete task, verify no new tasks
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.RUNNING, now())
        self.task_mgr.handle_task_update(update)
        self.system_task_mgr.handle_task_update(update)
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.FINISHED, now())
        self.task_mgr.handle_task_update(update)
        self.system_task_mgr.handle_task_update(update)
        self.assertListEqual([], self.system_task_mgr.get_tasks_to_schedule(now()))
        self.assertTrue(self.system_task_mgr._is_db_update_completed)

    def test_handle_failed_db_update_task(self):
        """Tests handling failed database update task"""

        # Get database update task
        when = now()
        self.assertFalse(self.system_task_mgr._is_db_update_completed)
        task = self.system_task_mgr.get_tasks_to_schedule(when)[0]
        self.assertTrue(task.id.startswith(DB_UPDATE_TASK_ID_PREFIX))
        task_1_id = task.id

        # Fail task after running and get different task next time
        task.agent_id = self.agent_id
        self.task_mgr.launch_tasks([task], now())
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.RUNNING, now())
        self.task_mgr.handle_task_update(update)
        self.system_task_mgr.handle_task_update(update)
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.FAILED, now())
        self.task_mgr.handle_task_update(update)
        self.system_task_mgr.handle_task_update(update)

        # No new database update right away
        tasks = self.system_task_mgr.get_tasks_to_schedule(when + datetime.timedelta(seconds=5))
        self.assertListEqual([], tasks)
        self.assertFalse(self.system_task_mgr._is_db_update_completed)

        # After error threshold, we should get new database update task
        new_time = when + SystemTaskManager.DATABASE_UPDATE_ERR_THRESHOLD + datetime.timedelta(seconds=5)
        task = self.system_task_mgr.get_tasks_to_schedule(new_time)[0]
        self.assertNotEqual(task.id, task_1_id)
        self.assertTrue(task.id.startswith(DB_UPDATE_TASK_ID_PREFIX))
        self.assertFalse(self.system_task_mgr._is_db_update_completed)

    def test_handle_killed_db_update_task(self):
        """Tests handling killed database update task"""

        # Get database update task
        when = now()
        self.assertFalse(self.system_task_mgr._is_db_update_completed)
        task = self.system_task_mgr.get_tasks_to_schedule(when)[0]
        self.assertTrue(task.id.startswith(DB_UPDATE_TASK_ID_PREFIX))
        task_1_id = task.id

        # Kill task after running and get different task next time
        task.agent_id = self.agent_id
        self.task_mgr.launch_tasks([task], now())
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.RUNNING, now())
        self.task_mgr.handle_task_update(update)
        self.system_task_mgr.handle_task_update(update)
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.KILLED, now())
        self.task_mgr.handle_task_update(update)
        self.system_task_mgr.handle_task_update(update)
        task = self.system_task_mgr.get_tasks_to_schedule(when)[0]
        self.assertTrue(task.id.startswith(DB_UPDATE_TASK_ID_PREFIX))
        self.assertNotEqual(task.id, task_1_id)
        self.assertFalse(self.system_task_mgr._is_db_update_completed)

    def test_handle_lost_db_update_task(self):
        """Tests handling lost database update task"""

        # Get database update task
        when = now()
        self.assertFalse(self.system_task_mgr._is_db_update_completed)
        task = self.system_task_mgr.get_tasks_to_schedule(when)[0]
        self.assertTrue(task.id.startswith(DB_UPDATE_TASK_ID_PREFIX))
        task_1_id = task.id

        # Lose task after scheduling and get different task next time
        task.agent_id = self.agent_id
        self.task_mgr.launch_tasks([task], now())
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.LOST, now())
        self.task_mgr.handle_task_update(update)
        self.system_task_mgr.handle_task_update(update)
        task = self.system_task_mgr.get_tasks_to_schedule(when)[0]
        task_2_id = task.id
        self.assertTrue(task.id.startswith(DB_UPDATE_TASK_ID_PREFIX))
        self.assertNotEqual(task.id, task_1_id)
        self.assertFalse(self.system_task_mgr._is_db_update_completed)

        # Lose task after running and get different task next time
        task.agent_id = self.agent_id
        self.task_mgr.launch_tasks([task], now())
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.RUNNING, now())
        self.task_mgr.handle_task_update(update)
        self.system_task_mgr.handle_task_update(update)
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.LOST, now())
        self.task_mgr.handle_task_update(update)
        self.system_task_mgr.handle_task_update(update)
        task = self.system_task_mgr.get_tasks_to_schedule(when)[0]
        self.assertTrue(task.id.startswith(DB_UPDATE_TASK_ID_PREFIX))
        self.assertNotEqual(task.id, task_1_id)
        self.assertNotEqual(task.id, task_2_id)
        self.assertFalse(self.system_task_mgr._is_db_update_completed)
