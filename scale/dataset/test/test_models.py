from __future__ import unicode_literals
from __future__ import absolute_import

import copy
import datetime
import json
import time

import django
import django.utils.timezone as timezone
from django.test import TestCase, TransactionTestCase

class TestDataSetManager(TransactionTestCase):

    def setUp(self):
        django.setup()

    def test_create_dataset_v6(self):
        """Tests calling DataSetManager.create_dataset_v6() """

    def test_filter_datasets(self):
        """Tests calling DataSetManager.filterdatasets """

    def test_filter_datasets_related_v6(self):
        """Tests calling DataSetManager.filter_datasets_related() """
        
    def test_get_datasets_v6(self):
        """Tests calling DataSetmanager.get_datasets_v6() """
        
    def test_get_dataset_details(self):
        """Tests calling DataSetManager.get_dataset_details() """
        
class TestDataSet(TransactionTestCase):

    def setUp(self):
        django.setup()
        
        dataset_def_str = \
            """
            """
        
