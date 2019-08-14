from __future__ import unicode_literals
from __future__ import absolute_import

import copy
import datetime
import json
import time

import django
from django.utils.timezone import now
from django.test import TestCase, TransactionTestCase

from data.data.json.data_v6 import DataV6
from data.interface.interface import Interface
from data.interface.parameter import FileParameter, JsonParameter
from dataset.exceptions import InvalidDataSetMember
from dataset.models import DataSet, DataSetMember, DataSetFile
import dataset.test.utils as dataset_test_utils
from dataset.definition.definition import DataSetDefinition
from dataset.definition.json.definition_v6 import DataSetDefinitionV6
from storage.models import ScaleFile, Workspace
import storage.test.utils as storage_test_utils

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

        title = 'Test Dataset'
        description = 'Test DataSet description'

        # call test
        dataset = DataSet.objects.create_dataset_v6(definition=self.dataset_definition, title=title, description=description)

        # Check results
        the_dataset = DataSet.objects.get(pk=dataset.id)
        self.assertEqual(the_dataset.title, title)
        self.assertDictEqual(the_dataset.definition, self.dataset_definition.get_dict())

    def test_filter_datasets(self):
        """Tests calling DataSetManager filter_datasets
        """

        today = now()
        yesterday = today - datetime.timedelta(days=1)
        tomorrow = today + datetime.timedelta(days=1)
        
        title1 = 'Test Dataset 1'
        description1 = 'Test DataSet description 1'

        dataset1 = DataSet.objects.create(definition=self.definition, title=title1, description=description1)
        DataSet.objects.filter(pk=dataset1.pk).update(created=yesterday)

        title2 = 'Key Test Dataset 2'
        description2 = 'Test DataSet description 2'

        dataset2 = DataSet.objects.create(definition=self.definition, title=title2, description=description2)
        DataSet.objects.filter(pk=dataset2.pk).update(created=today)

        title3 = 'Test Dataset 3'
        description3 = 'Key Test DataSet description 3'

        dataset3 = DataSet.objects.create(definition=self.definition, title=title3, description=description3)
        DataSet.objects.filter(pk=dataset3.pk).update(created=tomorrow)

        ids = [dataset1.id, dataset3.id]

        # Test the filter_datasets method
        datasets = DataSet.objects.filter_datasets(dataset_ids=ids)
        self.assertEqual(len(datasets), 2)
        for ds in datasets:
            self.assertTrue(ds.id in ids)
            self.assertNotEquals(ds.id, dataset2.id)

        datasets = DataSet.objects.filter_datasets(started=today)
        self.assertEqual(len(datasets), 2)
        self.assertEqual(datasets[0].title, title2)
        datasets = DataSet.objects.filter_datasets(ended=today, order=['-id'])
        self.assertEqual(len(datasets), 2)
        self.assertEqual(datasets[0].title, title2)
        datasets = DataSet.objects.filter_datasets(started=today, ended=today)
        self.assertEqual(len(datasets), 1)
        self.assertEqual(datasets[0].title, title2)
        
        datasets = DataSet.objects.filter_datasets(keywords=['key'])
        self.assertEqual(len(datasets), 2)
        self.assertEqual(datasets[0].title, title2)

    def test_get_datasets_v6(self):
        """Tests calling DataSetmanager.get_datasets_v6() """

        title = 'Test Dataset 1'
        description = 'Test DataSet description 1'

        dataset1 = DataSet.objects.create_dataset_v6(definition=self.dataset_definition, title=title, description=description)

        title = 'Test Dataset 2'
        description = 'Test DataSet description 2'
        dataset2 = DataSet.objects.create_dataset_v6(definition=self.dataset_definition, title=title, description=description)

        title = 'Test Dataset 3'
        description = 'Test DataSet description 3'

        dataset3 = DataSet.objects.create_dataset_v6(definition=self.dataset_definition, title=title, description=description)

        ids = [dataset1.id, dataset3.id]
        datasets = DataSet.objects.get_datasets_v6(dataset_ids=ids)
        self.assertEqual(len(datasets), 2)
        for ds in datasets:
            self.assertTrue(ds.id in ids)
            self.assertNotEquals(ds.id, dataset2.id)

    def test_get_details_v6(self):
        """Tests calling DataSetManager.get_dataset_details() """

        title = 'Test Dataset'
        description = 'Test DataSet description'

        # create object
        dataset = DataSet.objects.create_dataset_v6(definition=self.dataset_definition, title=title, description=description)
        dataset2 = DataSet.objects.get_details_v6(dataset.id)
        self.assertDictEqual(dataset.definition, dataset2.definition)

