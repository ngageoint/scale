"""Defines utility methods for testing datasets"""
from __future__ import unicode_literals
from __future__ import absolute_import

from dataset.models import DataSet

COMPLETE_DATASET = {
    
}

MINIMUM_DATASET = {
    
}

def create_dataset(name=None, title=None, description=None, version=None, 
    created_time=None, definition=None):
    """Creates a dataset model for unit testing
    
    :returns: The dataset model
    :rtype: :class:`dataset.models.DataSet`
    """
    
    if not definition:
        definition = {}
        
    dataset = DataSet.objects.create_dataset(name=name, title=title, description=description,
        created_time=created_time, version=version, definition=definition)
    
    return dataset