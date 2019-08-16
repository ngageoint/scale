"""Defines the database models for datasets"""
from __future__ import absolute_import, unicode_literals

import copy
import logging
from collections import namedtuple

import django.contrib.postgres.fields
from django.db import models, transaction
from django.db.models import Q, Count

from data.data import data_util
from data.data.json.data_v6 import convert_data_to_v6_json, DataV6
from data.data.exceptions import InvalidData
from data.data.value import FileValue
from dataset.definition.definition import DataSetDefinition
from dataset.definition.json.definition_v6 import convert_definition_to_v6_json, DataSetDefinitionV6
from dataset.exceptions import InvalidDataSetDefinition, InvalidDataSetMember
from dataset.dataset_serializers import DataSetFileSerializerV6, DataSetMemberSerializerV6
from storage.models import ScaleFile
from util import rest as rest_utils

logger = logging.getLogger(__name__)

DataSetValidation = namedtuple('DataSetValidation', ['is_valid', 'errors', 'warnings'])
# DataSetKey = namedtuple('DataSetKey', ['name', 'version'])

class DataSetManager(models.Manager):
    """Provides additional methods for handling datasets"""

    def create_dataset_v6(self, definition, title=None, description=None):
        """Creates and returns a new dataset for the given name/title/description/definition/version??

        :param definition: Parameter definition of the dataset
        :type definition: :class:`dataset.definition.definition.DataSetDefinition`
        :param title: Optional title of the dataset
        :type title: string
        :param description: Optional description of the dataset
        :type description: string

        :returns: The new dataset
        :rtype: :class:`dataset.models.DataSet`

        :raises :class:`dataset.exceptions.InvalidDataSet`: If a give dataset has an invalid value
        """

        if not definition:
            definition = DataSetDefinition(definition={})

        dataset = DataSet()

        dataset.title = title
        dataset.description = description
        dataset.definition = definition.get_dict()

        dataset.save()

        return dataset

    def get_details_v6(self, dataset_id):
        """Gets additional details for the given dataset id

        :returns: The full dataset for the given id
        :rtype: :class:`dataset.models.DataSet`
        """

        ds = DataSet.objects.get(pk=dataset_id)
        ds.files = DataSetFile.objects.get_dataset_files(ds.id)
        return ds

    def get_datasets_v6(self, started=None, ended=None, dataset_ids=None, keywords=None, order=None):
        """Handles retrieving datasets - possibly filtered and ordered

        :returns: The list of datasets that match the given filters
        :rtype: [:class:`dataset.models.DataSet`]
        """
        return self.filter_datasets(started=started, ended=ended, dataset_ids=dataset_ids, keywords=keywords, order=order)

    def filter_datasets(self, started=None, ended=None, dataset_ids=None, keywords=None, order=None):
        """Returns a query for dataset models that filters on the given fields

        :param started: Query datasets created after this amount of time.
        :type started: :class:`datetime.datetime`
        :param ended: Query datasets created before this amount of time.
        :type ended: :class:`datetime.datetime`
        :param dataset_ids: Query datasets assciated with the given id(s)
        :type dataset_ids: list
        :param keywords: Query datasets with title or description matching one of the specified keywords
        :type keywords: list
        :param order: A list of fields to control the sort order.
        :type order: list
        :returns: The dataset query
        :rtype: :class:`django.db.models.QuerySet`
        """

        # Fetch a list of the datasets
        datasets = self.all()

        # Apply time range filtering
        if started:
            datasets = datasets.filter(created__gte=started)
        if ended:
            datasets = datasets.filter(created__lte=ended)

        # Apply additional filters
        if dataset_ids:
            datasets = datasets.filter(id__in=dataset_ids)

        # Execute a sub-query that returns distinct job type names that match the provided filter arguments
        if keywords:
            key_query = Q()
            for keyword in keywords:
                key_query |= Q(title__icontains=keyword)
                key_query |= Q(description__icontains=keyword)
            datasets = datasets.filter(key_query)

        # Apply sorting
        if order:
            datasets = datasets.order_by(*order)
        else:
            datasets = datasets.order_by('id')

        for ds in datasets:
            files = DataSetFile.objects.get_file_ids(dataset_ids=[ds.id])
            ds.files = len(files)
        return datasets

    def validate_dataset_v6(self, definition, title=None, description=None):
        """Validates the given dataset definiton

        :param definition: The dataset definition
        :type definition: dict
        :returns: The dataset validation
        :rtype: :class:`datset.models.DataSetValidation`
        """

        is_valid = True
        errors = []
        warnings = []

        dataset_definition = None
        try:
            dataset_definition = DataSetDefinitionV6(definition=definition, do_validate=True)
        except InvalidDataSetDefinition as ex:
            is_valid = False
            errors.append(ex.error)
            message = 'Dataset definition is invalid: %s' % ex
            logger.info(message)
            pass

        # validate other fields
        return DataSetValidation(is_valid, errors, warnings)

    def get_dataset_files(self, dataset_id):
        """Returns the files associated with the given dataset

        :returns: The list of DataSetFiles matching the file_id
        :rtype: [:class:`dataset.models.DataSetFile`]
        """

        files = DataSetFile.objects.get_dataset_files(dataset_id=dataset_id)
        return files

    def get_dataset_members(self, dataset_id):
        """Returns the members associated with the given dataset_id
        :returns: The list of DataSetMembers
        :rtype: [:clas:`dataset.models.DataSetMember`]
        """
        dataset = self.get(pk=dataset_id)
        members = DataSetMember.objects.all().filter(dataset=dataset)
        return members


