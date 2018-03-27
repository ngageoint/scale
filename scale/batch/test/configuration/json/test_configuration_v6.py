from __future__ import unicode_literals

import django
from django.test import TestCase

from batch.configuration.configuration import BatchConfiguration
from batch.configuration.exceptions import InvalidConfiguration
from batch.configuration.json.configuration_v6 import convert_configuration_to_v6, BatchConfigurationV6


class TestBatchConfigurationV6(TestCase):

    def setUp(self):
        django.setup()

    def test_get_v6_configuration_json(self):
        """Tests calling get_v6_configuration_json()"""

        # Try configuration with nothing set
        configuration = BatchConfiguration()
        json = convert_configuration_to_v6(configuration)
        BatchConfigurationV6(configuration=json.get_dict(), do_validate=True)  # Revalidate

        # Try configuration with priority set
        configuration = BatchConfiguration()
        configuration.priority = 100
        json = convert_configuration_to_v6(configuration)
        BatchConfigurationV6(configuration=json.get_dict(), do_validate=True)  # Revalidate
        self.assertEqual(json.get_configuration().priority, configuration.priority)

    def test_init_validation(self):
        """Tests the validation done in __init__"""

        # Try minimal acceptable configuration
        BatchConfigurationV6(do_validate=True)

        # Invalid version
        json_dict = {'version': 'BAD'}
        self.assertRaises(InvalidConfiguration, BatchConfigurationV6, json_dict, True)

        # Valid priority
        json_dict = {'version': '6', 'priority': 500}
        BatchConfigurationV6(configuration=json_dict, do_validate=True)
