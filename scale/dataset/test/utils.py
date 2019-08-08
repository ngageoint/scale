"""Defines utility methods for testing datasets"""
from __future__ import unicode_literals
from __future__ import absolute_import

from datetime import datetime

import storage.test.utils as storage_utils
from data.data.json.data_v6 import DataV6

from dataset.models import DataSet, DataSetMember
from dataset.definition.definition import DataSetDefinition

DATASET_TITLE_COUNTER = 1

DATA_DEFINITION = {'files': {'input_e': [1234], 'input_f': [1235, 1236]},
                                            'json': {'input_g': 999, 'input_h': {'greeting': 'hello'}}}

DATASET_DEFINITION = {'global_data': {'files': {'input_a': [1234], 'input_b': [1235, 1236]},
                                            'json': {'input_c': 999, 'input_d': {'greeting': 'hello'}}},
                      'global_parameters': {'files': [{'name': 'input_a', },
                                                                {'name': 'input_b', 'media_types': ['application/json'],
                                                                 'required': False, 'multiple': True}],
                                      'json': [{'name': 'input_c', 'type': 'integer'},
                                               {'name': 'input_d', 'type': 'object', 'required': False}]},
                      'parameters': {'files': [{'name': 'input_e'},
                                                               {'name': 'input_f', 'media_types': ['application/json'],
                                                                'required': False, 'multiple': True}],
                                     'json': [{'name': 'input_g', 'type': 'integer'},
                                              {'name': 'input_h', 'type': 'object', 'required': False}]}}

def create_dataset(title=None, description=None, created=None, definition=None):
    """Creates a dataset model for unit testing

    :keyword title: The title of the dataset
    :type title: string
    :keyword description: The description of the dataset
    :type description: string
    :keyword created: The created time of the dataset
    :type created: :class: 'datetime'
    :keyword definition: The dataset definition
    :type definition: dict
    :returns: The dataset model
    :rtype: :class:`dataset.models.DataSet`
    """

    if not title:
        global DATASET_TITLE_COUNTER
        title = 'Test Dataset %i' % DATASET_TITLE_COUNTER

    if not definition:
        definition = {
            'parameters': {'files': [], 'json': []}
        }

    dataset = DataSet.objects.create_dataset_v6(title=title, description=description,
        definition=definition)
    return dataset

def create_dataset_member(dataset=None, data=None):
    """Creates a datasetmember model

    :keyword dataset: The dataset the member is a part of
    :type dataset: :class:`dataset.models.DataSet`
    :keyword data: The member data
    :type data: :class:'data.data.data.Data'
    """
    if not dataset:
        dataset = create_dataset()

    if not data:
        data = {
            'version': '7',
            'files': {},
            'json': {'input_c': 999, 'input_d': {'greeting': 'hello'}}
        }

    dataset_member = DataSetMember.objects.create(dataset=dataset, data=data)
    return dataset_member
