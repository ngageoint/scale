from __future__ import unicode_literals

import datetime

import django
from django.test import TestCase
from django.utils.timezone import now
from mock import patch

from job.test import utils as job_test_utils
from scheduler.node.conditions import NodeConditions
from util.parse import datetime_to_string

class TestNodeConditions(TestCase):

    def setUp(self):
        django.setup()

        self.conditions = NodeConditions('test_node')
        self.job_exes = [job_test_utils.create_running_job_exe()]

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
        print node_dict

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

        self.assertListEqual(node_dict['errors'], expected_results['errors'])
        self.assertListEqual(node_dict['warnings'], expected_results['warnings'])
