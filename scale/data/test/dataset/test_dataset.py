from __future__ import unicode_literals

import django

from django.test.testcases import TestCase

from data.data.data import Data
from data.data.exceptions import InvalidData
from data.data.value import FileValue, JsonValue
from data.interface.parameter import FileParameter, JsonParameter
from data.dataset.dataset import DataSetDefinition
from data.exceptions import InvalidDataSetDefinition


class TestDataSetDefinition(TestCase):
    """Tests related to the DataSetDefinition class"""

    def setUp(self):
        django.setup()

        self.definition = DataSetDefinition()
        self.file_param = FileParameter('input_a', ['application/json'])
        self.json_param = JsonParameter('input_b', 'integer')
        self.file_param2 = FileParameter('input_c', ['application/json'])
        self.json_param2 = JsonParameter('input_d', 'integer')
        self.definition.add_global_parameter(self.file_param)
        self.definition.add_global_parameter(self.json_param)
        self.definition.add_parameter(self.file_param2)
        self.definition.add_parameter(self.json_param2)

    def test_add_parameter(self):
        """Tests calling DataSetDefinition.add_value()"""
        
        self.assertSetEqual(set(self.definition.get_parameters()), {'input_a', 'input_b', 'input_c', 'input_d'})

        file_param = FileParameter('input_e', ['application/json'])
        self.definition.add_parameter(file_param)
        
        self.assertSetEqual(set(self.definition.get_parameters()), {'input_a', 'input_b', 'input_c', 'input_d', 'input_e'})

        #test adding duplicate
        with self.assertRaises(InvalidDataSetDefinition) as context:
            self.definition.add_parameter(self.file_param)
            self.assertEqual(context.exception.error.name, 'DUPLICATE_PARAMETER')

        with self.assertRaises(InvalidDataSetDefinition) as context:
            self.definition.add_global_parameter(self.file_param2)
            self.assertEqual(context.exception.error.name, 'DUPLICATE_PARAMETER')

    def test_validate(self):
        """Tests calling DataSetDefinition.validate()"""

        data = Data()
        data.add_value(FileValue('input_c', [124]))
        
        #missing global data
        with self.assertRaises(InvalidDataSetDefinition) as context:
            self.definition.validate(data=data)
            self.assertEqual(context.exception.error.name, 'MISSING_GLOBAL_DATA')
            
        #incorrect global data
        gd = Data()
        gd.add_value(FileValue('input_a', [123]))
        gd.add_value(FileValue('input_b', [123]))
        self.definition.global_data = gd
        with self.assertRaises(InvalidData) as context:
            self.definition.validate(data=data)
        self.assertEqual(context.exception.error.name, 'MISMATCHED_PARAM_TYPE')
        
        #missing data
        gd2 = Data()
        gd2.add_value(FileValue('input_a', [123]))       
        gd2.add_value(JsonValue('input_b', 100))        
        self.definition.global_data = gd2

        with self.assertRaises(InvalidData) as context:
            self.definition.validate(data=data)
        self.assertEqual(context.exception.error.name, 'PARAM_REQUIRED')
        
        #successful validation
        data.add_value(JsonValue('input_d', 100))
        self.definition.validate(data=data)

        #incorrect data
        data2 = Data()
        data2.add_value(FileValue('input_c', [124]))
        data2.add_value(FileValue('input_d', [124]))
        
        with self.assertRaises(InvalidData) as context:
            self.definition.validate(data=data2)
        self.assertEqual(context.exception.error.name, 'MISMATCHED_PARAM_TYPE')

