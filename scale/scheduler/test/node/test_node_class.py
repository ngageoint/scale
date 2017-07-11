from __future__ import unicode_literals

import datetime

import django
from django.test import TestCase
from django.utils.timezone import now
from mock import patch

from job.execution.job_exe import RunningJobExecution
from job.execution.tasks.cleanup_task import CLEANUP_TASK_ID_PREFIX
from job.tasks.health_task import HEALTH_TASK_ID_PREFIX, HealthTask
from job.tasks.manager import TaskManager
from job.tasks.pull_task import PULL_TASK_ID_PREFIX
from job.tasks.update import TaskStatusUpdate
from job.test import utils as job_test_utils
from node.test import utils as node_test_utils
from scheduler.cleanup.node import JOB_EXES_WARNING_THRESHOLD
from scheduler.models import Scheduler
from scheduler.node.conditions import NodeConditions
from scheduler.node.node_class import Node
from util.parse import datetime_to_string


class TestNode(TestCase):

    def setUp(self):
        django.setup()

        self.scheduler = Scheduler()
        self.node_agent = 'agent_1'
        self.node = node_test_utils.create_node(hostname='host_1', slave_id=self.node_agent)
        self.job_exe = job_test_utils.create_job_exe(node=self.node)
        self.task_mgr = TaskManager()

    @patch('scheduler.node.conditions.now')
    def test_generate_status_json(self, mock_now):
        """Tests calling generate_status_json() successfully"""

        right_now = now()
        mock_now.return_value = right_now
        num_job_exes = JOB_EXES_WARNING_THRESHOLD + 1

        node = Node(self.node_agent, self.node, self.scheduler)
        node._conditions.handle_pull_task_failed()
        node._conditions.update_cleanup_count(num_job_exes)
        node._update_state()
        nodes_list = []
        node.generate_status_json(nodes_list)

        expected_results = [{'id': node.id, 'hostname': node.hostname, 'agent_id': self.node_agent, 'is_active': True,
                             'state': {'name': 'DEGRADED', 'title': Node.DEGRADED.title,
                                       'description': Node.DEGRADED.description},
                             'errors': [{'name': 'IMAGE_PULL', 'title': NodeConditions.IMAGE_PULL_ERR.title,
                                         'description': NodeConditions.IMAGE_PULL_ERR.description,
                                         'started': datetime_to_string(right_now),
                                         'last_updated': datetime_to_string(right_now)}],
                             'warnings': [{'name': 'CLEANUP', 'title': NodeConditions.CLEANUP_WARNING.title,
                                           'description': NodeConditions.CLEANUP_WARNING.description % num_job_exes,
                                           'started': datetime_to_string(right_now),
                                           'last_updated': datetime_to_string(right_now)}]}]
        self.assertListEqual(nodes_list, expected_results)

    def test_handle_failed_cleanup_task(self):
        """Tests handling failed cleanup task"""

        when = now()
        node = Node(self.node_agent, self.node, self.scheduler)
        node._last_heath_task = when
        # Get initial cleanup task
        task = node.get_next_tasks(when)[0]
        self.assertTrue(task.id.startswith(CLEANUP_TASK_ID_PREFIX))
        task_1_id = task.id

        # Fail task after running and get different task next time
        self.task_mgr.launch_tasks([task], now())
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.RUNNING, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.FAILED, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)

        # No new cleanup task right away
        tasks = node.get_next_tasks(when + datetime.timedelta(seconds=5))
        self.assertListEqual([], tasks)
        self.assertFalse(node._is_initial_cleanup_completed)

        # After error threshold, we should get new cleanup task
        new_time = when + Node.CLEANUP_ERR_THRESHOLD + datetime.timedelta(seconds=5)
        node._last_heath_task = new_time  # Get rid of health check task
        task = node.get_next_tasks(new_time)[0]
        self.assertNotEqual(task.id, task_1_id)
        self.assertTrue(task.id.startswith(CLEANUP_TASK_ID_PREFIX))

    def test_handle_initial_cleanup_task(self):
        """Tests handling the initial cleanup task"""

        when = now()
        node = Node(self.node_agent, self.node, self.scheduler)
        node._last_heath_task = when

        # Get initial cleanup task
        task = node.get_next_tasks(when)[0]
        self.assertTrue(task.id.startswith(CLEANUP_TASK_ID_PREFIX))
        self.assertTrue(task.is_initial_cleanup)
        self.assertEqual(task.agent_id, self.node_agent)

        # Schedule initial cleanup and make sure no new task is ready
        self.task_mgr.launch_tasks([task], now())
        self.assertListEqual([], node.get_next_tasks(when))
        self.assertFalse(node._is_initial_cleanup_completed)

        # Complete initial clean up, verify no new cleanup task
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.RUNNING, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.FINISHED, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)
        for task in node.get_next_tasks(when):
            self.assertFalse(task.id.startswith(CLEANUP_TASK_ID_PREFIX))
        self.assertTrue(node._is_initial_cleanup_completed)

    def test_handle_killed_cleanup_task(self):
        """Tests handling killed cleanup task"""

        when = now()
        node = Node(self.node_agent, self.node, self.scheduler)
        # Get initial cleanup task
        task = node.get_next_tasks(when)[0]
        self.assertTrue(task.id.startswith(CLEANUP_TASK_ID_PREFIX))
        task_1_id = task.id

        # Kill task after running and get different task next time
        self.task_mgr.launch_tasks([task], now())
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.RUNNING, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.KILLED, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)
        task = node.get_next_tasks(when)[0]
        self.assertTrue(task.id.startswith(CLEANUP_TASK_ID_PREFIX))
        self.assertNotEqual(task.id, task_1_id)
        self.assertFalse(node._is_initial_cleanup_completed)

    def test_handle_lost_cleanup_tasks(self):
        """Tests handling lost cleanup tasks"""

        when = now()
        node = Node(self.node_agent, self.node, self.scheduler)
        # Get initial cleanup task
        task = node.get_next_tasks(when)[0]
        self.assertTrue(task.id.startswith(CLEANUP_TASK_ID_PREFIX))
        task_1_id = task.id

        # Lose task without scheduling and get different task next time
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.LOST, now())
        node.handle_task_update(update)
        task = node.get_next_tasks(when)[0]
        self.assertTrue(task.id.startswith(CLEANUP_TASK_ID_PREFIX))
        self.assertNotEqual(task.id, task_1_id)
        self.assertFalse(node._is_initial_cleanup_completed)

        # Lose task with scheduling and get different task next time
        self.task_mgr.launch_tasks([task], now())
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.LOST, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)
        task = node.get_next_tasks(when)[0]
        self.assertTrue(task.id.startswith(CLEANUP_TASK_ID_PREFIX))
        self.assertNotEqual(task.id, task_1_id)
        self.assertFalse(node._is_initial_cleanup_completed)

        # Lose task after running and get different task next time
        self.task_mgr.launch_tasks([task], now())
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.RUNNING, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.LOST, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)
        task = node.get_next_tasks(when)[0]
        self.assertTrue(task.id.startswith(CLEANUP_TASK_ID_PREFIX))
        self.assertNotEqual(task.id, task_1_id)
        self.assertFalse(node._is_initial_cleanup_completed)

    def test_handle_regular_cleanup_task(self):
        """Tests handling a regular cleanup task"""

        when = now()
        node = Node(self.node_agent, self.node, self.scheduler)
        node._last_heath_task = when
        node._initial_cleanup_completed()
        node._image_pull_completed()
        node._update_state()

        # No task since there are no job executions to clean
        self.assertListEqual([], node.get_next_tasks(when))

        # Add job execution and complete task to clean it up
        job_exe = RunningJobExecution('agent', self.job_exe)
        node.add_job_execution(job_exe)
        task = node.get_next_tasks(when)[0]
        self.assertTrue(task.id.startswith(CLEANUP_TASK_ID_PREFIX))
        self.assertFalse(task.is_initial_cleanup)
        self.assertListEqual(task.job_exes, [job_exe])
        self.task_mgr.launch_tasks([task], now())
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.RUNNING, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.FINISHED, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)

        # No task since all job executions have been cleaned
        self.assertListEqual([], node.get_next_tasks(when))

    def test_paused_node_cleanup_task(self):
        """Tests not returning cleanup task when its node is paused"""

        when = now()
        paused_node = node_test_utils.create_node(hostname='host_1_paused', slave_id='agent_paused')
        paused_node.is_paused = True
        node = Node('agent_paused', paused_node, self.scheduler)
        # Turn off health task
        node._last_heath_task = when
        # No task due to paused node
        self.assertListEqual([], node.get_next_tasks(when))

    def test_handle_failed_health_task(self):
        """Tests handling failed health task"""

        when = now()
        node = Node(self.node_agent, self.node, self.scheduler)
        node._initial_cleanup_completed()
        node._image_pull_completed()
        node._update_state()
        # Get health task
        task = node.get_next_tasks(when)[0]
        task_1_id = task.id
        self.assertTrue(task.id.startswith(HEALTH_TASK_ID_PREFIX))

        # Fail task after running
        self.task_mgr.launch_tasks([task], now())
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.RUNNING, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.FAILED, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)

        # Check node state
        self.assertEqual(node._state, Node.DEGRADED)
        self.assertTrue(NodeConditions.HEALTH_FAIL_ERR.name in node._conditions._active_errors)

        # No new health task right away
        tasks = node.get_next_tasks(when + datetime.timedelta(seconds=5))
        self.assertListEqual([], tasks)
        self.assertFalse(node._conditions.is_health_check_normal)

        # After error threshold, we should get new health task
        new_time = when + Node.HEALTH_ERR_THRESHOLD + datetime.timedelta(seconds=5)
        task = node.get_next_tasks(new_time)[0]
        self.assertNotEqual(task.id, task_1_id)
        self.assertTrue(task.id.startswith(HEALTH_TASK_ID_PREFIX))

    def test_handle_failed_health_task_bad_daemon(self):
        """Tests handling a failed health task where the Docker daemon is bad"""

        when = now()
        node = Node(self.node_agent, self.node, self.scheduler)
        node._initial_cleanup_completed()
        node._image_pull_completed()
        node._update_state()
        # Get health task
        task = node.get_next_tasks(when)[0]
        self.assertTrue(task.id.startswith(HEALTH_TASK_ID_PREFIX))

        # Fail task with bad daemon exit code
        self.task_mgr.launch_tasks([task], now())
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.RUNNING, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.FAILED, now(),
                                                          exit_code=HealthTask.BAD_DAEMON_CODE)
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)

        # Check node state
        self.assertEqual(node._state, Node.DEGRADED)
        self.assertTrue(NodeConditions.BAD_DAEMON_ERR.name in node._conditions._active_errors)

    def test_handle_failed_health_task_bad_logstash(self):
        """Tests handling a failed health task where logstash is unreachable"""

        when = now()
        node = Node(self.node_agent, self.node, self.scheduler)
        node._initial_cleanup_completed()
        node._image_pull_completed()
        node._update_state()
        # Get health task
        task = node.get_next_tasks(when)[0]
        self.assertTrue(task.id.startswith(HEALTH_TASK_ID_PREFIX))

        # Fail task with bad logstash exit code
        self.task_mgr.launch_tasks([task], now())
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.RUNNING, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.FAILED, now(),
                                                          exit_code=HealthTask.BAD_LOGSTASH_CODE)
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)

        # Check node state
        self.assertEqual(node._state, Node.DEGRADED)
        self.assertTrue(NodeConditions.BAD_LOGSTASH_ERR.name in node._conditions._active_errors)

    def test_handle_failed_health_task_low_docker_space(self):
        """Tests handling a failed health task where Docker has low disk space"""

        when = now()
        node = Node(self.node_agent, self.node, self.scheduler)
        node._initial_cleanup_completed()
        node._image_pull_completed()
        node._update_state()
        # Get health task
        task = node.get_next_tasks(when)[0]
        self.assertTrue(task.id.startswith(HEALTH_TASK_ID_PREFIX))

        # Fail task with low Docker space exit code
        self.task_mgr.launch_tasks([task], now())
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.RUNNING, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.FAILED, now(),
                                                          exit_code=HealthTask.LOW_DOCKER_SPACE_CODE)
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)

        # Check node state
        self.assertEqual(node._state, Node.DEGRADED)
        self.assertTrue(NodeConditions.LOW_DOCKER_SPACE_ERR.name in node._conditions._active_errors)

    def test_handle_successful_health_task(self):
        """Tests handling the health task successfully"""

        when = now()
        node = Node(self.node_agent, self.node, self.scheduler)
        node._initial_cleanup_completed()
        node._image_pull_completed()
        node._update_state()

        # Get health task
        task = node.get_next_tasks(when)[0]
        self.assertTrue(task.id.startswith(HEALTH_TASK_ID_PREFIX))
        self.assertEqual(task.agent_id, self.node_agent)

        # Schedule health task and make sure no new task is ready
        self.task_mgr.launch_tasks([task], now())
        self.assertListEqual([], node.get_next_tasks(when))
        self.assertTrue(node._conditions.is_health_check_normal)

        # Complete pull task, verify no new task
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.RUNNING, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.FINISHED, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)
        self.assertListEqual([], node.get_next_tasks(when))
        self.assertTrue(node._conditions.is_health_check_normal)

    def test_handle_killed_health_task(self):
        """Tests handling killed health task"""

        when = now()
        node = Node(self.node_agent, self.node, self.scheduler)
        node._initial_cleanup_completed()
        node._image_pull_completed()
        node._update_state()
        # Get pull task
        task = node.get_next_tasks(when)[0]
        self.assertTrue(task.id.startswith(HEALTH_TASK_ID_PREFIX))
        task_1_id = task.id

        # Kill task after running and get different task next time
        self.task_mgr.launch_tasks([task], now())
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.RUNNING, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.KILLED, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)
        task = node.get_next_tasks(when)[0]
        self.assertTrue(task.id.startswith(HEALTH_TASK_ID_PREFIX))
        self.assertNotEqual(task.id, task_1_id)
        self.assertTrue(node._conditions.is_health_check_normal)

    def test_handle_lost_health_task(self):
        """Tests handling lost health task"""

        when = now()
        node = Node(self.node_agent, self.node, self.scheduler)
        node._initial_cleanup_completed()
        node._image_pull_completed()
        node._update_state()
        # Get pull task
        task = node.get_next_tasks(when)[0]
        self.assertTrue(task.id.startswith(HEALTH_TASK_ID_PREFIX))
        task_1_id = task.id
        self.assertIsNotNone(task)

        # Lose task without scheduling and get different task next time
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.LOST, now())
        node.handle_task_update(update)
        task = node.get_next_tasks(when)[0]
        self.assertTrue(task.id.startswith(HEALTH_TASK_ID_PREFIX))
        self.assertNotEqual(task.id, task_1_id)
        self.assertTrue(node._conditions.is_health_check_normal)

        # Lose task with scheduling and get different task next time
        self.task_mgr.launch_tasks([task], now())
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.LOST, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)
        task = node.get_next_tasks(when)[0]
        self.assertTrue(task.id.startswith(HEALTH_TASK_ID_PREFIX))
        self.assertNotEqual(task.id, task_1_id)
        self.assertTrue(node._conditions.is_health_check_normal)

        # Lose task after running and get different task next time
        self.task_mgr.launch_tasks([task], now())
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.RUNNING, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.LOST, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)
        task = node.get_next_tasks(when)[0]
        self.assertTrue(task.id.startswith(HEALTH_TASK_ID_PREFIX))
        self.assertNotEqual(task.id, task_1_id)
        self.assertTrue(node._conditions.is_health_check_normal)

    def test_handle_failed_pull_task(self):
        """Tests handling failed Docker pull task"""

        when = now()
        node = Node(self.node_agent, self.node, self.scheduler)
        node._last_heath_task = when
        node._initial_cleanup_completed()
        node._update_state()
        # Get Docker pull task
        task = node.get_next_tasks(when)[0]
        task_1_id = task.id
        self.assertTrue(task.id.startswith(PULL_TASK_ID_PREFIX))

        # Fail task after running
        self.task_mgr.launch_tasks([task], now())
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.RUNNING, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.FAILED, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)

        # No new pull task right away
        tasks = node.get_next_tasks(when + datetime.timedelta(seconds=5))
        self.assertListEqual([], tasks)
        self.assertFalse(node._is_image_pulled)

        # After error threshold, we should get new pull task
        new_time = when + Node.IMAGE_PULL_ERR_THRESHOLD + datetime.timedelta(seconds=5)
        node._last_heath_task = new_time  # Get rid of health check task
        task = node.get_next_tasks(new_time)[0]
        self.assertNotEqual(task.id, task_1_id)
        self.assertTrue(task.id.startswith(PULL_TASK_ID_PREFIX))

    def test_handle_successful_pull_task(self):
        """Tests handling the Docker pull task successfully"""

        when = now()
        node = Node(self.node_agent, self.node, self.scheduler)
        node._last_heath_task = when
        node._initial_cleanup_completed()
        node._update_state()

        # Get Docker pull task
        task = node.get_next_tasks(when)[0]
        self.assertTrue(task.id.startswith(PULL_TASK_ID_PREFIX))
        self.assertEqual(task.agent_id, self.node_agent)

        # Schedule pull task and make sure no new task is ready
        self.task_mgr.launch_tasks([task], now())
        self.assertListEqual([], node.get_next_tasks(when))
        self.assertFalse(node._is_image_pulled)

        # Complete pull task, verify no new task
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.RUNNING, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.FINISHED, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)
        self.assertListEqual([], node.get_next_tasks(when))
        self.assertTrue(node._is_image_pulled)
        # Node should now be ready
        self.assertEqual(node._state, Node.READY)

    def test_handle_killed_pull_task(self):
        """Tests handling killed cleanup task"""

        when = now()
        node = Node(self.node_agent, self.node, self.scheduler)
        node._last_heath_task = when
        node._initial_cleanup_completed()
        node._update_state()
        # Get pull task
        task = node.get_next_tasks(when)[0]
        self.assertTrue(task.id.startswith(PULL_TASK_ID_PREFIX))
        task_1_id = task.id

        # Kill task after running and get different task next time
        self.task_mgr.launch_tasks([task], now())
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.RUNNING, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.KILLED, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)
        task = node.get_next_tasks(when)[0]
        self.assertTrue(task.id.startswith(PULL_TASK_ID_PREFIX))
        self.assertNotEqual(task.id, task_1_id)
        self.assertFalse(node._is_image_pulled)

    def test_handle_lost_pull_task(self):
        """Tests handling lost pull task"""

        when = now()
        node = Node(self.node_agent, self.node, self.scheduler)
        node._last_heath_task = when
        node._initial_cleanup_completed()
        node._update_state()
        # Get pull task
        task = node.get_next_tasks(when)[0]
        self.assertTrue(task.id.startswith(PULL_TASK_ID_PREFIX))
        task_1_id = task.id
        self.assertIsNotNone(task)

        # Lose task without scheduling and get different task next time
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.LOST, now())
        node.handle_task_update(update)
        task = node.get_next_tasks(when)[0]
        self.assertTrue(task.id.startswith(PULL_TASK_ID_PREFIX))
        self.assertNotEqual(task.id, task_1_id)
        self.assertFalse(node._is_image_pulled)

        # Lose task with scheduling and get different task next time
        self.task_mgr.launch_tasks([task], now())
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.LOST, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)
        task = node.get_next_tasks(when)[0]
        self.assertTrue(task.id.startswith(PULL_TASK_ID_PREFIX))
        self.assertNotEqual(task.id, task_1_id)
        self.assertFalse(node._is_image_pulled)

        # Lose task after running and get different task next time
        self.task_mgr.launch_tasks([task], now())
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.RUNNING, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.LOST, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)
        task = node.get_next_tasks(when)[0]
        self.assertTrue(task.id.startswith(PULL_TASK_ID_PREFIX))
        self.assertNotEqual(task.id, task_1_id)
        self.assertFalse(node._is_image_pulled)

    def test_paused_node_pull_task(self):
        """Tests not returning pull task when its node is paused"""

        when = now()
        paused_node = node_test_utils.create_node(hostname='host_1_paused', slave_id='agent_paused')
        paused_node.is_paused = True
        node = Node('agent_paused', paused_node, self.scheduler)
        node._last_heath_task = when
        node._initial_cleanup_completed()
        node._update_state()
        tasks = node.get_next_tasks(when)
        # No task due to paused node
        self.assertListEqual([], tasks)

    def test_node_that_is_not_cleaned_yet_no_pull_task(self):
        """Tests not returning pull task when the node hasn't been cleaned up yet"""

        when = now()
        node = Node(self.node_agent, self.node, self.scheduler)
        tasks = node.get_next_tasks(when)
        # No pull task due to node not cleaned yet
        for task in tasks:
            self.assertFalse(task.id.startswith(PULL_TASK_ID_PREFIX))
