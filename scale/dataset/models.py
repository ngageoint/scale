"""Defines the database models for datasets""" 
from __future__ import absolute_import, unicode_literals

import logging
import django.contrib.postgres.fields
from django.db import models

from storage.models import ScaleFile
from dataset import convert_definition_to_v6_json, DataSetDefinition
from util import rest as rest_utils

"""
From #1067

We need to create the concept of data sets: a collection of n bundles of data. 
Each data set will have a defined set of parameters (like job type input) and 
then n members that match the parameter definition.

I think it might make sense to put this in its own app, perhaps called data? 
This app can store things related to defining and validating data sets and 
inputs.
"""

logger = logging.getLogger(__name__)


class DataSetManager(models.Manager):
    """Provides additional methods for handling datasets"""
    
    def create_dataset_v6(self, title=None, description=None, definition=None):
        """Creates and returns a new dataset for the given title/description/definition
        
        :param title: Optional title of the dataset
        :type title:
        :param description: Optional description of the dataset
        :type description:
        :param definition: Parameter definition of the dataset
        :type definition:
        """
        
        dataset = DataSet(title=title, description=description, definition=definition)
        
    def filter_datasets(self, created_time=None, dataset_ids=None, dataset_names=None, order=None):
        """Returns a query for dataset models that filters on the given fields
        
        :param created: Query datsets created at this time
        :type created: :class:`datetime.datetime`
        :param dataset_ids: Query datasets assciated with the given id(s)
        :type dataset_ids: list
        :param dataset_names: Query datasets assciated with the given name(s)
        :type dataset_names: list
        :param order: A list of fields to control the sort order.
        :type order: list
        :returns: The dataset query
        :rtype: :class:`django.db.models.QuerySet`
        """
        
        # Fetch a list of the datasets
        datasets = self.all()
        
        # Apply time range filtering
        if created_time:
            datasets = datasets.filter(created_time__gte=created_time)
            
        # Apply additional filters
        if dataset_ids:
            datasets = datasets.filter(dataset_ids__in=dataset_ids)
        if dataset_names:
            datasets = datasets.filter(data_set_name__in=dataset_names)
        
        # Apply sorting
        if order:
            datasets = datasets.order_by(*order)
        else:
            datasets = datasets.order_by('last_modified')

        return datasets
        
    def filter_datasets_related_v6(self, created_time=None, dataset_ids=None, dataset_names=None, order=None):
        """Returns a query for dataset models that filters on the given field. The returned query includes the related
        datset, datsetdefinition
        
        :param created_time: The created time of the datase
        :type created_time: :class:`datetime.datetime`
        :param dataset_ids: Query datasets associated with the identifier
        :type dataset_ids: [int]
        :param dataset_names: Query datasets associated with the name
        :type dataset_names: [string]
        :param order: A list of fields to control the sort order
        :type order: [string]
        """
        
        datasets = self.filter_datasets(created_time=created_time, dataset_ids=dataset_ids, dataset_names=dataset_names, order=order)
        datasets = datasets.select_related('')
        datasets = datasets.defer()

        return datasets
        
    def get_details(self, dataset_id):
        """Gets additional dtails for the given dataset model based on related model attributes.
        
        
        """
        
    def get_datasets_v6(self, created_time=None, dataset_ids=None, dataset_names=None, order=None):
        return self.filter_datasets_related_v6(order=order)
        
"""DataSet

* optional title
* optional description
* JSON definition (like job type input) (Required)
* created time
"""
class DataSet(models.Model):
    """
    Represents a DataSet object
    
    :keyword title: The human-readable title of this dataset (optional)
    :type title: :class:`django.db.models.CharField`
    :keyword name: The identifying name of the dataset used by clients for queries
    :type name: :class:`django.db.models.CharField`
    :keyword version: The version of the dataset
    :type version: :class:`django.db.models.CharField`
    :keyword version_array: The version of the dataset split into SemVer integer components (major,minor,patch,prerelease)
    :type version_array: list
    :keyword description: The description of the dataset (optional)
    :type description: :class:`django.db.models.CharField`
    :keyword created_time: Defines the created time of the dataset
    :type created_time: :class:`django.db.models.DateTimeField`
    :keyword definition: Defines the dataset
    :type definition: class:`django.contrib.postgres.fields.JSONField`
    """
    
    title = models.CharField(blank=True, max_length=50, null=True)
    name = models.CharField(db_index=True, max_length=50)
    version = models.CharField(db_index=True, max_length=50)
    version_array = django.contrib.postgres.fields.ArrayField(models.IntegerField(null=True),default=list([None]*4),size=4)
    created_time = models.DateTimeField('data.dataset')
    description = models.CharField('data.dataset')
    definition = django.contrib.postgres.fields.JSONField(default=dict)
    # parameters
    
    objects = DataSetManager()
        
    def get_dataset_definition(self):
        """Returns the dataset definition
        """
        if isinstance(self.definition, basestring):
            self.definition = {}
        return DataSetDefinition(self.definition, do_validate=False)
        
    def get_v6_definition_json(self):
        """Returns the dataset definition in v6 of the JSON schema
        
        :returns: The dataset definition in v6 of the JSON schema
        :rtype: dict
        """
        
        return rest_utils.strip_schema_version(convert_definition_to_v6_json(self.get_dataset_definition()).get_dict())
        
    def get_datasets(self, started, ended, names, categories)

"""
DataSetMember

Is this actually necessary?? Nothing else references datasetmember. datasetfile can 
refer back to the dataset id it's located in

* indexed foreign key to DataSet
* JSON field describing data in this member, must validate with DataSet definition (like job data/input)
* created time
"""
class DataSetMember(models.Model):
    """
    Defines the data of a dataset?
    contains list/descriptors of DataFiles
    
    :keyword dataset: indexed foreign key to DataSet
    :type dataset: :class:`django.db.models.ForeignKey`
    :keyword data: JSON description of the data in this DataSetMember. 
    :type data: :class: `django.contrib.postgres.fields.JSONField(default=dict)
    """
    
    dataset = models.ForeignKey('data.DataSet', on_delete=models.PROTECT)
    data = django.contrib.postgres.fields.JSONField(default=dict)

"""
DataSetFile

* indexed foreign key to DataSet
* index foreign key to Scale file
* char field for file parameter name (from data set definition JSON)
* unique combined index on (DataSet ID, Scale file ID) ??
"""
class DataSetFile(object):
    """
    The actual file in a dataset member
    
    :keyword dataset: Refers to the dataset the file is a member of
    :type dataset: :class:`django.db.models.ForeignKey`
    :keyword scale_file: Refers to the ScaleFile 
    :type scale_file: :class:`django.db.models.ForeignKey`
    :keyword parameter_name: Refers to the File parameter name
    :type parameter_name: :class:`django.db.models.CharField`
    """
    
    dataset = models.ForeignKey('data.DataSet', on_delete=models.PROTECT)
    scale_file = models.ForeignKey('storage.models.ScaleFile', on_delete=models.PROTECT)
    parameter_name = models.CharField(db_index=True, max_length=50)
