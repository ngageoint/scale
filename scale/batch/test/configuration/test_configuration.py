from __future__ import unicode_literals

import copy
import django
from django.test import TestCase

from batch.definition.definition import BatchDefinition
from batch.configuration.exceptions import InvalidConfiguration
from batch.configuration.json.configuration_v6 import BatchConfigurationV6
from batch.test import utils as batch_test_utils
from data.data.json.data_v6 import DataV6
from data.test import utils as data_test_utils
from storage.test import utils as storage_test_utils


class TestBatchDefinition(TestCase):

    def setUp(self):
        django.setup()

    def test_create_from_json(self):
        """Tests creating a BatchConfiguration from a JSON"""

        # Valid batch configuration
        json_dict = {'version': '6', 'priority': 201}
        json = BatchConfigurationV6(configuration=json_dict, do_validate=True)
        config = json.get_configuration()
        self.assertEqual(config.priority, 201)

    def test_validate(self):
        """Tests calling BatchConfiguration.validate()"""

        batch = batch_test_utils.create_batch()

        # Valid configuration
        json_dict = {'version': '6', 'priority': 202}
        json = BatchConfigurationV6(configuration=json_dict)
        configuration = json.get_configuration()
        configuration.validate(batch)

    def test_inputmap(self):
        dataset_def = {
            'parameters': {
                'files': [{'media_types': ['image/png'], 'required': True, 'multiple': False, 'name': 'INPUT_IMAGE'}],
                'json': []}
        }
        the_dataset = data_test_utils.create_dataset(definition=dataset_def)
        workspace = storage_test_utils.create_workspace()
        src_file_a = storage_test_utils.create_file(file_name='input_a.PNG', file_type='SOURCE', media_type='image/png',
                                                    file_size=10, data_type_tags=['type'], file_path='the_path',
                                                    workspace=workspace)
        src_file_b = storage_test_utils.create_file(file_name='input_b.PNG', file_type='SOURCE', media_type='image/png',
                                                    file_size=10, data_type_tags=['type'], file_path='the_path',
                                                    workspace=workspace)
        data_list = []
        data_dict = {
            'version': '6',
            'files': {'FILE_INPUT': [src_file_a.id]},
            'json': {}
        }
        data_list.append(DataV6(data=data_dict).get_dict())
        data_dict = {
            'version': '6',
            'files': {'FILE_INPUT': [src_file_b.id]},
            'json': {}
        }
        data_list.append(DataV6(data=data_dict).get_dict())
        members = data_test_utils.create_dataset_members(dataset=the_dataset, data_list=data_list)

        batch_def = BatchDefinition()
        batch_def.dataset = the_dataset.id
        batch = batch_test_utils.create_batch(definition=batch_def)

        json_dict = {
            'version': '6',
            'priority': 100,
            'inputMap': [{
                'input': 'FILE_INPUT',
                'datasetParameter': 'INPUT_IMAGE'
            }]
        }
        json = BatchConfigurationV6(configuration=json_dict)
        configuration = json.get_configuration()
        configuration.validate(batch)

        json_dict = {
            'version': '6',
            'priority': 100,
            'inputMap': [{
                'input': 'FILE_INPUT',
                'datasetParameter': 'FILE_INPUT'
            }]
        }
        json = BatchConfigurationV6(configuration=json_dict)
        configuration = json.get_configuration()
        self.assertRaises(InvalidConfiguration, configuration.validate, batch)
