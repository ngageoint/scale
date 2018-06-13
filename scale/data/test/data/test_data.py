from __future__ import unicode_literals

import django

from django.test.testcases import TestCase
from mock import MagicMock

from data.data.data import Data
from data.data.exceptions import InvalidData
from data.data.value import FileValue, JsonValue
from data.interface.interface import Interface
from data.interface.parameter import FileParameter, JsonParameter


class TestData(TestCase):
    """Tests related to the Data class"""

    def setUp(self):
        django.setup()

    def test_add_value(self):
        """Tests calling Data.add_value()"""

        data = Data()

        file_value = FileValue('input_1', [123])
        data.add_value(file_value)

        json_value = JsonValue('input_2', {'foo': 'bar'})
        data.add_value(json_value)

        self.assertSetEqual(set(data.values.keys()), {'input_1', 'input_2'})

        # Duplicate value
        dup_value = FileValue('input_1', [123])
        with self.assertRaises(InvalidData) as context:
            data.add_value(dup_value)
        self.assertEqual(context.exception.error.name, 'DUPLICATE_VALUE')

    def test_validate(self):
        """Tests calling Data.validate()"""

        interface = Interface()
        data = Data()

        interface.add_parameter(FileParameter('input_1', ['application/json']))
        interface.add_parameter(JsonParameter('input_2', 'integer'))
        data.add_value(FileValue('input_1', [123]))
        data.add_value(JsonValue('input_2', 100))
        data.add_value(JsonValue('extra_input_1', 'hello'))
        data.add_value(JsonValue('extra_input_2', 'there'))

        # Valid data
        data.validate(interface)
        # Ensure extra data values are removed
        self.assertSetEqual(set(data.values.keys()), {'input_1', 'input_2'})

        # Data is missing required input 3
        interface.add_parameter(FileParameter('input_3', ['image/gif'], required=True))
        with self.assertRaises(InvalidData) as context:
            data.validate(interface)
        self.assertEqual(context.exception.error.name, 'PARAM_REQUIRED')

        data.add_value(FileValue('input_3', [999]))  # Input 3 taken care of now

        # Invalid data
        interface.add_parameter(JsonParameter('input_4', 'string'))
        mock_value = MagicMock()
        mock_value.name = 'input_4'
        mock_value.validate.side_effect = InvalidData('MOCK', '')
        data.add_value(mock_value)
        with self.assertRaises(InvalidData) as context:
            data.validate(interface)
        self.assertEqual(context.exception.error.name, 'MOCK')