class DataSet(models.Model):
    """
    Represents a DataSet object

    :keyword name: The identifying name of the dataset used by clients for queries
    :type name: :class:`django.db.models.CharField`
    :keyword version: The version of the dataset
    :type version: :class:`django.db.models.CharField`
    :keyword version_array: The version of the dataset split into SemVer integer components (major,minor,patch,prerelease)
    :type version_array: list
    :keyword title: The human-readable title of this dataset (optional)
    :type title: :class:`django.db.models.CharField`
    :keyword description: The description of the dataset (optional)
    :type description: :class:`django.db.models.CharField`
    :keyword created: Defines the created time of the dataset
    :type created: :class:`django.db.models.DateTimeField`
    :keyword definition: Defines the dataset
    :type definition: class:`django.contrib.postgres.fields.JSONField`
    """

    title = models.CharField(blank=True, max_length=50, null=True)
    description = models.TextField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    definition = django.contrib.postgres.fields.JSONField(default=dict)

    objects = DataSetManager()

    def get_definition(self):
        """Returns the dataset definition

        :returns: The DataSet definition
        :rtype: :class:`dataset.definition.DataSetDefinition`
        """

        if isinstance(self.definition, basestring):
            self.definition = {}
        return DataSetDefinitionV6(definition=self.definition).get_definition()

    def get_v6_definition_json(self):
        """Returns the dataset definition in v6 of the JSON schema

        :returns: The dataset definition in v6 of the JSON schema
        :rtype: dict
        """

        return rest_utils.strip_schema_version(convert_definition_to_v6_json(self.get_definition()).get_dict())

    def get_dataset_definition(self):
        """Returns the dataset definition

        :returns: The dataset definition json
        :rtype: dict
        """

        return self.definition

    def get_dataset_members_json(self):
        """Returns the JSON for the associated dataset members

        :returns: Returns the outgoing primitive representation.
        :rtype: dict?
        """
        members = DataSet.objects.get_dataset_members(dataset_id=self.id)
        serializer = DataSetMemberSerializerV6(members, many=True)
        return serializer.data

    def get_dataset_files_json(self):
        """Returns the JSON for the associated dataset files

        :returns: Returns the outgoing primitive representation.
        :rtype: dict?
        """
        files = DataSet.objects.get_dataset_files(self.id)
        serializer = DataSetFileSerializerV6(files, many=True)
        return serializer.data

    class Meta(object):
        """meta information for the db"""
        db_table = 'data_set'

