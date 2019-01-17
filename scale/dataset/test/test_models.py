from __future__ import unicode_literals
from __future__ import absolute_import

import copy
import datetime
import json
import time

import django
import django.utils.timezone as timezone
from django.test import TestCase, TransactionTestCase

from dataset.models import DataSet
import dataset.test.utils as dataset_test_utils
from dataset.definition.json.definition_v6 import DataSetDefinition

class TestDataSetManager(TransactionTestCase):

    def setUp(self):
        django.setup()

        self.definition = {
            'version': '6',
            'parameters': {
                'global-param': {
                    'param_type': {
                        'param_type': 'global',
                    },
                },
                'member-param': {
                    'param_type': {
                        'param_type': 'member',
                    },
                },
            },
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