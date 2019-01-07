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
        DataFilterV6(data=json.get_dict(), do_validate=True)  # Revalidate

        # Try data with a variety of values
        filter = DataFilter()
        filter.add_filter({'name': 'input_a', 'type': 'media-type', 'condition': '==', 'values': ['application/json']})
        filter.add_filter({'name': 'input_b', 'type': 'string', 'condition': 'contains', 'values': ['abcde']})
        filter.add_filter({'name': 'input_c', 'type': 'integer', 'condition': '>', 'values': [0]})
        filter.add_filter({'name': 'input_d', 'type': 'integer', 'condition': 'between', 'values': [0,100]})
        json = convert_filter_to_v6_json(filter)
        DataFilterV6(data=json.get_dict(), do_validate=True)  # Revalidate
        self.assertSetEqual(set(json.get_filter().filters.keys()), {'input_a', 'input_b', 'input_c', 'input_d'})

    def test_init_validation(self):
        """Tests the validation done in __init__"""

        # Try minimal acceptable configuration
        DataFilterV6(do_validate=True)

        # Invalid version
        filter = {'version': 'BAD'}
        with self.assertRaises(InvalidDataFilter) as context:
            DataFilterV6(filter, do_validate=True)
        self.assertEqual(context.exception.error.name, 'INVALID_VERSION')

        # invalid condition
        filter = {'version': '6', 'filters': [
            {'name': 'input_a', 'type': 'media-type', 'condition': 'BAD', 'values': ['application/json']}
        ]}
        with self.assertRaises(InvalidDataFilter) as context:
            DataFilterV6(filter, do_validate=True)

        # Valid v6 filter
        filter = {'version': '6', 'filters': [
            {'name': 'input_a', 'type': 'media-type', 'condition': '==', 'values': ['application/json']},
            {'name': 'input_b', 'type': 'string', 'condition': 'contains', 'values': ['abcde']},
            {'name': 'input_c', 'type': 'integer', 'condition': '>', 'values': [0]},
            {'name': 'input_d', 'type': 'integer', 'condition': 'between', 'values': [0, 100]}
        ]}
        data1 = DataFilterV6(data_filter=filter, do_validate=True).get_data()
        self.assertItemsEqual(data1.filters['input_a'], [1234])
        self.assertItemsEqual(data1.filters['input_b'], [1235, 1236])
        self.assertEqual(data1.filters['input_c'], 999)
        self.assertItemsEqual(data1.filters['input_d'], ['hello'])

