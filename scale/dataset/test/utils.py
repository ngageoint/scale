"""Defines utility methods for testing datasets"""
from __future__ import unicode_literals
from __future__ import absolute_import

from datetime import datetime


from dataset.models import DataSet, DataSetMember
from dataset.definition.definition import DataSetDefinition

DATASET_NAME_COUNTER = 1
DATASET_VERSION_COUNTER = 1

DATASET_MEMBER_NAME_COUNTER = 1

COMPLETE_DATASET_DEF = {


}

MINIMUM_DATASET = {

}

def create_dataset(name=None, title=None, description=None, version=None,
    created=None, definition=None):
    """Creates a dataset model for unit testing

    :keyword name: The name of the dataset
    :type name: string
    :keyword title: The title of the dataset
    :type title: string
    :keyword description: The description of the dataset
    :type description: string
    :keyword version: The version of the dataset
    :type version: string
    :keyword created: The created time of the dataset
    :type created: ??
    :returns: The dataset model
    :rtype: :class:`dataset.models.DataSet`
    """

    if not name:
        global DATASET_NAME_COUNTER
        name = 'test-dataset-%i' % DATASET_NAME_COUNTER
    if not version:
        global DATASET_VERSION_COUNTER
        version = '%i.0.0' % DATASET_VERSION_COUNTER

    if not created:
        created = datetime.now()
    if not definition:
        definition = {
            'parameters': [],
        }

    dataset = DataSet.objects.create(name=name, title=title, description=description,
        version=version, definition=definition, created=created)
    dataset.save()
    return dataset

def create_dataset_member(dataset=None, definition=None, created=None):
    """Creates a datasetmember model

    :keyword dataset: The dataset the member is a part of
    :type dataset: :class:`dataset.models.DataSet`
    :keyword definition: The member definition
    :type definition: dict
    """
    if not dataset:
        raise Exception('Cannot create dataset member without dataset')

    if not definition:
        global DATASET_MEMBER_NAME_COUNTER
        definition = {
            'name': 'test-datset-member-%i' % DATASET_MEMBER_NAME_COUNTER,
            'input': {
                'version': '6',
                'files': [],
                'json': [],
            },
        }

    if not created:
        created=datetime.now()

    dataset_member = DataSetMember.objects.create(dataset=dataset, definition=definition, created=created)
    dataset_member.save()
    return dataset_member
