from __future__ import unicode_literals

import django
from django.test import TestCase

from data.data.data import Data
from data.data.json.data_v1 import convert_data_to_v1_json, DataV1
from data.data.json.data_v6 import DataV6
from data.data.value import FileValue, JsonValue
from data.interface.interface import Interface
from data.interface.parameter import FileParameter


class TestDataV1(TestCase):

    def setUp(self):
        django.setup()

    def test_convert_data_to_v1_json(self):
        """Tests calling convert_data_to_v1_json()"""

        # Try interface with nothing set
        data = Data()
        interface = Interface()
        json = convert_data_to_v1_json(data, interface)
        DataV1(data=json.get_dict())  # Revalidate

        # Try data with a variety of values
        data = Data()
        data.add_value(FileValue('input_a', [1234]))
        data.add_value(FileValue('input_b', [1235, 1236]))
        data.add_value(JsonValue('input_c', 'hello'))
        data.add_value(JsonValue('input_d', 11.9))
        json = convert_data_to_v1_json(data, interface)
        self.assertDictEqual(json.get_dict(), {u'input_data': [{u'name': u'input_d', u'value': 11.9}, {u'name': u'input_b', u'file_ids': [1235, 1236]}, {u'name': u'input_c', u'value': u'hello'}, {u'name': u'input_a', u'file_id': 1234}], u'version': u'1.0'})
        DataV1(data=json.get_dict())  # Revalidate
        self.assertSetEqual(set(DataV6(json.get_dict()).get_data().values.keys()),
                            {'input_a', 'input_b', 'input_c', 'input_d'})

        # Try data with a single file list that should be a directory
        data = Data()
        data.add_value(FileValue('input_a', [1234]))
        interface = Interface()
        file_param = FileParameter('input_a', [], True, True)
        interface.add_parameter(file_param)
        json = convert_data_to_v1_json(data, interface)
                            
        self.assertDictEqual(json.get_dict(), {u'input_data': [{u'name': u'input_a', u'file_ids': [1234]}], u'version': u'1.0'})