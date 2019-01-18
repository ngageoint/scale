from __future__ import unicode_literals
from __future__ import absolute_import

import copy
import datetime
import json
import time

import django
import django.utils.timezone as timezone
from django.test import TestCase, TransactionTestCase

from data.interface.interface import Interface
from data.interface.parameter import FileParameter, JsonParameter
from dataset.models import DataSet, DataSetMember
import dataset.test.utils as dataset_test_utils
from dataset.definition.definition import DataSetDefinition, DataSetMemberDefinition
from dataset.definition.json.definition_v6 import DataSetDefinitionV6, DataSetMemberDefinitionV6

class TestDataSetManager(TransactionTestCase):

    def setUp(self):
        django.setup()

        self.definition = {'version': '6',
            'parameters': [{'name': 'global-param', 'param_type': 'global'},
                           {'name': 'member-param', 'param_type': 'member'}],
        }

        self.dataset_definition = DataSetDefinition(self.definition)

    def test_create_dataset(self):
        """Tests calling DataSet.create() """

        name = 'test-dataset'
        title = 'Test Dataset'
        description = 'Test DataSet description'
        version = '1.0.0'

        # call test
        dataset = dataset_test_utils.create_dataset(name=name, title=title, description=description,
            version=version, definition=self.definition)

        # Check results
        the_dataset = DataSet.objects.get(pk=dataset.id)
        self.assertEqual(the_dataset.name, name)
        self.assertEqual(the_dataset.title, title)
        self.assertEqual(the_dataset.version, version)
        self.assertDictEqual(the_dataset.definition, self.definition)

    def test_create_dataset_v6(self):
        """Tests calling DataSetManager.create_dataset_v6() """

        name = 'test-dataset'
        title = 'Test Dataset'
        description = 'Test DataSet description'
        version = '1.0.0'

        # call test
        dataset = DataSet.objects.create_dataset_v6(version, self.dataset_definition, name=name, title=title, description=description)

        # Check results
        the_dataset = DataSet.objects.get(pk=dataset.id)
        self.assertEqual(the_dataset.name, name)
        self.assertEqual(the_dataset.title, title)
        self.assertEqual(the_dataset.version, version)
        self.assertDictEqual(the_dataset.definition, self.dataset_definition.get_dict())

    def test_filter_datasets(self):
        """Tests calling DataSetManager filter_datasets
        """
        name = 'test-dataset-1'
        title = 'Test Dataset 1'
        description = 'Test DataSet description 1'
        version = '1.0.0'

        dataset1 = DataSet.objects.create_dataset_v6(version, self.dataset_definition, name=name, title=title, description=description)

        name = 'test-dataset-2'
        title = 'Test Dataset 2'
        description = 'Test DataSet description 2'
        version = '1.0.0'

        dataset2 = DataSet.objects.create_dataset_v6(version, self.dataset_definition, name=name, title=title, description=description)

        name = 'test-dataset-3'
        title = 'Test Dataset 3'
        description = 'Test DataSet description 3'
        version = '1.0.0'

        dataset3 = DataSet.objects.create_dataset_v6(version, self.dataset_definition, name=name, title=title, description=description)

        ids = [dataset1.id, dataset3.id]

        # Test the filter_datasets method
        datasets = DataSet.objects.filter_datasets(dataset_ids=ids)
        self.assertEqual(len(datasets), 2)
        for ds in datasets:
            self.assertTrue(ds.id in ids)
            self.assertNotEquals(ds.id, dataset2.id)

        datasets = DataSet.objects.filter_datasets(dataset_names=[dataset2.name])
        self.assertEqual(len(datasets), 1)
        self.assertEqual(datasets[0].name, dataset2.name)

    def test_get_datasets_v6(self):
        """Tests calling DataSetmanager.get_datasets_v6() """

        name = 'test-dataset-1'
        title = 'Test Dataset 1'
        description = 'Test DataSet description 1'
        version = '1.0.0'

        dataset1 = DataSet.objects.create_dataset_v6(version, self.dataset_definition, name=name, title=title, description=description)

        name = 'test-dataset-2'
        title = 'Test Dataset 2'
        description = 'Test DataSet description 2'
        version = '1.0.0'
        dataset2 = DataSet.objects.create_dataset_v6(version, self.dataset_definition, name=name, title=title, description=description)

        name = 'test-dataset-3'
        title = 'Test Dataset 3'
        description = 'Test DataSet description 3'
        version = '1.0.0'

        dataset3 = DataSet.objects.create_dataset_v6(version, self.dataset_definition, name=name, title=title, description=description)

        ids = [dataset1.id, dataset3.id]
        datasets = DataSet.objects.get_datasets_v6(dataset_ids=ids)
        self.assertEqual(len(datasets), 2)
        for ds in datasets:
            self.assertTrue(ds.id in ids)
            self.assertNotEquals(ds.id, dataset2.id)

    def test_get_details_v6(self):
        """Tests calling DataSetManager.get_dataset_details() """

        name = 'test-dataset'
        title = 'Test Dataset'
        description = 'Test DataSet description'
        version = '1.0.0'

        # create object
        dataset = DataSet.objects.create_dataset_v6(version, self.dataset_definition, name=name, title=title, description=description)
        dataset2 = DataSet.objects.get_details_v6(name, version)
        self.assertEquals(dataset.name, dataset2.name)
        self.assertEquals(dataset.version, dataset2.version)
        self.assertDictEqual(dataset.definition, dataset2.definition)

