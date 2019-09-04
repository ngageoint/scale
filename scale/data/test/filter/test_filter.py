from __future__ import unicode_literals

import django

from django.test.testcases import TestCase

from data.data.data import Data
from data.data.value import FileValue, JsonValue
from data.filter.filter import DataFilter, ALL_CONDITIONS
from data.filter.exceptions import InvalidDataFilter
from data.interface.interface import Interface
from data.interface.parameter import FileParameter, JsonParameter

import storage.test.utils as storage_test_utils


class TestDataFilter(TestCase):
    """Tests related to the DataFilter class"""

    def setUp(self):
        django.setup()
        
        self.workspace = storage_test_utils.create_workspace()
        self.file1 = storage_test_utils.create_file(media_type='application/json')
        self.file2 = storage_test_utils.create_file(media_type='application/json', meta_data={'a': {'b': 'foo'}})

    def test_add_filter(self):
        """Tests calling DataFilter.add_value()"""

        data_filter = DataFilter()
        data_filter.add_filter({'name': 'input_a', 'type': 'media-type', 'condition': '==', 'values': ['application/json']})
        data_filter.add_filter({'name': 'input_b', 'type': 'string', 'condition': 'contains', 'values': ['abcde']})
        data_filter.add_filter({'name': 'input_c', 'type': 'integer', 'condition': '>', 'values': ['0']})
        data_filter.add_filter({'name': 'input_d', 'type': 'integer', 'condition': 'between', 'values': ['0', '100']})

        filter_dict = {'version': '6', 'filters': [
            {'name': 'input_a', 'type': 'media-type', 'condition': '==', 'values': ['application/json']},
            {'name': 'input_b', 'type': 'string', 'condition': 'contains', 'values': ['abcde']},
            {'name': 'input_c', 'type': 'integer', 'condition': '>', 'values': [0]},
            {'name': 'input_d', 'type': 'integer', 'condition': 'between', 'values': [0,100]}
        ]}
        self.assertItemsEqual(data_filter.filter_list, filter_dict['filters'])
        
        with self.assertRaises(InvalidDataFilter) as context:
            data_filter.add_filter({})
        self.assertEqual(context.exception.error.name, 'MISSING_NAME')
        
        with self.assertRaises(InvalidDataFilter) as context:
            data_filter.add_filter({'name': 'input_a'})
        self.assertEqual(context.exception.error.name, 'MISSING_TYPE')
        
        with self.assertRaises(InvalidDataFilter) as context:
            data_filter.add_filter({'name': 'input_a', 'type': 'integer'})
        self.assertEqual(context.exception.error.name, 'MISSING_CONDITION')

    def test_is_data_accepted(self):
        """Tests calling DataFilter.is_data_accepted()"""

        data_filter = DataFilter(all=False)
        data_filter.add_filter({'name': 'input_a', 'type': 'media-type', 'condition': '==', 'values': ['application/json']})
        data_filter.add_filter({'name': 'input_b', 'type': 'string', 'condition': 'contains', 'values': ['abcde']})
        data_filter.add_filter({'name': 'input_c', 'type': 'integer', 'condition': '>', 'values': ['0']})
        data_filter.add_filter({'name': 'input_d', 'type': 'integer', 'condition': 'between', 'values': ['0', '100']})
        data_filter.add_filter({'name': 'input_f', 'type': 'meta-data', 'condition': 'in', 'values': [['foo', 'baz']],
                                'fields': [['a', 'b']]})
        
        data = Data()

        file_value = FileValue('input_a', [self.file1.id])
        data.add_value(file_value)
        
        # first filter passes, so data is accepted if all is set to false
        self.assertTrue(data_filter.is_data_accepted(data))
        data_filter.all = True
        # other filters fail so data is not accepted
        self.assertFalse(data_filter.is_data_accepted(data))
        
        # get other filters to pass
        json_value = JsonValue('input_b', 'abcdefg')
        data.add_value(json_value)
        json_value = JsonValue('input_c', '10')
        data.add_value(json_value)
        json_value = JsonValue('input_d', 50)
        data.add_value(json_value)
        file_value = FileValue('input_f', [self.file2.id])
        data.add_value(file_value)

        self.assertTrue(data_filter.is_data_accepted(data))

    def test_validate(self):
        """Tests calling DataFilter.validate()"""

        data_filter = DataFilter(all=False)
        data_filter.add_filter({'name': 'input_a', 'type': 'media-type', 'condition': '==', 'values': ['application/json']})
        data_filter.add_filter({'name': 'input_b', 'type': 'string', 'condition': 'contains', 'values': ['abcde']})
        data_filter.add_filter({'name': 'input_c', 'type': 'integer', 'condition': '>', 'values': ['0']})
        data_filter.add_filter({'name': 'input_d', 'type': 'integer', 'condition': 'between', 'values': ['0', '100']})
        data_filter.add_filter({'name': 'input_f', 'type': 'meta-data', 'condition': 'in', 'values': [['foo','baz']],
                                'fields': [['a','b']]})

        interface = Interface()
        interface.add_parameter(FileParameter('input_a', ['application/json']))
        warnings = data_filter.validate(interface)
        self.assertEqual(len(warnings), 4)
        self.assertEqual(warnings[0].name, 'UNMATCHED_FILTER')
        
        interface.add_parameter(JsonParameter('input_e', 'integer'))
        warnings = data_filter.validate(interface)
        self.assertEqual(len(warnings), 5)
        self.assertEqual(warnings[3].name, 'UNMATCHED_FILTER')
        self.assertEqual(warnings[4].name, 'UNMATCHED_PARAMETERS')
        
        interface.add_parameter(JsonParameter('input_b', 'integer'))
        with self.assertRaises(InvalidDataFilter) as context:
            data_filter.validate(interface)
        self.assertEqual(context.exception.error.name, 'MISMATCHED_TYPE')
        
        interface2 = Interface()
        interface2.add_parameter(FileParameter('input_a', ['application/json']))
        interface2.add_parameter(JsonParameter('input_b', 'string'))
        interface2.add_parameter(JsonParameter('input_c', 'integer'))
        interface2.add_parameter(JsonParameter('input_d', 'integer'))
        interface2.add_parameter(FileParameter('input_f', ['integer']))
        warnings = data_filter.validate(interface2)
        self.assertEqual(len(warnings), 0)
        
        
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

        with self.assertRaises(InvalidDataFilter) as context:
            DataFilter.validate_filter({'name': 'input_a', 'type': 'object', 'condition': '<', 'values': [['not a number']]})
        self.assertEqual(context.exception.error.name, 'INVALID_CONDITION')

        with self.assertRaises(InvalidDataFilter) as context:
            DataFilter.validate_filter({'name': 'input_a', 'type': 'object', 'condition': '<', 'values': [['not a number']], 'fields': [['a'],['b']]})
        self.assertEqual(context.exception.error.name, 'INVALID_FIELDS')
        
    def test_less_than(self):
        """Tests less than operation
        """
    
        self.assertTrue(ALL_CONDITIONS['<'](0, [1]))
        self.assertFalse(ALL_CONDITIONS['<'](1, [0]))
        self.assertFalse(ALL_CONDITIONS['<'](1, []))
        
    def test_less_than_equal(self):
        """Tests less than equal operation
        """
    
        self.assertTrue(ALL_CONDITIONS['<='](0, [1]))
        self.assertTrue(ALL_CONDITIONS['<='](0, [0]))
        self.assertFalse(ALL_CONDITIONS['<='](1, [0]))
        self.assertFalse(ALL_CONDITIONS['<='](1, []))
        
    def test_greater_than(self):
        """Tests greater than operation
        """
    
        self.assertTrue(ALL_CONDITIONS['>'](1, [0]))
        self.assertFalse(ALL_CONDITIONS['>'](0, [1]))
        self.assertFalse(ALL_CONDITIONS['>'](1, []))
        
    def test_greater_than_equal(self):
        """Tests greater than equal operation
        """
    
        self.assertTrue(ALL_CONDITIONS['>='](1, [0]))
        self.assertTrue(ALL_CONDITIONS['>='](1, [1]))
        self.assertFalse(ALL_CONDITIONS['>='](0, [1]))
        self.assertFalse(ALL_CONDITIONS['>='](1, []))
        
    def test_equal(self):
        """Tests equal operation
        """
    
        self.assertTrue(ALL_CONDITIONS['=='](1, [1]))
        self.assertTrue(ALL_CONDITIONS['==']('1', ['1']))
        self.assertFalse(ALL_CONDITIONS['=='](0, [1]))
        self.assertFalse(ALL_CONDITIONS['=='](1, []))

    def test_not_equal(self):
        """Tests not equal operation
        """
    
        self.assertTrue(ALL_CONDITIONS['!='](1, [0]))
        self.assertTrue(ALL_CONDITIONS['!=']('1', ['0']))
        self.assertFalse(ALL_CONDITIONS['!='](0, [0]))
        self.assertFalse(ALL_CONDITIONS['!='](1, []))

    def test_between(self):
        """Tests between operation
        """
    
        self.assertTrue(ALL_CONDITIONS['between'](1, [0,10]))
        self.assertFalse(ALL_CONDITIONS['between'](10, [0,5]))
        self.assertFalse(ALL_CONDITIONS['between'](1, [1]))

    def test_in(self):
        """Tests in operation
        """
    
        self.assertTrue(ALL_CONDITIONS['in'](1, [1]))
        self.assertTrue(ALL_CONDITIONS['in']('1', ['1']))
        self.assertFalse(ALL_CONDITIONS['in']('1', ['123']))
        self.assertFalse(ALL_CONDITIONS['in']('4', ['123']))
        self.assertFalse(ALL_CONDITIONS['in'](4, [123]))
        self.assertFalse(ALL_CONDITIONS['in'](4, 4))

    def test_not_in(self):
        """Tests not in operation
        """
    
        self.assertFalse(ALL_CONDITIONS['not in'](1, [1]))
        self.assertFalse(ALL_CONDITIONS['not in']('1', ['1']))
        self.assertTrue(ALL_CONDITIONS['not in']('1', ['123']))
        self.assertTrue(ALL_CONDITIONS['not in']('4', ['123']))
        self.assertTrue(ALL_CONDITIONS['not in'](4, [123]))
        self.assertTrue(ALL_CONDITIONS['not in'](4, 4))

    def test_contains(self):
        """Tests contains operation
        """
    
        self.assertFalse(ALL_CONDITIONS['contains'](1, [1]))
        self.assertTrue(ALL_CONDITIONS['contains']('1', ['1']))
        self.assertFalse(ALL_CONDITIONS['contains']('1', ['123']))
        self.assertFalse(ALL_CONDITIONS['contains'](['123'], ['1']))
        self.assertTrue(ALL_CONDITIONS['contains']('123', ['1']))
        self.assertTrue(ALL_CONDITIONS['contains']({'a':1}, ['a']))
        self.assertFalse(ALL_CONDITIONS['contains']({'a':{'b': 1}}, ['b']))
        self.assertFalse(ALL_CONDITIONS['contains']({'a':{'b': 1}}, [{'b': 1}]))
        
    def test_subset(self):
        """Tests subset operation
        """
    
        self.assertFalse(ALL_CONDITIONS['subset of'](1, [{'b': 1}]))
        self.assertFalse(ALL_CONDITIONS['subset of']({'b': 1}, [1]))
        self.assertFalse(ALL_CONDITIONS['subset of']({'b': 1}, []))
        self.assertFalse(ALL_CONDITIONS['subset of']({'b': 1}, [{'a':1,'b': 2}]))
        self.assertTrue(ALL_CONDITIONS['subset of']({'b': 2}, [{'a':1,'b': 2}]))

    def test_superset(self):
        """Tests superset operation
        """
    
        self.assertFalse(ALL_CONDITIONS['superset of'](1, [{'b': 1}]))
        self.assertFalse(ALL_CONDITIONS['superset of']({'b': 1}, [1]))
        self.assertFalse(ALL_CONDITIONS['superset of']({'b': 1}, []))
        self.assertFalse(ALL_CONDITIONS['superset of']({'a': 1, 'b': 2}, [{'b': 1}]))
        self.assertTrue(ALL_CONDITIONS['superset of']({'a': 1, 'b': 2}, [{'b': 2}]))
