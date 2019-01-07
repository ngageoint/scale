from __future__ import unicode_literals

import django

from django.test.testcases import TestCase
from mock import MagicMock

from data.data.data import Data
from data.data.exceptions import InvalidData
from data.data.value import FileValue, JsonValue
from data.interface.interface import Interface
from data.interface.parameter import FileParameter, JsonParameter


class TestDataFilter(TestCase):
    """Tests related to the DataFilter class"""

    def setUp(self):
        django.setup()
        
        self.workspace = storage_test_utils.create_workspace()
        self.file = storage_test_utils.create_file(media_type='application/json')

    def test_add_filter(self):
        """Tests calling DataFilter.add_value()"""

        filter = DataFilter()
        filter.add_filter({'name': 'input_a', 'type': 'media-type', 'condition': '==', 'values': ['application/json']})
        filter.add_filter({'name': 'input_b', 'type': 'string', 'condition': 'contains', 'values': ['abcde']})
        filter.add_filter({'name': 'input_c', 'type': 'integer', 'condition': '>', 'values': ['0']})
        filter.add_filter({'name': 'input_d', 'type': 'integer', 'condition': 'between', 'values': ['0', '100']})

        filter_dict = {'version': '6', 'filters': [
            {'name': 'input_a', 'type': 'media-type', 'condition': '==', 'values': ['application/json']},
            {'name': 'input_b', 'type': 'string', 'condition': 'contains', 'values': ['abcde']},
            {'name': 'input_c', 'type': 'integer', 'condition': '>', 'values': [0]},
            {'name': 'input_d', 'type': 'integer', 'condition': 'between', 'values': [0,100]}
        ]}
        self.assertItemsEqual(filter.filters, filter_dict['filters'])
        
        with self.assertRaises(InvalidDataFilter) as context:
            filter.add_filter({})
        self.assertEqual(context.exception.error.name, 'MISSING_NAME')
        
        with self.assertRaises(InvalidDataFilter) as context:
            filter.add_filter({'name': 'input_a'})
        self.assertEqual(context.exception.error.name, 'MISSING_TYPE')
        
        with self.assertRaises(InvalidDataFilter) as context:
            filter.add_filter({'name': 'input_a', 'type': 'integer'})
        self.assertEqual(context.exception.error.name, 'MISSING_CONDITION')

    def test_is_data_accepted(self):
        """Tests calling DataFilter.is_data_accepted()"""

        filter = DataFilter(all=False)
        filter.add_filter({'name': 'input_a', 'type': 'media-type', 'condition': '==', 'values': ['application/json']})
        filter.add_filter({'name': 'input_b', 'type': 'string', 'condition': 'contains', 'values': ['abcde']})
        filter.add_filter({'name': 'input_c', 'type': 'integer', 'condition': '>', 'values': ['0']})
        filter.add_filter({'name': 'input_d', 'type': 'integer', 'condition': 'between', 'values': ['0', '100']})
        
        data = Data()

        file_value = FileValue('input_a', [self.file.id])
        data.add_value(file_value)
        
        # first filter passes, so data is accepted if all is set to false
        self.assertTrue(filter.is_data_accepted(data))
        filter.all = True
        # other filters fail so data is not accepted
        self.assertFalse(filter.is_data_accepted(data))
        
        # get other filters to pass
        json_value = JsonValue('input_b', 'abcdefg')
        data.add_value(json_value)
        json_value = JsonValue('input_c', '10')
        data.add_value(json_value)
        json_value = JsonValue('input_d', 50)
        data.add_value(json_value)

        self.assertTrue(filter.is_data_accepted(data))

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