class TestDataSetMemberManager(TransactionTestCase):
    """Tests the DataSetMember class"""

    def setUp(self):
        django.setup()

        # create a dataset
        self.dataset = dataset_test_utils.create_dataset(definition={'version': '6','parameters': [{'name': 'member-param', 'param_type': 'member'}],})


        # global_interface = Interface()
        # global_interface.add_parameter(FileParameter('input_a', ['text/csv']))
        # global_interface.add_parameter(JsonParameter('input_b', 'integer'))

        # member_interface = Interface()
        # member_interface.add_parameter(FileParameter('input_c', ['application/json'], False, True))
        # member_interface.add_parameter(JsonParameter('input_d', 'object', False))

        # self.global_definition = DataSetMemberDefinition('global-param', global_interface)
        # self.member_definition = DataSetMemberDefinition('member_param', member_interface)


    def test_create_datast_member(self):
        """Tests calling DataSetMember.create() """
        definition = {
            'name': 'member-param',
            'input': {
                'files': [{'name': 'input_a', 'mediaTypes': ['application/json'], 'required': True, 'partial': False}],
                'json': [],
            },
        }

        # call test
        dataset_member = dataset_test_utils.create_dataset_member(dataset=self.dataset,
            definition=definition)

        # Check results
        the_dataset_member = DataSetMember.objects.get(pk=dataset_member.id)
        self.assertDictEqual(the_dataset_member.definition, definition)

    def test_create_dataset_member_v6(self):
        """Tests calling DataSetManager.create_dataset_v6() """

        member_definition_dict = {
            'name': 'member-param',
            'input': {
                'files': [{'name': 'input_a', 'mediaTypes': ['application/json'], 'required': True, 'partial': False}],
                'json': [],
            },
        }
        member_definition = DataSetMemberDefinition(definition=member_definition_dict)

        # call test
        dataset_member = DataSetMember.objects.create_dataset_member_v6(self.dataset, member_definition)

        # Check results
        the_dataset_member = DataSetMember.objects.get(pk=dataset_member.id)
        self.assertDictEqual(the_dataset_member.definition, member_definition_dict)

    def test_get_dataset_members_v6(self):
        """Tests calling DataSetMemberManager get_dataset_members"""

        # Add some members
        member_definition_1 = {
            'name': 'member-param',
            'input': {
                'files': [{'name': 'input_a', 'mediaTypes': ['application/json'], 'required': True, 'partial': False}],
                'json': [],
            },
        }
        # dataset_member_definition = DataSetMemberDefinition(definition=member_definition_1)
        member_1 = dataset_test_utils.create_dataset_member(dataset=self.dataset, definition=member_definition_1)

        member_definition_2 = {
            'name': 'member-param-2',
            'input': {
                'files': [{'name': 'input_b', 'mediaTypes': ['application/json'], 'required': True, 'partial': False}, {'name': 'input_c', 'mediaTypes': ['application/json'], 'required': True, 'partial': True}],
                'json': [{'name': 'input_d', 'value': 1}],
            },
        }
        # dataset_member_definition = DataSetMemberDefinition(definition=member_definition_2)
        member_2 = dataset_test_utils.create_dataset_member(dataset=self.dataset, definition=member_definition_2)

        members = DataSetMember.objects.get_dataset_members(self.dataset)
        self.assertTrue(len(members), 2)
        for member in members:
            expected = None
            if member.id == member_1.id:
                expected = member_1
            elif member.id == member_2.id:
                expected = member_2
            else:
                self.fail('Found unexpected result: %s' % member.id)
            self.assertDictEqual(member.get_v6_definition_json(), expected.get_v6_definition_json())

class TestDataSetFileManager(TransactionTestCase):
    """Tests the DataSetFileManager class"""

    def setUp(self):
        django.setup()

        # create a dataset
        self.dataset = dataset_test_utils.create_dataset(definition={'version': '6','parameters': [{'name': 'param_a', 'param_type': 'member'}, {'name': 'param_b', 'param_type': 'member'}]})

        # create a couple members
        param_a = {
            'name': 'param_a',
            'input': {
                'files': [{'name': 'input_a', 'mediaTypes': ['application/json'], 'required': True, 'partial': False}],
                'json': [],
            },
        }
        self.member_a = dataset_test_utils.create_dataset_member(dataset=self.dataset, definition=param_a)

        param_b = {
            'name': 'param_b',
            'input': {
                'files': [{'name': 'input_b', 'mediaTypes': ['application/json'], 'required': True, 'partial': False}, {'name': 'input_c', 'mediaTypes': ['application/json'], 'required': True, 'partial': True}],
                'json': [{'name': 'input_d', 'value': 1}],
            },
        }
        self.member_b = dataset_test_utils.create_dataset_member(dataset=self.dataset, definition=param_b)

    def test_create_dataset_file(self):
        """Tests creating a dataset file"""
        pass