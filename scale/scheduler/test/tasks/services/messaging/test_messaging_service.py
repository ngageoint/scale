from __future__ import unicode_literals

import django
from django.test import TestCase
from django.utils.timezone import now

from job.tasks.manager import task_mgr
from job.tasks.update import TaskStatusUpdate
from job.test import utils as job_test_utils
from scheduler.manager import scheduler_mgr
from scheduler.tasks.services.messaging.messaging_service import MessagingService


class TestMessagingService(TestCase):

    def setUp(self):
        django.setup()

    def test_generate_status_json(self):
        """Tests calling generate_status_json() successfully"""

        scheduler_mgr.config.num_message_handlers = 2

        service = MessagingService()
        status_json = service.generate_status_json()

        self.assertEqual(status_json['actual_count'], 0)
        self.assertEqual(status_json['desired_count'], 2)

    def test_get_tasks_to_kill(self):
        """Tests calling get_tasks_to_kill() successfully"""

        # Start with 5 tasks
        scheduler_mgr.config.num_message_handlers = 5
        service = MessagingService()
        tasks = service.get_tasks_to_schedule()
        task_mgr.launch_tasks(tasks, now())

        # Lower number of desired tasks to 3, should get 2 to kill
        scheduler_mgr.config.num_message_handlers = 3
        tasks_to_kill = service.get_tasks_to_kill()
        self.assertEqual(len(tasks_to_kill), 2)

        # Kill the 2 tasks
        for task in tasks_to_kill:
            update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.KILLED, now())
            task_mgr.handle_task_update(update)
            service.handle_task_update(update)
        self.assertEqual(service.get_actual_task_count(), 3)

        # Increase desired tasks to 10, should not get any to kill
        scheduler_mgr.config.num_message_handlers = 10
        tasks_to_kill = service.get_tasks_to_kill()
        self.assertEqual(len(tasks_to_kill), 0)

    def test_get_tasks_to_schedule(self):
        """Tests calling get_tasks_to_schedule() successfully"""

        # Set desired tasks to 5
        scheduler_mgr.config.num_message_handlers = 5
        service = MessagingService()

        # Should get 5 tasks to schedule
        tasks = service.get_tasks_to_schedule()
        self.assertEqual(len(tasks), 5)

        # Launch the 5 tasks
        task_mgr.launch_tasks(tasks, now())
        self.assertEqual(service.get_actual_task_count(), 5)

        # Lower number of desired tasks to 3, should not get any to schedule
        scheduler_mgr.config.num_message_handlers = 3
        tasks = service.get_tasks_to_schedule()
        self.assertEqual(len(tasks), 0)

    def test_handle_task_update(self):
        """Tests calling handle_task_update() successfully"""

        # Start with 5 tasks
        scheduler_mgr.config.num_message_handlers = 5
        service = MessagingService()
        tasks = service.get_tasks_to_schedule()
        task_mgr.launch_tasks(tasks, now())

        # One task fails
        task = tasks[0]
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.FAILED, now())
        task_mgr.handle_task_update(update)
        service.handle_task_update(update)
        self.assertEqual(service.get_actual_task_count(), 4)

        # Should get one new task to schedule
        tasks = service.get_tasks_to_schedule()
        self.assertEqual(len(tasks), 1)
