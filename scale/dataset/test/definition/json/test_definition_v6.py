from __future__ import unicode_literals

import copy
import django
from django.test import TestCase

from data.data.json.data_v6 import convert_data_to_v6_json
from data.interface.parameter import FileParameter, JsonParameter
from dataset.definition.definition import DataSetDefinition
from dataset.definition.json.definition_v6 import convert_definition_to_v6_json, DataSetDefinitionV6
from dataset.exceptions import InvalidDataSetDefinition
import dataset.test.utils as dataset_test_utils


class TestDataV6(TestCase):

    def setUp(self):
        django.setup()

    def test_convert_definition_to_v6_json(self):
        """Tests calling convert_data_to_v6_json()"""

        # Try interface with nothing set
        definition = DataSetDefinitionV6()
        json = convert_definition_to_v6_json(definition)
        DataSetDefinitionV6(definition=json.get_dict(), do_validate=True)  # Revalidate

        # Try data with a variety of values
        definition = DataSetDefinition()
        file_param = FileParameter('input_1', ['application/json'])
        json_param = JsonParameter('input_2', 'integer')
        file_param2 = FileParameter('input_3', ['application/json'])
        json_param2 = JsonParameter('input_4', 'integer')
        definition.add_global_parameter(file_param)
        definition.add_global_parameter(json_param)
        definition.add_parameter(file_param2)
        definition.add_parameter(json_param2)
        json = convert_data_to_v6_json(definition)
        DataSetDefinitionV6(definition=json.get_dict(), do_validate=True)  # Revalidate
        self.assertSetEqual(set(json.get_definition().get_parameters()), {'input_1', 'input_2', 'input_3', 'input_4'})

    def test_init_validation(self):
        """Tests the validation done in __init__"""

        # Try minimal acceptable configuration
        DataSetDefinitionV6(do_validate=True)

        # Invalid version
        definition = {'version': 'BAD'}
        with self.assertRaises(InvalidDataSetDefinition) as context:
            DataSetDefinitionV6(definition, do_validate=True)
        self.assertEqual(context.exception.error.name, 'INVALID_DATASET_DEFINITION')

        # Valid v6 dataset
        dataset = copy.deepcopy(dataset_test_utils.DATASET_DEFINITION)
        dataset1 = DataSetDefinitionV6(dataset=dataset, do_validate=True).get_dataset()
        self.assertItemsEqual(dataset1.global_data.values['input_a'].file_ids, [1234])
        self.assertItemsEqual(dataset1.global_data.values['input_b'].file_ids, [1235, 1236])
        self.assertEqual(dataset1.global_data.values['input_c'].value, 999)
        self.assertItemsEqual(dataset1.global_data.values['input_d'].value, ['hello'])

        #duplicate parameter
        param = {'version': '6', 'files': [{'name': 'input_a'},
                                               {'name': 'input_f', 'media_types': ['application/json'],
                                                'required': False, 'multiple': True}],
                     'json': [{'name': 'input_g', 'type': 'integer'},
                              {'name': 'input_h', 'type': 'object', 'required': False}]}

        dataset = {'version': '6', 'global_parameters': gp, 'global_data': gd, 'parameters': param}

        with self.assertRaises(InvalidDataSetDefinition) as context:
            dataset2 = DataSetDefinitionV6(dataset=dataset, do_validate=True).get_dataset()
            self.assertEqual(context.exception.error.name, 'INVALID_DATASET_DEFINITION')