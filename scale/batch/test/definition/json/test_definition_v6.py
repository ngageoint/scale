from __future__ import unicode_literals

import django
from django.test import TestCase

from batch.definition.definition import BatchDefinition
from batch.definition.exceptions import InvalidDefinition
from batch.definition.json.definition_v6 import convert_definition_to_v6, BatchDefinitionV6


class TestBatchDefinitionV6(TestCase):

    def setUp(self):
        django.setup()

    def test_get_v6_definition_json(self):
        """Tests calling get_v6_definition_json()"""

        # Try definition with nothing set
        definition = BatchDefinition()
        json = convert_definition_to_v6(definition)
        BatchDefinitionV6(definition=json.get_dict(), do_validate=True)  # Revalidate

        # Try definition with previous batch ID set
        definition = BatchDefinition()
        definition.prev_batch_id = 1234
        json = convert_definition_to_v6(definition)
        BatchDefinitionV6(definition=json.get_dict(), do_validate=True)  # Revalidate
        self.assertEqual(json.get_definition().prev_batch_id, definition.prev_batch_id)

    def test_init_validation(self):
        """Tests the validation done in __init__"""

        # Try minimal acceptable configuration
        BatchDefinitionV6(do_validate=True)

        # Invalid version
        definition = {'version': 'BAD'}
        self.assertRaises(InvalidDefinition, BatchDefinitionV6, definition, True)

        # Missing batch_id
        definition = {'version': '6', 'previous_batch': {'all_jobs': True}}
        self.assertRaises(InvalidDefinition, BatchDefinitionV6, definition, True)

        # Valid previous batch definition
        definition = {'version': '6', 'previous_batch': {'batch_id': 1234, 'job_names': ['job_a', 'job_b'],
                                                         'all_jobs': True}}
        BatchDefinitionV6(definition=definition, do_validate=True)
