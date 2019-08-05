"""Defines utility methods for testing datasets"""
from __future__ import unicode_literals
from __future__ import absolute_import

from datetime import datetime

import storage.test.utils as storage_utils
from data.data.json.data_v6 import DataV6

from dataset.models import DataSet, DataSetMember
from dataset.definition.definition import DataSetDefinition

DATASET_NAME_COUNTER = 1
DATASET_VERSION_COUNTER = 1

DATASET_MEMBER_NAME_COUNTER = 1

DATA_DEFINITION = {'version': '6', 'files': {'input_e': [1234], 'input_f': [1235, 1236]},
                                            'json': {'input_g': 999, 'input_h': {'greeting': 'hello'}}}

DATASET_DEFINITION = {'version': '6',
                      'global_data': {'version': '6', 'files': {'input_a': [1234], 'input_b': [1235, 1236]},
                                            'json': {'input_c': 999, 'input_d': {'greeting': 'hello'}}},
                      'global_parameters': {'version': '6', 'files': [{'name': 'input_a'},
                                                                {'name': 'input_b', 'media_types': ['application/json'],
                                                                 'required': False, 'multiple': True}],
                                      'json': [{'name': 'input_c', 'type': 'integer'},
                                               {'name': 'input_d', 'type': 'object', 'required': False}]},
                      'parameters': {'version': '6', 'files': [{'name': 'input_e'},
                                                               {'name': 'input_f', 'media_types': ['application/json'],
                                                                'required': False, 'multiple': True}],
                                     'json': [{'name': 'input_g', 'type': 'integer'},
                                              {'name': 'input_h', 'type': 'object', 'required': False}]}}

def create_dataset(name=None, title=None, description=None, version=None,
    created=None, definition=None):
    """Creates a dataset model for unit testing

    :keyword name: The name of the dataset
    :type name: string
    :keyword title: The title of the dataset
    :type title: string
    :keyword description: The description of the dataset
    :type description: string
    :keyword created: The created time of the dataset
    :type created: ??
    :returns: The dataset model
    :rtype: :class:`dataset.models.DataSet`
    """

    if not name:
        global DATASET_NAME_COUNTER
        name = 'test-dataset-%i' % DATASET_NAME_COUNTER

    if not created:
        created = datetime.now()
    if not definition:
        definition = {
            'parameters': [],
        }

    dataset = DataSet.objects.create(name=name, title=title, description=description,
        definition=definition, created=created)
    dataset.save()
    return dataset

def create_dataset_member(dataset=None, data=None, created=None):
    """Creates a datasetmember model

    :keyword dataset: The dataset the member is a part of
    :type dataset: :class:`dataset.models.DataSet`
    :keyword data: The member data
    :type data: dict
    """
    if not dataset:
        raise Exception('Cannot create dataset member without dataset')

    if not data:
        file = storage_utils.create_file()
        data_dict = {
            'version': '6',
            'files': {'input_a': [file.id]},
            'json': {'input_c': 999, 'input_d': {'hello'}}
        }
        data = DataV6(data=data).get_data()

    if not created:
        created=datetime.now()

    dataset_member = DataSetMember.objects.create(dataset=dataset, data=data, created=created)
    dataset_member.save()
    return dataset_member
