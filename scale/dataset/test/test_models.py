from __future__ import unicode_literals
from __future__ import absolute_import

import copy
import datetime
import json
import time

import django
from django.utils.timezone import now
from django.test import TestCase, TransactionTestCase

from data.interface.interface import Interface
from data.interface.parameter import FileParameter, JsonParameter
from dataset.models import DataSet, DataSetMember
import dataset.test.utils as dataset_test_utils
from dataset.definition.definition import DataSetDefinition
from dataset.definition.json.definition_v6 import DataSetDefinitionV6
from storage.models import ScaleFile, Workspace

class TestDataSetManager(TransactionTestCase):

    def setUp(self):
        django.setup()

        self.definition = copy.deepcopy(dataset_test_utils.DATASET_DEFINITION)
        self.dataset_definition = DataSetDefinitionV6(self.definition).get_definition()

    def test_create_dataset(self):
        """Tests calling DataSet.create() """

        title = 'Test Dataset'
        description = 'Test DataSet description'

        # call test
        dataset = dataset_test_utils.create_dataset(title=title, description=description,
            definition=self.definition)

        # Check results
        the_dataset = DataSet.objects.get(pk=dataset.id)
        self.assertEqual(the_dataset.title, title)
        self.assertDictEqual(the_dataset.definition, self.definition)

    def test_create_dataset_v6(self):
        """Tests calling DataSetManager.create_dataset_v6() """

        name = 'test-dataset'
        title = 'Test Dataset'
        description = 'Test DataSet description'
        version = '1.0.0'

        # call test
        dataset = DataSet.objects.create_dataset_v6(definition=self.dataset_definition, title=title, description=description)

        # Check results
        the_dataset = DataSet.objects.get(pk=dataset.id)
        self.assertEqual(the_dataset.title, title)
        self.assertDictEqual(the_dataset.definition, self.dataset_definition.get_dict())

    def test_filter_datasets(self):
        """Tests calling DataSetManager filter_datasets
        """
        title = 'Test Dataset 1'
        description = 'Test DataSet description 1'

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

        data = copy.deepcopy(dataset_test_utils.DATA_DEFINITION)

        # call test
        dataset_member = DataSetMember.objects.create_dataset_member_v6(self.dataset, data=data)

        # Check results
        the_dataset_member = DataSetMember.objects.get(pk=dataset_member.id)
        self.assertDictEqual(the_dataset_member.definition, data)

    def test_get_dataset_members_v6(self):
        """Tests calling DataSetMemberManager get_dataset_members"""

        # Add some members
        data1 = copy.deepcopy(dataset_test_utils.DATA_DEFINITION)

        # dataset_member_definition = DataSetMemberDefinition(definition=member_definition_1)
        member_1 = dataset_test_utils.create_dataset_member(dataset=self.dataset, data=data1)

        data2 = copy.deepcopy(dataset_test_utils.DATA_DEFINITION)

        # dataset_member_definition = DataSetMemberDefinition(definition=member_definition_2)
        member_2 = dataset_test_utils.create_dataset_member(dataset=self.dataset, data=data2)

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

class TestDataSetFile(TransactionTestCase):
    """Tests the DataSetFileManager class"""

    def setUp(self):
        django.setup()

        # create a workspace
        self.workspace = Workspace.objects.create(name='Test Workspace', is_active=True, created=now(),
                                                  last_modified=now())

        # create a dataset
        self.dataset = dataset_test_utils.create_dataset()

        # create members
        self.member_a = dataset_test_utils.create_dataset_member(dataset=self.dataset)
        self.member_b = dataset_test_utils.create_dataset_member(dataset=self.dataset)

    def test_get_dataset_files(self):
        """Tests retrieving dataset files for a dataset, parameter, member, etc
        """

        src_file_a = ScaleFile.objects.create(file_name='input_a.json', file_type='SOURCE', media_type='application/json',
                                              file_size=10, data_type='type', file_path='the_path',
                                              workspace=self.workspace)
        src_file_b = ScaleFile.objects.create(file_name='input_b.json', file_type='SOURCE', media_type='application/json',
                                              file_size=10, data_type='type', file_path='the_path',
                                              workspace=self.workspace)
        file_a = DataSet.objects.add_dataset_files(self.dataset.id, 'param_a', [src_file_a])[0]
        file_b = DataSet.objects.add_dataset_files(self.dataset.id, 'param_b', [src_file_b])[0]

        # Get files by dataset
        files = DataSet.objects.get_dataset_files(dataset_id=self.dataset.id)
        self.assertTrue(len(files), 2)

        # Get files by member
        # files = DataSet.objects.get_dataset_files(dataset_member)

        # Get files by parameter?