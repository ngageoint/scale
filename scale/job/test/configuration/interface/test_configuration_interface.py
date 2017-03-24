from __future__ import unicode_literals

import django
from django.test import TestCase

from job.configuration.exceptions import InvalidJobConfiguration
from job.configuration.json.job.job_config import JobConfiguration


class TestJobConfiguration(TestCase):

    def setUp(self):
        django.setup()

    def test_init_validation(self):
        """Tests the validation done in __init__"""

        # Try minimal acceptable configuration
        JobConfiguration()

        # Missing name
        config = {'version': '1.0',
                  'default_settings': {
                      '': 'val1',
                      'name2': 'val2'
                  }}

        self.assertRaises(InvalidJobConfiguration, JobConfiguration, config)

        # Missing value
        config = {'version': '1.0',
                  'default_settings': {
                      'name1': '',
                      'name2': 'val2'
                  }}

        self.assertRaises(InvalidJobConfiguration, JobConfiguration, config)

        # Wrong version
        config = {'version': '0.9',
                  'default_settings': {
                      'name1': 'val1',
                      'name2': 'val2'
                  }}
        self.assertRaises(InvalidJobConfiguration, JobConfiguration, config)

        # Invalid value (int)
        config = {'version': '1.0',
                  'default_settings': {
                      'name1': 1234
                  }}
        self.assertRaises(InvalidJobConfiguration, JobConfiguration, config)
