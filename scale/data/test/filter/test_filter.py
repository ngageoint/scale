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

    def test_validate_filter(self):
        """Tests calling DataFilter.validate_filter()"""

        with self.assertRaises(InvalidDataFilter) as context:
            DataFilter.validate_filter({})
        self.assertEqual(context.exception.error.name, 'MISSING_NAME')
        
        with self.assertRaises(InvalidDataFilter) as context:
            DataFilter.validate_filter({'name': 'input_a'})
        self.assertEqual(context.exception.error.name, 'MISSING_TYPE')
        
        with self.assertRaises(InvalidDataFilter) as context:
            DataFilter.validate_filter({'name': 'input_a', 'type': 'integer'})
        self.assertEqual(context.exception.error.name, 'MISSING_CONDITION')
        
        with self.assertRaises(InvalidDataFilter) as context:
            DataFilter.validate_filter({'name': 'input_a', 'type': 'integer', 'condition': '>'})
        self.assertEqual(context.exception.error.name, 'MISSING_VALUES')
        
        with self.assertRaises(InvalidDataFilter) as context:
            DataFilter.validate_filter({'name': 'input_a', 'type': 'integer', 'condition': 'BAD', 'values': [0]})
        self.assertEqual(context.exception.error.name, 'INVALID_CONDITION')
        
        with self.assertRaises(InvalidDataFilter) as context:
            DataFilter.validate_filter({'name': 'input_a', 'type': 'string', 'condition': 'between', 'values': ['0']})
        self.assertEqual(context.exception.error.name, 'INVALID_CONDITION')
        
        with self.assertRaises(InvalidDataFilter) as context:
            DataFilter.validate_filter({'name': 'input_a', 'type': 'integer', 'condition': 'contains', 'values': [0]})
        self.assertEqual(context.exception.error.name, 'INVALID_CONDITION')
        
        with self.assertRaises(InvalidDataFilter) as context:
            DataFilter.validate_filter({'name': 'input_a', 'type': 'boolean', 'condition': 'contains', 'values': [0]})
        self.assertEqual(context.exception.error.name, 'INVALID_CONDITION')
        
        with self.assertRaises(InvalidDataFilter) as context:
            DataFilter.validate_filter({'name': 'input_a', 'type': 'bad', 'condition': 'contains', 'values': [0]})
        self.assertEqual(context.exception.error.name, 'INVALID_TYPE')
        
        with self.assertRaises(InvalidDataFilter) as context:
            DataFilter.validate_filter({'name': 'input_a', 'type': 'integer', 'condition': '<', 'values': ['not a number']})
        self.assertEqual(context.exception.error.name, 'VALUE_ERROR')
