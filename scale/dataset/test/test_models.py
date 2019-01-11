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

        definition = {}
        self.dataset_definition = DataSetDefinition(definition)

    def test_create_dataset(self):
        """Tests calling DataSet.create() """

        name = 'test-dataset'
        title = 'Test Dataset'
        description = 'Test DataSet description'
        version = '1.0.0'
        definition = {}

        # call test
        dataset = dataset_test_utils.create_dataset(name=name, title=title, description=description,
            version=version, definition=definition)

        # Check results
        the_dataset = DataSet.objects.get(pk=dataset.id)
        self.assertEqual(the_dataset.name, name)
        self.assertEqual(the_dataset.title, title)
        self.assertEqual(the_dataset.version, version)
        self.assertDictEqual(the_dataset.definition, definition)

    def test_create_dataset_v6(self):
        """Tests calling DataSetManager.create_dataset_v6() """

        name = 'test-dataset'
        title = 'Test Dataset'
        description = 'Test DataSet description'
        version = '1.0.0'
        definition = {}

        # call test
        dataset = DataSet.objects.create_dataset_v6(version, definition, name=name, title=title, description=description)

        # Check results
        the_dataset = DataSet.objects.get(pk=dataset.id)
        self.assertEqual(the_dataset.name, name)
        self.assertEqual(the_dataset.title, title)
        self.assertEqual(the_dataset.version, version)
        self.assertDictEqual(the_dataset.definition, definition)

    def test_filter_datasets(self):
        """Tests calling DataSetManager filter_datasets
        """

        pass

    def test_filter_datasets_related_v6(self):
        """Tests calling DataSetManager.filter_datasets_related() """

        pass

    def test_get_datasets_v6(self):
        """Tests calling DataSetmanager.get_datasets_v6() """

        pass

    def test_get_dataset_details(self):
        """Tests calling DataSetManager.get_dataset_details() """

        pass

#class TestDataSet(TransactionTestCase):

#    def setUp(self):
#        django.setup()

        # dataset_def_str = \
        #     """
        #     """

