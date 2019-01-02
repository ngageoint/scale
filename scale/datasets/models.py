# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import django.contrib.postgres.fields
from django.db import models

# Create your models here.
"""
From #1067

We need to create the concept of data sets, a collection of n bundles of data. 
Each data set will have a defined set of parameters (like job type input) and 
then n members that match the parameter definition.

I think it might make sense to put this in its own app, perhaps called data? 
This app can store things related to defining and validating data sets and 
inputs.
"""


class DataSetManager(models.Manager):
    """Provides additional methods for handling datasets
    """
    
    def create_dataset_v6(self, dataset_definition=None):
        """Creates a new dataset for the given ???"""
        
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
        """
        """
        
        datasets = self.filter_datasets(created_time=created_time, dataset_ids=dataset_ids, dataset_names=dataset_names, order=order)
        datasets = datasets.select_related('')
        datasets = datasets.defer()

        return datasets
        
"""DataSet

* optional title
* optional description
* JSON definition (like job type input)
* created time
"""
class DataSet(models.Model):
    """
    Represents a DataSet object
    
    :keyword title: The human-readable title of this data set (optional)
    :type title: :class:`django.db.models.CharField`
    :keyword name: The identifying name of the data set used by clients for queries
    :type name: :class:`django.db.models.CharField`
    :keyword version: The version of the data set
    :type version: :class:`django.db.models.CharField`
    :keyword version_array: The version of the data set split into SemVer integer components (major,minor,patch,prerelease)
    :type version_array: list
    
    :keyword description: The description of the data set (optional)
    :type description: :class:`django.db.models.CharField`
    :keyword created_time: Defines the created time of the DataSet
    :type created_time: :class:`django.db.models.DateTimeField`
    :keyword definition: Defines the DataSet
    :type definition: class:`django.contrib.postgres.fields.JSONField`
    """
    
    title = models.CharField(blank=True, max_length=50, null=True)
    name = models.CharField(db_index=True, max_length=50)
    version = models.CharField(db_index=True, max_length=50)
    version_array = django.contrib.postgres.fields.ArrayField(models.IntegerField(null=True),default=list([None]*4),size=4)
    created_time = models.DateTimeField('data.dataset')
    description = models.CharField('data.dataset')
    definition = django.contrib.postgres.fields.JSONField(default=dict)
        
    def get_dataset_definition(self):
        if isinstance(self.definition, basestring):
            self.definition = {}
        return DataSetDefinition(self.definition, do_validate=False)
        
    def get_v6_definition_json(self):
        """Returns the dataset definition in v6 of the JSON schema
        
        :returns: The dataset definition in v6 of the JSON schema
        :rtype: dict
        """
        
        return rest_utils.strip_schema_version(convert_definition_to_v6_json(self.get_dataset_definition()).get_dict())

"""
DataSetMember

* indexed foreign key to DataSet
*JSON field describing data in this member, must validate with DataSet definition (like job data/input)
*created time
"""
class DataSetMember(models.Model):
    """
    Defines the data of a dataset?
    
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
* unique combined index on (DataSet ID, Scale file ID)
"""
class DataSetFile(object):
    """
    
    """
    