class DataSetMemberManager(models.Manager):
    """Provides additional methods for handling dataset members"""

    def build_data_list(self, template, data_started=None, data_ended=None, source_started=None, source_ended=None,
                        source_sensor_classes=None, source_sensors=None, source_collections=None,
                        source_tasks=None, mod_started=None, mod_ended=None, job_type_ids=None, job_type_names=None,
                        job_ids=None, is_published=None, is_superseded=None, file_names=None, job_outputs=None,
                        recipe_ids=None, recipe_type_ids=None, recipe_nodes=None, batch_ids=None, order=None):
        """Builds a list of data dictionaries from a template and file filters

        :param template: The template to fill with files found through filters
        :type template: dict
        :param data_started: Query files where data started after this time.
        :type data_started: :class:`datetime.datetime`
        :param data_ended: Query files where data ended before this time.
        :type data_ended: :class:`datetime.datetime`
        :param source_started: Query files where source collection started after this time.
        :type source_started: :class:`datetime.datetime`
        :param source_ended: Query files where source collection ended before this time.
        :type source_ended: :class:`datetime.datetime`
        :param source_sensor_classes: Query files with the given source sensor class.
        :type source_sensor_classes: list
        :param source_sensor: Query files with the given source sensor.
        :type source_sensor: list
        :param source_collection: Query files with the given source class.
        :type source_collection: list
        :param source_tasks: Query files with the given source tasks.
        :type source_tasks: list
        :param mod_started: Query files where the last modified date is after this time.
        :type mod_started: :class:`datetime.datetime`
        :param mod_ended: Query files where the last modified date is before this time.
        :type mod_ended: :class:`datetime.datetime`
        :param job_type_ids: Query files with jobs with the given type identifier.
        :type job_type_ids: list
        :param job_type_names: Query files with jobs with the given type name.
        :type job_type_names: list
        :keyword job_ids: Query files with a given job id
        :type job_ids: list
        :param is_published: Query files flagged as currently exposed for publication.
        :type is_published: bool
        :param is_superseded: Query files that have/have not been superseded.
        :type is_superseded: bool
        :param file_names: Query files with the given file names.
        :type file_names: list
        :keyword job_outputs: Query files with the given job outputs
        :type job_outputs: list
        :keyword recipe_ids: Query files with a given recipe id
        :type recipe_ids: list
        :keyword recipe_nodes: Query files with a given recipe nodes
        :type recipe_nodes: list
        :keyword recipe_type_ids: Query files with the given recipe types
        :type recipe_type_ids: list
        :keyword batch_ids: Query files with batches with the given identifiers.
        :type batch_ids: list
        :param order: A list of fields to control the sort order.
        :type order: list
        """
        
        files = ScaleFile.objects.filter_files(
            data_started=data_started, data_ended=data_ended,
            source_started=source_started, source_ended=source_ended,
            source_sensor_classes=source_sensor_classes, source_sensors=source_sensors,
            source_collections=source_collections, source_tasks=source_tasks,
            mod_started=mod_started, mod_ended=mod_ended, job_type_ids=job_type_ids,
            job_type_names=job_type_names, job_ids=job_ids,
            file_names=file_names, job_outputs=job_outputs, recipe_ids=recipe_ids,
            recipe_type_ids=recipe_type_ids, recipe_nodes=recipe_nodes, batch_ids=batch_ids,
            order=order)
        
        data_list = []    
        try:
            for f in files:
                entry = copy.deepcopy(template)
                file_params = entry['files']
                for p in file_params:
                    if file_params[p] == 'FILE_VALUE':
                        file_params[p] = [f.id]
                data_list.append(DataV6(data=entry, do_validate=True).get_data())
        except (KeyError, TypeError) as ex:
            raise InvalidData('INVALID_TEMPLATE', "Specified template is invalid: %s" % ex)
        
        return data_list

    def validate_data_list(self, dataset, data_list):
        """Validates a list of data objects against a dataset

        :param dataset: The dataset the member is a part of
        :type dataset: :class:`dataset.models.DataSet`
        :param data_list: Data definitions of the dataset members
        :type data_list: [:class:`data.data.data.Data`]
        """

        is_valid = True
        errors = []
        warnings = []
        
        for data in data_list:
            try:
                dataset.get_definition().validate(data)
            except (InvalidData, InvalidDataSetMember) as ex:
                is_valid = False
                errors.append(ex.error)
                message = 'Dataset definition is invalid: %s' % ex
                logger.info(message)
                pass

        # validate other fields
        return DataSetValidation(is_valid, errors, warnings)
        
    def create_dataset_members(self, dataset, data_list):
        """Creates a dataset member

        :param dataset: The dataset the member is a part of
        :type dataset: :class:`dataset.models.DataSet`
        :param data_list: Data definitions of the dataset members
        :type data_list: [:class:`data.data.data.Data`]
        """

        with transaction.atomic():
            dataset_members = []
            datasetfiles = []
            existing_scale_ids = DataSetFile.objects.get_file_ids(dataset_ids=[dataset.id])
            for d in data_list:
                dataset_member = DataSetMember()
                dataset_member.dataset = dataset
                dataset_member.data = convert_data_to_v6_json(d).get_dict()
                dataset_member.file_ids = list(data_util.get_file_ids(d))
                dataset_members.append(dataset_member)
                datasetfiles = DataSetFile.objects.create_dataset_files(dataset, d, existing_scale_ids)
            DataSetFile.objects.bulk_create(datasetfiles)
            return DataSetMember.objects.bulk_create(dataset_members)

    def get_dataset_members(self, dataset):
        """Returns dataset members for the given dataset

        :returns: members for a given dataset
        :rtype: QuerySet<DataSetMember>
        """
        return self.all().filter(dataset=dataset).order_by('id')

    def get_details_v6(self, dsm_id):
        """Gets additional details for the given dataset member id

        :returns: The full dataset member for the given id
        :rtype: :class:`dataset.models.DataSetMember`
        """

        dsm = DataSetMember.objects.get(pk=dsm_id)
        dsm.files = DataSetFile.objects.filter(dataset=dsm.dataset, scale_file_id__in=list(dsm.file_ids))
        return dsm


