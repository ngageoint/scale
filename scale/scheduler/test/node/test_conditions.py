from __future__ import unicode_literals

import datetime

import django
from django.test import TestCase
from django.utils.timezone import now
from mock import patch

from job.test import utils as job_test_utils
from job.tasks.health_task import HealthTask
from scheduler.node.conditions import NodeConditions, NodeWarning, CLEANUP_WARN_THRESHOLD, WARNING_NAME_COUNTER
from util.parse import datetime_to_string

class TestNodeConditions(TestCase):

    def setUp(self):
        django.setup()

        self.conditions = NodeConditions('test_node')
        self.job_exes = [job_test_utils.create_running_job_exe()]
        self.job_ids = [exe.job_id for exe in self.job_exes]

    @patch('scheduler.node.conditions.now')
    def test_generate_status_json(self, mock_now):
        """Tests calling generate_status_json() successfully"""

        right_now = now()
        mock_now.return_value = right_now

        self.conditions._error_active(NodeConditions.BAD_DAEMON_ERR)
        self.conditions._error_active(NodeConditions.BAD_LOGSTASH_ERR)
        self.conditions._error_active(NodeConditions.CLEANUP_ERR)
        self.conditions._error_active(NodeConditions.HEALTH_FAIL_ERR)
        self.conditions._error_active(NodeConditions.HEALTH_TIMEOUT_ERR)
        self.conditions._error_active(NodeConditions.IMAGE_PULL_ERR)
        self.conditions._error_active(NodeConditions.LOW_DOCKER_SPACE_ERR)

        self.conditions._warning_active(NodeConditions.CLEANUP_FAILURE, NodeConditions.CLEANUP_FAILURE.description % [1,2,3])
        self.conditions._warning_active(NodeConditions.CLEANUP_TIMEOUT, NodeConditions.CLEANUP_TIMEOUT.description % [1,2,3])
        self.conditions._warning_active(NodeConditions.SLOW_CLEANUP, NodeConditions.SLOW_CLEANUP.description % 1)
        self.maxDiff = None

        node_dict = {}
        self.conditions.generate_status_json(node_dict)

        expected_results = {
                             'errors': [{'name': 'BAD_DAEMON', 'title': NodeConditions.BAD_DAEMON_ERR.title,
                                         'description': NodeConditions.BAD_DAEMON_ERR.description,
                                         'started': datetime_to_string(right_now),
                                         'last_updated': datetime_to_string(right_now)},
                                        {'name': 'BAD_LOGSTASH', 'title': NodeConditions.BAD_LOGSTASH_ERR.title,
                                         'description': NodeConditions.BAD_LOGSTASH_ERR.description,
                                         'started': datetime_to_string(right_now),
                                         'last_updated': datetime_to_string(right_now)},
                                        {'name': 'CLEANUP', 'title': NodeConditions.CLEANUP_ERR.title,
                                         'description': NodeConditions.CLEANUP_ERR.description,
                                         'started': datetime_to_string(right_now),
                                         'last_updated': datetime_to_string(right_now)},
                                        {'name': 'HEALTH_FAIL', 'title': NodeConditions.HEALTH_FAIL_ERR.title,
                                         'description': NodeConditions.HEALTH_FAIL_ERR.description,
                                         'started': datetime_to_string(right_now),
                                         'last_updated': datetime_to_string(right_now)},
                                        {'name': 'HEALTH_TIMEOUT', 'title': NodeConditions.HEALTH_TIMEOUT_ERR.title,
                                         'description': NodeConditions.HEALTH_TIMEOUT_ERR.description,
                                         'started': datetime_to_string(right_now),
                                         'last_updated': datetime_to_string(right_now)},
                                        {'name': 'IMAGE_PULL', 'title': NodeConditions.IMAGE_PULL_ERR.title,
                                         'description': NodeConditions.IMAGE_PULL_ERR.description,
                                         'started': datetime_to_string(right_now),
                                         'last_updated': datetime_to_string(right_now)},
                                        {'name': 'LOW_DOCKER_SPACE', 'title': NodeConditions.LOW_DOCKER_SPACE_ERR.title,
                                         'description': NodeConditions.LOW_DOCKER_SPACE_ERR.description,
                                         'started': datetime_to_string(right_now),
                                         'last_updated': datetime_to_string(right_now)}
                                        ],
                             'warnings': [{'name': 'CLEANUP_FAILURE', 'title': NodeConditions.CLEANUP_FAILURE.title,
                                           'description': NodeConditions.CLEANUP_FAILURE.description % [1,2,3],
                                           'started': datetime_to_string(right_now),
                                           'last_updated': datetime_to_string(right_now)},
                                          {'name': 'CLEANUP_TIMEOUT', 'title': NodeConditions.CLEANUP_TIMEOUT.title,
                                           'description': NodeConditions.CLEANUP_TIMEOUT.description % [1,2,3],
                                           'started': datetime_to_string(right_now),
                                           'last_updated': datetime_to_string(right_now)},
                                          {'name': 'SLOW_CLEANUP', 'title': NodeConditions.SLOW_CLEANUP.title,
                                           'description': NodeConditions.SLOW_CLEANUP.description % 1,
                                           'started': datetime_to_string(right_now),
                                           'last_updated': datetime_to_string(right_now)}
                                          ]}

        self.assertCountEqual(node_dict['errors'], expected_results['errors'])
        self.assertCountEqual(node_dict['warnings'], expected_results['warnings'])
        self.assertItemsEqual(node_dict['errors'], expected_results['errors'])
        self.assertItemsEqual(node_dict['warnings'], expected_results['warnings'])

    @patch('scheduler.node.conditions.now')
    def test_handle_cleanup_task_completed(self, mock_now):
        """Tests calling handle_cleanup_task_completed"""

        right_now = now()
        then = right_now - CLEANUP_WARN_THRESHOLD
        mock_now.return_value = right_now

        self.conditions._error_active(NodeConditions.CLEANUP_ERR)
        self.conditions._warning_active(NodeConditions.CLEANUP_FAILURE,
                                        NodeConditions.CLEANUP_FAILURE.description % [1, 2, 3])
        self.conditions._warning_active(NodeWarning(name='old-warning', title='old', description=None))
        self.conditions._active_warnings['old-warning'].last_updated = then

        node_dict = {}
        self.conditions.generate_status_json(node_dict)
        self.maxDiff = None

        expected_results = {
                             'errors': [{'name': 'CLEANUP', 'title': NodeConditions.CLEANUP_ERR.title,
                                         'description': NodeConditions.CLEANUP_ERR.description,
                                         'started': datetime_to_string(right_now),
                                         'last_updated': datetime_to_string(right_now)}
                                        ],
                             'warnings': [{'name': 'CLEANUP_FAILURE', 'title': NodeConditions.CLEANUP_FAILURE.title,
                                           'description': NodeConditions.CLEANUP_FAILURE.description % [1,2,3],
                                           'started': datetime_to_string(right_now),
                                           'last_updated': datetime_to_string(right_now)},
                                          {'name': 'old-warning', 'title': 'old',
                                           'description': None,
                                           'started': datetime_to_string(right_now),
                                           'last_updated': datetime_to_string(then)}
                                          ]}

        self.assertItemsEqual(node_dict['errors'], expected_results['errors'])
        self.assertItemsEqual(node_dict['warnings'], expected_results['warnings'])

        self.conditions.handle_cleanup_task_completed()
        node_dict = {}
        self.conditions.generate_status_json(node_dict)

        expected_results = {
                             'errors': [],
                             'warnings': [{'name': 'CLEANUP_FAILURE', 'title': NodeConditions.CLEANUP_FAILURE.title,
                                           'description': NodeConditions.CLEANUP_FAILURE.description % [1,2,3],
                                           'started': datetime_to_string(right_now),
                                           'last_updated': datetime_to_string(right_now)}
                                          ]}

        self.assertDictEqual(node_dict, expected_results)

        @patch('scheduler.node.conditions.now')
        def test_handle_cleanup_task_failed(self, mock_now):
            """Tests calling handle_cleanup_task_failed"""

            right_now = now()

            expected_results = {
                'errors': [{'name': 'CLEANUP', 'title': NodeConditions.CLEANUP_ERR.title,
                            'description': NodeConditions.CLEANUP_ERR.description,
                            'started': datetime_to_string(right_now),
                            'last_updated': datetime_to_string(right_now)}
                            ],
                'warnings': [{'name': 'CLEANUP_FAILURE' + ' %d' % WARNING_NAME_COUNTER,
                              'title': NodeConditions.CLEANUP_FAILURE.title,
                              'description': NodeConditions.CLEANUP_FAILURE.description % self.job_ids,
                              'started': datetime_to_string(right_now),
                              'last_updated': datetime_to_string(right_now)}
                             ]}

            self.conditions.handle_cleanup_task_failed(self.job_exes)
            node_dict = {}
            self.conditions.generate_status_json(node_dict)

            self.assertDictEqual(node_dict, expected_results)

        @patch('scheduler.node.conditions.now')
        def test_handle_cleanup_task_timeout(self, mock_now):
            """Tests calling handle_cleanup_task_timeout"""

            right_now = now()

            expected_results = {
                'errors': [{'name': 'CLEANUP', 'title': NodeConditions.CLEANUP_ERR.title,
                            'description': NodeConditions.CLEANUP_ERR.description,
                            'started': datetime_to_string(right_now),
                            'last_updated': datetime_to_string(right_now)}
                            ],
                'warnings': [{'name': 'CLEANUP_TIMEOUT' + ' %d' % WARNING_NAME_COUNTER,
                              'title': NodeConditions.CLEANUP_TIMEOUT.title,
                              'description': NodeConditions.CLEANUP_TIMEOUT.description % self.job_ids,
                              'started': datetime_to_string(right_now),
                              'last_updated': datetime_to_string(right_now)}
                             ]}

            self.conditions.handle_cleanup_task_timeout(self.job_exes)
            node_dict = {}
            self.conditions.generate_status_json(node_dict)

            self.assertDictEqual(node_dict, expected_results)

        @patch('scheduler.node.conditions.now')
        def test_handle_health_task_completed(self, mock_now):
            """Tests calling handle_health_task_completed"""

            right_now = now()

            self.conditions._error_active(NodeConditions.BAD_DAEMON_ERR)
            self.conditions._error_active(NodeConditions.BAD_LOGSTASH_ERR)
            self.conditions._error_active(NodeConditions.CLEANUP_ERR)
            self.conditions._error_active(NodeConditions.HEALTH_FAIL_ERR)
            self.conditions._error_active(NodeConditions.HEALTH_TIMEOUT_ERR)
            self.conditions._error_active(NodeConditions.IMAGE_PULL_ERR)
            self.conditions._error_active(NodeConditions.LOW_DOCKER_SPACE_ERR)

            expected_results = {
                'errors': [{'name': 'CLEANUP', 'title': NodeConditions.CLEANUP_ERR.title,
                            'description': NodeConditions.CLEANUP_ERR.description,
                            'started': datetime_to_string(right_now),
                            'last_updated': datetime_to_string(right_now)},
                           {'name': 'IMAGE_PULL', 'title': NodeConditions.IMAGE_PULL_ERR.title,
                            'description': NodeConditions.IMAGE_PULL_ERR.description,
                            'started': datetime_to_string(right_now),
                            'last_updated': datetime_to_string(right_now)}
                           ],
                'warnings': []}

            self.conditions.handle_health_task_completed()
            node_dict = {}
            self.conditions.generate_status_json(node_dict)

            self.assertItemsEqual(node_dict['errors'], expected_results['errors'])
            self.assertTrue(self.conditions.is_health_check_normal)
            self.assertTrue(self.conditions.is_pull_bad)

        @patch('scheduler.node.conditions.now')
        def test_handle_health_task_failed(self, mock_now):
            """Tests calling handle_health_task_failed"""

            right_now = now()

            self.conditions._error_active(NodeConditions.BAD_DAEMON_ERR)
            self.conditions._error_active(NodeConditions.BAD_LOGSTASH_ERR)
            self.conditions._error_active(NodeConditions.HEALTH_FAIL_ERR)
            self.conditions._error_active(NodeConditions.HEALTH_TIMEOUT_ERR)
            self.conditions._error_active(NodeConditions.LOW_DOCKER_SPACE_ERR)
            self.conditions.is_health_check_normal = True

            expected_results = {
                'errors': [{'name': 'BAD_DAEMON', 'title': NodeConditions.BAD_DAEMON_ERR.title,
                            'description': NodeConditions.BAD_DAEMON_ERR.description,
                            'started': datetime_to_string(right_now),
                            'last_updated': datetime_to_string(right_now)}
                           ],
                'warnings': []}

            bad_daemon = job_test_utils.create_task_status_update(task_id='id',agent_id='agent',status='status',
                                                     when=right_now, exit_code=HealthTask.BAD_DAEMON_CODE)
            self.conditions.handle_health_task_failed(bad_daemon)

            node_dict = {}
            self.conditions.generate_status_json(node_dict)

            self.assertItemsEqual(node_dict['errors'], expected_results['errors'])
            self.assertFalse(self.conditions.is_health_check_normal)

            expected_results = {
                'errors': [{'name': 'BAD_LOGSTASH', 'title': NodeConditions.BAD_LOGSTASH_ERR.title,
                            'description': NodeConditions.BAD_LOGSTASH_ERR.description,
                            'started': datetime_to_string(right_now),
                            'last_updated': datetime_to_string(right_now)}
                           ],
                'warnings': []}

            bad_log = job_test_utils.create_task_status_update(task_id='id', agent_id='agent', status='status',
                                                                  when=right_now, exit_code=HealthTask.BAD_LOGSTASH_CODE)
            self.conditions.handle_health_task_failed(bad_log)

            node_dict = {}
            self.conditions.generate_status_json(node_dict)

            self.assertItemsEqual(node_dict['errors'], expected_results['errors'])
            self.assertFalse(self.conditions.is_health_check_normal)

            expected_results = {
                'errors': [{'name': 'LOW_DOCKER_SPACE', 'title': NodeConditions.LOW_DOCKER_SPACE_ERR.title,
                            'description': NodeConditions.LOW_DOCKER_SPACE_ERR.description,
                            'started': datetime_to_string(right_now),
                            'last_updated': datetime_to_string(right_now)}
                           ],
                'warnings': []}

            low_docker = job_test_utils.create_task_status_update(task_id='id', agent_id='agent', status='status',
                                                                  when=right_now, exit_code=HealthTask.LOW_DOCKER_SPACE_CODE)
            self.conditions.handle_health_task_failed(low_docker)

            node_dict = {}
            self.conditions.generate_status_json(node_dict)

            self.assertItemsEqual(node_dict['errors'], expected_results['errors'])
            self.assertFalse(self.conditions.is_health_check_normal)

            expected_results = {
                'errors': [{'name': 'HEALTH_FAIL', 'title': NodeConditions.HEALTH_FAIL_ERR.title,
                            'description': NodeConditions.HEALTH_FAIL_ERR.description,
                            'started': datetime_to_string(right_now),
                            'last_updated': datetime_to_string(right_now)}
                           ],
                'warnings': []}

            unknown = job_test_utils.create_task_status_update(task_id='id', agent_id='agent', status='status',
                                                                  when=right_now, exit_code=0)
            self.conditions.handle_health_task_failed(unknown)

            node_dict = {}
            self.conditions.generate_status_json(node_dict)

            self.assertItemsEqual(node_dict['errors'], expected_results['errors'])
            self.assertFalse(self.conditions.is_health_check_normal)

        @patch('scheduler.node.conditions.now')
        def test_handle_health_task_timeout(self, mock_now):
            """Tests calling handle_health_task_timeout"""

            right_now = now()
            self.conditions._error_active(NodeConditions.BAD_DAEMON_ERR)
            self.conditions._error_active(NodeConditions.BAD_LOGSTASH_ERR)
            self.conditions._error_active(NodeConditions.HEALTH_FAIL_ERR)
            self.conditions._error_active(NodeConditions.HEALTH_TIMEOUT_ERR)
            self.conditions._error_active(NodeConditions.LOW_DOCKER_SPACE_ERR)
            self.conditions.is_health_check_normal = True

            self.conditions.handle_health_task_timeout()

            expected_results = {
                'errors': [{'name': 'HEALTH_TIMEOUT', 'title': NodeConditions.HEALTH_TIMEOUT_ERR.title,
                            'description': NodeConditions.HEALTH_TIMEOUT_ERR.description,
                            'started': datetime_to_string(right_now),
                            'last_updated': datetime_to_string(right_now)}
                           ],
                'warnings': []}
            node_dict = {}
            self.conditions.generate_status_json(node_dict)

            self.assertItemsEqual(node_dict['errors'], expected_results['errors'])
            self.assertFalse(self.conditions.is_health_check_normal)
