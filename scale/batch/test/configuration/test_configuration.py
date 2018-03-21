from __future__ import unicode_literals

import django
from django.test import TestCase

from batch.configuration.json.configuration_v6 import BatchConfigurationV6
from batch.test import utils as batch_test_utils


class TestBatchDefinition(TestCase):

    def setUp(self):
        django.setup()

    def test_create_from_json(self):
        """Tests creating a BatchConfiguration from a JSON"""

        # Valid batch configuration
        json_dict = {'version': '6', 'priority': 201}
        json = BatchConfigurationV6(configuration=json_dict, do_validate=True)
        config = json.get_configuration()
        self.assertEqual(config.priority, 201)

    def test_validate(self):
        """Tests calling BatchConfiguration.validate()"""

        batch = batch_test_utils.create_batch()

        # Valid configuration
        json_dict = {'version': '6', 'priority': 202}
        json = BatchConfigurationV6(configuration=json_dict)
        configuration = json.get_configuration()
        configuration.validate(batch)
