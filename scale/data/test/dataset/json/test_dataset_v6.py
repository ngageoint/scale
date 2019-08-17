from __future__ import unicode_literals

import copy
import django
from django.test import TestCase

from data.data.value import FileValue, JsonValue
from data.interface.parameter import FileParameter, JsonParameter
from data.dataset.dataset import DataSetDefinition
from data.dataset.json.dataset_v6 import convert_definition_to_v6_json, DataSetDefinitionV6
from data.exceptions import InvalidDataSetDefinition
import data.test.utils as dataset_test_utils


class TestDataV6(TestCase):

    def setUp(self):
        django.setup()

    def test_convert_definition_to_v6_json(self):
        """Tests calling convert_data_to_v6_json()"""

        # Try interface with nothing set
        definition = DataSetDefinitionV6()
        json = convert_definition_to_v6_json(definition.get_definition())
        DataSetDefinitionV6(definition=json.get_dict(), do_validate=True)  # Revalidate

        # Try data with a variety of values
        definition = DataSetDefinition(definition={})
        file_param = FileParameter('input_a', ['application/json'])
        json_param = JsonParameter('input_b', 'integer')
        file_param2 = FileParameter('input_c', ['application/json'])
        json_param2 = JsonParameter('input_d', 'integer')
        definition.add_global_parameter(file_param)
        definition.add_global_parameter(json_param)
        definition.add_global_value(FileValue('input_a', [123]))
        definition.add_global_value(JsonValue('input_b', 100))
        definition.add_parameter(file_param2)
        definition.add_parameter(json_param2)
        json = convert_definition_to_v6_json(definition)
        DataSetDefinitionV6(definition=json.get_dict(), do_validate=True)  # Revalidate
        self.assertSetEqual(set(json.get_definition().get_parameters()), {'input_a', 'input_b', 'input_c', 'input_d'})

    def test_init_validation(self):
        """Tests the validation done in __init__"""

        # Try minimal acceptable configuration
        DataSetDefinitionV6(do_validate=True)

        # Invalid version
        with self.assertRaises(InvalidDataSetDefinition) as context:
            definition = {'version': 'BAD'}
            DataSetDefinitionV6(definition=definition, do_validate=True)
        self.assertEqual(context.exception.error.name, 'INVALID_VERSION')

        # Valid v6 dataset
        definition = copy.deepcopy(dataset_test_utils.DATASET_DEFINITION)
        definition1 = DataSetDefinitionV6(definition=definition, do_validate=True).get_definition()
        self.assertItemsEqual(definition1.global_data.values['input_a'].file_ids, [1234])
        self.assertItemsEqual(definition1.global_data.values['input_b'].file_ids, [1235, 1236])
        self.assertEqual(definition1.global_data.values['input_c'].value, 999)
        self.assertDictEqual(definition1.global_data.values['input_d'].value, {'greeting': 'hello'})

        #duplicate parameter
        param = {'version': '6', 'files': [{'name': 'input_a'},
                                               {'name': 'input_f', 'media_types': ['application/json'],
                                                'required': False, 'multiple': True}],
                     'json': [{'name': 'input_g', 'type': 'integer'},
                              {'name': 'input_h', 'type': 'object', 'required': False}]}

        definition['parameters'] = param

        with self.assertRaises(InvalidDataSetDefinition) as context:
            dataset2 = DataSetDefinitionV6(definition=definition, do_validate=True).get_definition()
            self.assertEqual(context.exception.error.name, 'INVALID_DATASET_DEFINITION')

        # Global param/data mismatch
        definition = copy.deepcopy(dataset_test_utils.DATASET_DEFINITION)
        del definition['global_data']['files']['input_a']
        with self.assertRaises(InvalidDataSetDefinition) as context:
            dataset3 = DataSetDefinitionV6(definition=definition, do_validate=True).get_definition()
        self.assertEqual(context.exception.error.name, 'INVALID_GLOBAL_DATA')