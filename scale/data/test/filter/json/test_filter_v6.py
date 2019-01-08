from __future__ import unicode_literals

import django
from django.test import TestCase

from data.filter.filter import DataFilter
from data.filter.exceptions import InvalidDataFilter
from data.filter.json.filter_v6 import convert_filter_to_v6_json, DataFilterV6


class TestDataFilterV6(TestCase):

    def setUp(self):
        django.setup()

    def test_convert_filter_to_v6_json(self):
        """Tests calling convert_filter_to_v6_json()"""

        # Try interface with nothing set
        filter = DataFilter()
        json = convert_filter_to_v6_json(filter)
        DataFilterV6(data_filter=json.get_dict(), do_validate=True)  # Revalidate

        # Try data with a variety of values
        filter_dict = {'version': '6', 'filters': [
            {'name': 'input_a', 'type': 'media-type', 'condition': '==', 'values': ['application/json']},
            {'name': 'input_b', 'type': 'string', 'condition': 'contains', 'values': ['abcde']},
            {'name': 'input_c', 'type': 'integer', 'condition': '>', 'values': ['0']},
            {'name': 'input_d', 'type': 'integer', 'condition': 'between', 'values': ['0', '100']}
        ]}
        filter = DataFilter(filters=filter_dict['filters'])
        json = convert_filter_to_v6_json(filter)
        DataFilterV6(data_filter=json.get_dict(), do_validate=True)  # Revalidate
        filter_dict['filters'][2]['values'] = [0]
        filter_dict['filters'][3]['values'] = [0,100]
        self.assertItemsEqual(json.get_filter().filters, filter_dict['filters'])

    def test_init_validation(self):
        """Tests the validation done in __init__"""

        # Try minimal acceptable configuration
        DataFilterV6(do_validate=True)

        # Invalid version
        filter = {'version': 'BAD'}
        with self.assertRaises(InvalidDataFilter) as context:
            DataFilterV6(filter, do_validate=True)
        self.assertEqual(context.exception.error.name, 'INVALID_VERSION')

        # invalid type
        filter = {'version': '6', 'filters': [
            {'name': 'input_a', 'type': 'BAD', 'condition': '>', 'values': ['application/json']}
        ]}
        with self.assertRaises(InvalidDataFilter) as context:
            DataFilterV6(filter, do_validate=True)
        self.assertEqual(context.exception.error.name, 'INVALID_DATA_FILTER')
        
        # invalid condition
        filter = {'version': '6', 'filters': [
            {'name': 'input_a', 'type': 'media-type', 'condition': 'BAD', 'values': ['application/json']}
        ]}
        with self.assertRaises(InvalidDataFilter) as context:
            DataFilterV6(filter, do_validate=True)
        self.assertEqual(context.exception.error.name, 'INVALID_DATA_FILTER')

        # Valid v6 filter
        filter = {'version': '6', 'filters': [
            {'name': 'input_a', 'type': 'media-type', 'condition': '==', 'values': ['application/json']},
            {'name': 'input_b', 'type': 'string', 'condition': 'contains', 'values': ['abcde']},
            {'name': 'input_c', 'type': 'integer', 'condition': '>', 'values': [0]},
            {'name': 'input_d', 'type': 'integer', 'condition': 'between', 'values': [0, 100]}
        ]}
        data1 = DataFilterV6(data_filter=filter, do_validate=True).get_filter()
        self.assertItemsEqual(data1.filters, filter['filters'])

