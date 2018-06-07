from __future__ import unicode_literals

import django
from django.test import TestCase

from data.data.data import Data
from data.data.json.data_v1 import convert_data_to_v1_json, DataV1
from data.data.json.data_v6 import DataV6
from data.data.value import FileValue, JsonValue


class TestDataV1(TestCase):

    def setUp(self):
        django.setup()

    def test_convert_data_to_v1_json(self):
        """Tests calling convert_data_to_v1_json()"""

        # Try interface with nothing set
        data = Data()
        json = convert_data_to_v1_json(data)
        DataV1(data=json.get_dict())  # Revalidate

        # Try data with a variety of values
        data = Data()
        data.add_value(FileValue('input_a', [1234]))
        data.add_value(FileValue('input_b', [1235, 1236]))
        data.add_value(JsonValue('input_c', 'hello'))
        data.add_value(JsonValue('input_d', 11.9))
        json = convert_data_to_v1_json(data)
        DataV1(data=json.get_dict())  # Revalidate
        self.assertSetEqual(set(DataV6(json.get_dict()).get_data().values.keys()),
                            {'input_a', 'input_b', 'input_c', 'input_d'})