class DataSetMember(models.Model):
    """
    Defines the data of a dataset? contains list/descriptors of DataFiles

    :keyword dataset: Refers to dataset member belongs to
    :type dataset: :class:`django.db.models.ForeignKey`
    :keyword data: JSON description of the data in this DataSetMember.
    :type data: :class: `django.contrib.postgres.fields.JSONField(default=dict)
    :keyword created: Created Time
    :type created: datetime
    """

    dataset = models.ForeignKey('dataset.DataSet', on_delete=models.PROTECT)
    data = django.contrib.postgres.fields.JSONField(default=dict)
    file_ids = django.contrib.postgres.fields.ArrayField(models.IntegerField(null=True))
    created = models.DateTimeField(auto_now_add=True)

    objects = DataSetMemberManager()

    def get_dataset_definition(self):
        """Returns the dataset definition

        :returns: The dataset definition
        :rtype: :class:`dataset.DataSetDefinition`
        """

        return self.dataset.get_definition()

    def get_data(self):
        """Returns the data for this datasetmember

        :returns: The data for this datasetmember
        :rtype: :class:`data.data.data.Data`
        """

        return DataV6(data=self.data, do_validate=False).get_data()

    def get_v6_data_json(self):
        """Returns the data for this datasetmember as v6 json with the version stripped

        :returns: The v6 JSON output data dict for this datasetmember
        :rtype: dict
        """

        return rest_utils.strip_schema_version(convert_data_to_v6_json(self.get_data()).get_dict())

    class Meta(object):
        """meta information for the db"""
        db_table = 'data_set_member'


