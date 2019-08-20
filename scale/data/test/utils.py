"""Defines utility methods for testing datasets"""
from __future__ import unicode_literals
from __future__ import absolute_import

from data.data.json.data_v6 import DataV6

from data.models import DataSet, DataSetMember
from data.dataset.dataset import DataSetDefinition

DATASET_TITLE_COUNTER = 1

DATA_DEFINITION = {'files': {'input_e': [1234], 'input_f': [1235, 1236]},
                   'json': {'input_g': 999, 'input_h': {'greeting': 'hello'}}}

DATASET_DEFINITION = {'global_data': {'files': {'input_a': [1234], 'input_b': [1235, 1236]},
                                      'json':  {'input_c': 999, 'input_d': {'greeting': 'hello'}}},
                      'global_parameters': {
                          'files': [
                            {'name': 'input_a', },
                            {'name': 'input_b', 'media_types': ['application/json'], 'required': False, 'multiple': True}],
                          'json':  [
                            {'name': 'input_c', 'type': 'integer'},
                            {'name': 'input_d', 'type': 'object', 'required': False}]},
                      'parameters': {
                          'files': [
                            {'name': 'input_e'},
                            {'name': 'input_f', 'media_types': ['application/json'], 'required': False, 'multiple': True}],
                          'json':  [
                            {'name': 'input_g', 'type': 'integer'},
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
    :rtype: :class:`data.models.DataSet`
    """

    if not title:
        global DATASET_TITLE_COUNTER
        title = 'Test Dataset %i' % DATASET_TITLE_COUNTER

    if not definition:
        definition = {
            'parameters': {'files': [], 'json': []}
        }
    definition_obj = DataSetDefinition(definition=definition)

    dataset = DataSet.objects.create_dataset_v6(title=title, description=description,
        definition=definition_obj)
    return dataset

def create_dataset_members(dataset=None, data_list=None):
    """Creates a datasetmember model

    :keyword dataset: The dataset the members are a part of
    :type dataset: :class:`data.models.DataSet`
    :keyword data_list: The data for the members
    :type data_list: [dict]
    """
    if not dataset:
        dataset = create_dataset()

    if not data_list:
        data_list = [{
            'version': '7',
            'files': {},
            'json': {'input_c': 999, 'input_d': {'greeting': 'hello'}}
        }]
    data_objs = []
    for d in data_list:
        data_objs.append(DataV6(data=d).get_data())

    dataset_members = DataSetMember.objects.create_dataset_members(dataset=dataset, data_list=data_objs)
    return dataset_members
