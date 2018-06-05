from __future__ import unicode_literals

import django
from django.test import TestCase

from data.data.data import Data
from data.data.exceptions import InvalidData
from data.data.json.data_v6 import convert_data_to_v6_json, DataV6
from data.data.value import FileValue, JsonValue


class TestDataV6(TestCase):

    def setUp(self):
        django.setup()

    def test_convert_data_to_v6_json(self):
        """Tests calling convert_data_to_v6_json()"""

        # Try interface with nothing set
        data = Data()
        json = convert_data_to_v6_json(data)
        DataV6(data=json.get_dict(), do_validate=True)  # Revalidate

        # Try data with a variety of values
        data = Data()
        data.add_value(FileValue('input_a', [1234]))
        data.add_value(FileValue('input_b', [1235, 1236]))
        data.add_value(JsonValue('input_c', 'hello'))
        data.add_value(JsonValue('input_d', 11.9))
        json = convert_data_to_v6_json(data)
        DataV6(data=json.get_dict(), do_validate=True)  # Revalidate
        self.assertSetEqual(set(json.get_data().values.keys()), {'input_a', 'input_b', 'input_c', 'input_d'})

    def test_init_validation(self):
        """Tests the validation done in __init__"""

        # Try minimal acceptable configuration
        DataV6(do_validate=True)

        # Invalid version
        data = {'version': 'BAD'}
        with self.assertRaises(InvalidData) as context:
            DataV6(data, do_validate=True)
        self.assertEqual(context.exception.error.name, 'INVALID_VERSION')

        # Valid data
        data = {'version': '6', 'files': {'input_a': [1234], 'input_b': [1235, 1236]},
                                'json': {'input_c': 999, 'input_d': {'hello'}}}
        DataV6(data=data, do_validate=True)