class DataSetFileManager(models.Manager):
    """Manages the datasetfile model"""

    def create_dataset_files(self, dataset, data, existing_scale_ids):
        """Creates dataset files for the given dataset and data"""

        datasetfiles = []
        for i in data.values.keys():
            v = data.values[i]
            if type(v) is FileValue:
                for id in v.file_ids:
                    if id in existing_scale_ids:
                        continue
                    file = DataSetFile()
                    file.dataset = dataset
                    file.scale_file = ScaleFile.objects.get(pk=id)
                    file.parameter_name = i
                    datasetfiles.append(file)

        return datasetfiles

    def get_file_ids(self, dataset_ids, parameter_names=None):
        """Returns a list of the file IDs for the given datasets, optionally filtered by parameter_name.

        :param dataset_ids: The ids of the associated datasets
        :type dataset_ids: integer
        :param parameter_names: The parameter names to search for in the given datasets
        :type parameter_names: string
        :returns: The list of scale file IDs
        :rtype: list
        """

        query = self.all().filter(dataset_id__in=list(dataset_ids))
        if parameter_names:
            query = query.filter(parameter_name__in=list(parameter_names))
        return [result.scale_file_id for result in query.only('scale_file_id').distinct()]

    def get_dataset_ids(self, file_ids, all_files=False):
        """Returns a list of the dataset IDs that contain the given files

        :param file_ids: The ids of the files to look for
        :type dataset_id: integer
        :param all_files: Whether or not a dataset must contain all files or just some of the files in the list
        :type all_files: bool
        :returns: The list of dataset IDs
        :rtype: list
        """

        results = []
        if not all_files:
            query = self.all().filter(scale_file_id__in=list(file_ids)).only('dataset_id').distinct()
            results = [result.dataset_id for result in query]
        else:
            query = self.all().filter(scale_file_id__in=list(file_ids)).values('dataset_id').annotate(total=Count('dataset_id')).order_by('total')
            for result in query:
                if result['total'] == len(file_ids):
                    results.append(result['dataset_id'])
        return results

    def get_files(self, dataset_ids, parameter_names=None):
        """Returns the dataset files associated with the given dataset_ids

        :param dataset_ids: The ids of the associated datasets
        :type dataset_ids: integer
        :param parameter_names: The parameter names to search for in the given datasets
        :type parameter_names: string
        :returns: The DataSetFiles associated with that dataset_id
        :rtype: [:class:`dataset.models.DataSetFile`]
        """

        files = self.all().filter(dataset_id__in=list(dataset_ids))
        if parameter_names:
            files = files.filter(parameter_name__in=list(parameter_names))
        return files

    def get_datasets(self, file_ids, all_files=False):
        """Returns the datasets associated with the given file_id

        :param file_id: The id of the associated file
        :type file_id: integer
        :param all_files: Whether or not a dataset must contain all files or just some of the files in the list
        :type all_files: bool
        :returns: The DataSets associated with that dataset_id
        :rtype: [:class:`dataset.models.DataSet`]
        """
        dataset_ids = self.get_dataset_ids(file_ids=file_ids, all_files=all_files)
        datasets = DataSet.objects.filter(id__in=dataset_ids)

        return datasets

    def get_dataset_files(self, dataset_id):
        """Returns the dataset files associated with the given dataset_id

        :param dataset_id: The id of the associated dataset
        :type dataset_id: integer
        :returns: The DataSetFiles associated with that dataset_id
        :rtype: [:class:`dataset.models.DataSetFile`]
        """

        files = DataSetFile.objects.filter(dataset_id=dataset_id)

        return files


class DataSetFile(models.Model):
    """
    The actual file in a dataset member

    :keyword dataset: Refers to the dataset the file is a member of
    :type dataset: :class:`django.db.models.ForeignKey`
    :keyword scale_file: Refers to the ScaleFile
    :type scale_file: :class:`django.db.models.ForeignKey`
    :keyword parameter_name: Refers to the File parameter name
    :type parameter_name: :class:`django.db.models.CharField`
    """

    dataset = models.ForeignKey('dataset.DataSet', on_delete=models.PROTECT)
    scale_file = models.ForeignKey('storage.ScaleFile', on_delete=models.PROTECT)
    parameter_name = models.CharField(db_index=True, max_length=50)
    objects = DataSetFileManager()

    class Meta(object):
        """meta information for the db"""
        db_table = 'data_set_file'
        unique_together = ("dataset", "scale_file")