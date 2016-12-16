from __future__ import unicode_literals

import django
from django.test import TestCase

from job.configuration.interface.exceptions import InvalidInterfaceDefinition
from job.configuration.interface.job_type_configuration import JobTypeConfiguration


class TestJobTypeConfiguration(TestCase):

    def setUp(self):
        django.setup()

    def test_init_validation(self):
        """Tests the validation done in __init__"""

        # Try minimal acceptable configuration
        JobTypeConfiguration()

        # Missing name
        config = {'version': '1.0',
                  'default_settings': {
                      '': 'val1',
                      'name2': 'val2'
                  }}

        self.assertRaises(InvalidInterfaceDefinition, JobTypeConfiguration, config)

        # Missing value
        config = {'version': '1.0',
                  'default_settings': {
                      'name1': '',
                      'name2': 'val2'
                  }}

        self.assertRaises(InvalidInterfaceDefinition, JobTypeConfiguration, config)

        # Wrong version
        config = {'version': '0.9',
                  'default_settings': {
                      'name1': 'val1',
                      'name2': 'val2'
                  }}
        self.assertRaises(InvalidInterfaceDefinition, JobTypeConfiguration, config)