class TestDataSetMemberManager(TransactionTestCase):
    """Tests the DataSetMember class"""

    def setUp(self):
        django.setup()

        # create a dataset
        self.definition = copy.deepcopy(dataset_test_utils.DATASET_DEFINITION)

        self.file1 = storage_test_utils.create_file()
        self.file2 = storage_test_utils.create_file()
        self.file3 = storage_test_utils.create_file()
        self.file4 = storage_test_utils.create_file()
        self.file5 = storage_test_utils.create_file()
        self.file6 = storage_test_utils.create_file()

        self.dataset = dataset_test_utils.create_dataset(definition=self.definition)


    def test_create_dataset_member_v6(self):
        """Tests calling DataSetManager.create_dataset_member_v6() """

        data_dict = copy.deepcopy(dataset_test_utils.DATA_DEFINITION)
        data_dict['files']['input_e'] = [self.file1.id]
        data_dict['files']['input_f'] = [self.file2.id, self.file3.id]
        data = DataV6(data=data_dict).get_data()

        # call test
        dataset_member = DataSetMember.objects.create_dataset_member_v6(dataset=self.dataset, data=data)

        # Check results
        the_dataset_member = DataSetMember.objects.get(pk=dataset_member.id)
        self.assertDictEqual(the_dataset_member.data, data_dict)
        
        data_dict = copy.deepcopy(dataset_test_utils.DATA_DEFINITION)
        del data_dict['files']['input_e']
        data = DataV6(data=data_dict).get_data()

        # call test
        with self.assertRaises(InvalidDataSetMember) as context:
            dataset_member = DataSetMember.objects.create_dataset_member_v6(dataset=self.dataset, data=data)
        self.assertEqual(context.exception.error.name, 'INVALID_DATASET_MEMBER')
        
    def test_get_dataset_members_v6(self):
        """Tests calling DataSetMemberManager get_dataset_members"""

        # Add some members
        data1 = copy.deepcopy(dataset_test_utils.DATA_DEFINITION)
        data1['files']['input_e'] = [self.file1.id]
        data1['files']['input_f'] = [self.file2.id, self.file3.id]

        member_1 = dataset_test_utils.create_dataset_member(dataset=self.dataset, data=data1)

        data2 = copy.deepcopy(dataset_test_utils.DATA_DEFINITION)
        data2['files']['input_e'] = [self.file4.id]
        data2['files']['input_f'] = [self.file5.id, self.file6.id]

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
            self.assertDictEqual(member.get_v6_data_json(), expected.get_v6_data_json())

class TestDataSetFile(TransactionTestCase):
    """Tests the DataSetFileManager class"""

    def setUp(self):
        django.setup()

        # create a workspace and files
        self.workspace = storage_test_utils.create_workspace(name='Test Workspace', is_active=True)
                                                  
        self.file1 = storage_test_utils.create_file(file_name='input_e.json', file_type='SOURCE', media_type='application/json',
                                              file_size=10, data_type_tags=['type'], file_path='the_path',
                                              workspace=self.workspace)
        self.file2 = storage_test_utils.create_file(file_name='input_f.json', file_type='SOURCE', media_type='application/json',
                                              file_size=10, data_type_tags=['type'], file_path='the_path',
                                              workspace=self.workspace)
        self.file3 = storage_test_utils.create_file(file_name='input_f2.json', file_type='SOURCE', media_type='application/json',
                                              file_size=10, data_type_tags=['type'], file_path='the_path',
                                              workspace=self.workspace)
        self.file4 = storage_test_utils.create_file(file_name='input_eb.json', file_type='SOURCE', media_type='application/json',
                                              file_size=10, data_type_tags=['type'], file_path='the_path',
                                              workspace=self.workspace)
        self.file5 = storage_test_utils.create_file(file_name='input_fb.json', file_type='SOURCE', media_type='application/json',
                                              file_size=10, data_type_tags=['type'], file_path='the_path',
                                              workspace=self.workspace)
        self.file6 = storage_test_utils.create_file(file_name='input_fb2.json', file_type='SOURCE', media_type='application/json',
                                              file_size=10, data_type_tags=['type'], file_path='the_path',
                                              workspace=self.workspace)
                                              
        # create a dataset
        self.dataset = dataset_test_utils.create_dataset(definition=copy.deepcopy(dataset_test_utils.DATASET_DEFINITION))
        self.dataset2 = dataset_test_utils.create_dataset(definition=copy.deepcopy(dataset_test_utils.DATASET_DEFINITION))
        
        # create dataset members
        data1 = copy.deepcopy(dataset_test_utils.DATA_DEFINITION)
        data1['files']['input_e'] = [self.file1.id]
        data1['files']['input_f'] = [self.file2.id, self.file3.id]

        self.member_1 = dataset_test_utils.create_dataset_member(dataset=self.dataset, data=data1)

        data2 = copy.deepcopy(dataset_test_utils.DATA_DEFINITION)
        data2['files']['input_e'] = [self.file4.id]
        data2['files']['input_f'] = [self.file5.id, self.file6.id]
        
        self.member_2 = dataset_test_utils.create_dataset_member(dataset=self.dataset, data=data2)

        self.member_3 = dataset_test_utils.create_dataset_member(dataset=self.dataset2, data=data1)

    def test_get_dataset_files(self):
        """Tests retrieving dataset files for a dataset
        """

        # Get files by dataset
        files = DataSet.objects.get_dataset_files(dataset_id=self.dataset.id)
        self.assertEqual(len(files), 6)

    def test_get_files(self):
        """Tests retrieving files for datasets
        """

        files = DataSetFile.objects.get_files(dataset_ids=[self.dataset.id], parameter_names=['input_e'])
        self.assertEqual(len(files), 2)

        files = DataSetFile.objects.get_files(dataset_ids=[self.dataset.id, self.dataset2.id])
        self.assertEqual(len(files), 9)

        files = DataSetFile.objects.get_files(dataset_ids=[self.dataset.id, self.dataset2.id], parameter_names=['input_e'])
        self.assertEqual(len(files), 3)

        files = DataSetFile.objects.get_files(dataset_ids=[self.dataset.id], parameter_names=['input_a'])
        self.assertEqual(len(files), 0)

    def test_get_datasets(self):
        """Tests retrieving datasets for given files
        """
        datasets = DataSetFile.objects.get_datasets(file_ids=[self.file2.id, self.file3.id])
        self.assertEqual(len(datasets), 2)

        datasets = DataSetFile.objects.get_datasets(file_ids=[self.file2.id, self.file3.id, self.file4.id])
        self.assertEqual(len(datasets), 2)

        datasets = DataSetFile.objects.get_datasets(file_ids=[self.file2.id, self.file3.id, self.file4.id], all_files=True)
        self.assertEqual(len(datasets), 1)