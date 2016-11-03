from __future__ import unicode_literals

import django
from django.test import TestCase
from mock import patch

from job.configuration.configuration.exceptions import InvalidJobConfiguration
from job.configuration.configuration.job_configuration import JobConfiguration


class TestJobConfiguration(TestCase):

    def setUp(self):
        django.setup()

    def test_init_validation(self):
        """Tests the validation done in __init__"""

        # Try minimal acceptable configuration
        JobConfiguration()

        # Duplicate workspace name in pre-task
        config = {'pre_task': {'workspaces': [{'name': 'name1', 'mode': 'ro'}, {'name': 'name1', 'mode': 'ro'}]},
                  'job_task': {'workspaces': []}}
        self.assertRaises(InvalidJobConfiguration, JobConfiguration, config)

        # Duplicate workspace name in job-task
        config = {'job_task': {'workspaces': [{'name': 'name1', 'mode': 'ro'}, {'name': 'name1', 'mode': 'ro'}]}}
        self.assertRaises(InvalidJobConfiguration, JobConfiguration, config)

        # Duplicate workspace name in post-task
        config = {'post_task': {'workspaces': [{'name': 'name1', 'mode': 'ro'}, {'name': 'name1', 'mode': 'ro'}]},
                  'job_task': {'workspaces': []}}
        self.assertRaises(InvalidJobConfiguration, JobConfiguration, config)


class TestJobConfigurationConvert(TestCase):
    """Tests performing conversion from lower to higher minor versions of configuration schema."""

    def setUp(self):
        self.job_configuration_dict = {
            'version': '1.0',
            'job_task': {
                'workspaces': [{
                    'name': 'name1',
                    'mode': 'ro'
                    }]
                }
            }

        django.setup()

    @patch('job.configuration.configuration.job_configuration_1_0.JobConfiguration.get_dict')
    def test_successful(self, mock_get_dict):
        """Tests calling JobConfiguration.update() successfully."""
        mock_get_dict.return_value = self.job_configuration_dict
        job_configuration = JobConfiguration.convert_configuration(self.job_configuration_dict)
        self.assertEqual(job_configuration['version'], '1.1')
        self.assertFalse(job_configuration['job_task']['settings'])
