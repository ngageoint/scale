"""Defines utility methods for testing datasets"""
from __future__ import unicode_literals
from __future__ import absolute_import

from datetime import datetime

from dataset.models import DataSet
from dataset.definition.definition import DataSetDefinition

DATASET_NAME_COUNTER = 1
DATASET_VERSION_COUNTER = 1

COMPLETE_DATASET = {

}

MINIMUM_DATASET = {

}

def create_dataset(name=None, title=None, description=None, version=None,
    created=None, definition=None):
    """Creates a dataset model for unit testing

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

def create_dataset_member(dataset=None, definition=None):
    """Creates a datasetmember model"""
