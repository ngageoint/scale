"""Defines the database models for datasets"""
from __future__ import absolute_import, unicode_literals

import logging
import re
import semver
from collections import namedtuple

import django.contrib.postgres.fields
from django.db import models, transaction

from dataset.definition.definition import DataSetDefinition, DataSetMemberDefinition
from dataset.definition.json.definition_v6 import convert_definition_to_v6_json, DataSetDefinitionV6, convert_member_definition_to_v6_json, DataSetMemberDefinitionV6
from dataset.exceptions import InvalidDataSetDefinition, InvalidDataSetMember
from dataset.dataset_serializers import DataSetFilesSerializerV6, DataSetMemberSerializerV6
from storage.models import ScaleFile
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

DataSetValidation = namedtuple('DataSetValidation', ['is_valid', 'errors', 'warnings'])
# DataSetKey = namedtuple('DataSetKey', ['name', 'version'])

class DataSetManager(models.Manager):
    """Provides additional methods for handling datasets"""

    @transaction.atomic
    def create_dataset_v6(self, version, definition, name=None, title=None, description=None):
        """Creates and returns a new dataset for the given name/title/description/definition/version??

        :param version: Version of the dataset
        :type version: string
        :param definition: Parameter definition of the dataset
        :type definition: :class:`dataset.definition.definition.DataSetDefinition`
        :param name: unique name of the dataset
        :type name: string
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

        dataset.name = name
        dataset.version = version
        dataset.version_array = dataset.get_dataset_version_array(dataset.version)
        dataset.title = title
        dataset.version = version
        dataset.description = description
        dataset.definition = definition.get_dict()

        dataset.save()

        return dataset

    # TODO
    @transaction.atomic
    def edit_dataset_v6(self, dataset_id, definition=None, title=None, description=None):
        """Handles updating the given datset

        :param dataset_id: The unique identifier of the dataset to edit
        :type dataset_id: int
        :param definition: The DataSetDefinition
        :type: :class:`dataset.definition.DataSetDefinition`
        :param title: The title of the dataset
        :type title: string
        :param description: The description of the DataSet
        :type description: string
        :raises :class:`dataset.exceptions.InvalidDataSetField`: If a given dataset field has an invalid value
        """

        # Aquire model lock for dataset
        dataset = DataSet.objects.select_for_update().get(pk=dataset_id)

        # Update parameters
        if title:
            dataset.title = title
        if description:
            dataset.description = description
        if definition:
            dataset.definition = definition

        dataset.save()

    def get_dataset_id_v6(self, dataset_id):
        """Gets additional details for the given dataset id

        :returns: The full dataset for the given id
        :rtype: :class:`dataset.models.DataSet`
        """

        return DataSet.objects.get(pk=dataset_id)

    def get_dataset_versions_v6(self, dataset_name, order):
        """Gets all versions of the given dataset_name"""

        return self.filter_datasets(dataset_names=[dataset_name], order=order)

    def get_details_v6(self, name, version):
        """Returns the dataset for the given name and version

        :param name: The name of the dataset
        :type name: string
        :param version: The version of the dataset
        :type version: string
        :returns: The dataset with all detail fields incuded
        :rtype: :class:`dataset.models.DataSet`
        """
        return DataSet.objects.all().get(name=name, version=version)

    def get_datasets_v6(self, created_time=None, dataset_ids=None, dataset_names=None, order=None):
        """Handles retrieving datasets - possibly filtered and ordered

        :returns: The list of datasets that match the given filters
        :rtype: [:class:`dataset.models.DataSet`]
        """
        return self.filter_datasets(created_time=created_time, dataset_ids=dataset_ids, dataset_names=dataset_names, order=order)

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
            datasets = datasets.filter(created__gte=created_time)

        # Apply additional filters
        if dataset_ids:
            datasets = datasets.filter(id__in=dataset_ids)
        if dataset_names:
            datasets = datasets.filter(name__in=dataset_names)

        # Apply sorting
        if order:
            datasets = datasets.order_by(*order)
        else:
            datasets = datasets.order_by('id')

        return datasets

    def validate_dataset_v6(self, name, version, definition, title=None, description=None):
        """Validates the given datast definiton

        :param definition: The dataset definition
        :type definition: dict
        :returns: The dataset validation
        :rtype: :class:`datset.models.DataSetValidation`
        """

        is_valid = True
        errors = []
        warnings = []

        datset_definition = None
        try:
            datset_definition = DataSetDefinitionV6(definition=definition, do_validate=True)
        except InvalidDataSetDefinition as ex:
            is_valid = False
            errors.append(ex.error)
            message = 'Dataset definition is invalid: %s' % ex
            logger.info(message)
            pass

        # validate other fields
        return DataSetValidation(is_valid, errors, warnings)

    def add_dataset_files(self, dataset_id, parameter_name, scale_files):
        """Creates a DataSetFile attached to the given dataset and parameter name

        :param dataset_id: The dataset to attache the file to
        :type dataset_id:
        :param parameter_name: The parameter_name the file belongs with
        :type parameter_name: string
        :param scale_file: ScaleFile to attach
        :type scale_file: [:class:`storage.models.ScaleFile`]

        :returns: The created Data Set files
        :rtype: [:]class:`dataset.models.DataSetFile`]
        """

        if not dataset_id:
            # raise exception dataset must not be null
            return
        if not parameter_name:
            # raise exception
            return

        dataset = self.get_dataset_id_v6(dataset_id=dataset_id)

        #verify parameter_name is in dataset.parameters

        try:
            dataset_definition = DataSetDefinition(definition=dataset.definition)
            parameter = dataset_definition.get_parameter(parameter_name=parameter_name)
        except Exception as ex:# TODO raise Exception parameter not within DataSet
            return

        dataset_files = []
        # Create and return the dataset file
        for file in scale_files:
            dataset_file = DataSetFile()
            dataset_file.dataset = dataset
            dataset_file.scale_file = file
            dataset_file.parameter_name = parameter_name
            dataset_file.save()
            dataset_files.append(dataset_file)

        return dataset_files

    def get_dataset_files(self, dataset_id):
        """Returns the datasetFiles associated with the given dataset_id

        :returns: The list of DataSetFiles matching the file_id
        :rtype: [:class:`dataset.models.DataSetFile`]
        """
        dataset = self.get(pk=dataset_id)
        files = DataSetFile.objects.all().filter(dataset=dataset)
        return files

    def get_dataset_members(self, dataset_id):
        """Returns the members associated with the given dataset_id
        :returns: The list of DataSetMembers
        :rtype: [:clas:`dataset.models.DataSetMember`]
        """
        dataset = self.get(pk=dataset_id)
        members = DataSetMember.objects.all().filter(dataset=dataset)
        return members

"""DataSet

* optional title
* optional description
* JSON definition (like job type input) (Required)
* created time
"""
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

    name = models.CharField(db_index=True, max_length=50)
    version = models.CharField(db_index=True, max_length=50)
    version_array = django.contrib.postgres.fields.ArrayField(models.IntegerField(null=True),default=list([None]*4),size=4)
    title = models.CharField(blank=True, max_length=50, null=True)
    # filter = django.contrib.postgres.fields.JSONField(default=dict)
    description = models.TextField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    definition = django.contrib.postgres.fields.JSONField(default=dict)

    objects = DataSetManager()

    def get_definition(self):
        """Returns the dataset definition

        :returns: The DataSet definition
        :rtype: :class:`dataset.definition.json.DataSetDefinition`
        """

        if isinstance(self.definition, basestring):
            self.definition = {}
        return DataSetDefinition(definition=self.definition)

    def get_v6_definition_json(self):
        """Returns the dataset definition in v6 of the JSON schema

        :returns: The dataset definition in v6 of the JSON schema
        :rtype: dict
        """

        return rest_utils.strip_schema_version(convert_definition_to_v6_json(self.get_dataset_definition()).get_dict())

    def get_dataset_definition(self):
        """Returns the dataset definition

        :returns: The dataset definition json
        :rtype: dict
        """

        return self.definition

    def get_dataset_version_array(self, version):
        """Gets the dataset version as an array of integers
            for sorting using the semver package. The result will be an array of length
            4 with the first three being integers containing major,minor and patch version
            numbers. The fourth will be either a None value or if a prerelease value is
            present this function will attempt to convert it into an integer for sorting.

        :keyword version: The version of the dataset
        :type version: :class:`django.db.models.CharField`
        :return: the version array
        :rtype: array
        """

        parts = None
        try:
            parts = semver.parse(version)
        except:
            return [0,0,0,0]
        prerelease = None
        if parts['prerelease']:
            # attempt to convert pre-release field to a number for sorting
            # we want a non-null value if there is a pre-release field in version as
            # null values come first when sorting by descending order so we want
            # any prerelease versions to have a non-null value
            prerelease = re.sub("[^0-9]", "", parts['prerelease'])
            try:
                prerelease = int(prerelease)
            except ValueError:
                prerelease = ord(parts['prerelease'][0])
        version_array = [parts['major'], parts['minor'], parts['patch'], prerelease]

        return version_array

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
        serializer = DataSetFilesSerializerV6(files, many=True)
        return serializer.data

class DataSetMemberManager(models.Manager):
    """Provides additional methods for handling dataset members"""

    def create_dataset_member_v6(self, dataset, member_definition):
        """Creates a dataset member

        :param dataset: The dataset the member is a part of
        :type version: :class:`dataset.models.DataSet`
        :param member_definition: Parameter definition of the dataset
        :type definition: :class:`dataset.definition.definition.DataSetMemberDefinition`

        :returns: The new dataset member
        :rtype: :class:`dataset.models.DataSetMember`

        :raises :class:`dataset.exceptions.InvalidDataSetMember`: If the dataset member has an invalid value
        """

        if not dataset:
            raise InvalidDataSetMember('INVALID_DATASET_MEMBER', 'No dataset provided for dataset member')

        if not member_definition:
            raise InvalidDataSetMember('INVALID_DATASET_MEMBER', 'No dataset member definition provided')

        dataset_member = DataSetMember()
        dataset_member.dataset = dataset
        dataset_member.definition = member_definition.get_dict()
        dataset_member.save()

        return dataset_member

    def get_dataset_members(self, dataset):
        """Returns dataset members for the given dataset

        :returns: members for a given dataset
        :rtype: QuerySet<DataSetMember>
        """
        return self.all().filter(dataset=dataset)

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
    Defines the data of a dataset? contains list/descriptors of DataFiles

    :keyword dataset: Refers to dataset member belongs to
    :type dataset: :class:`django.db.models.ForeignKey`
    :keyword definition: JSON description of the data in this DataSetMember.
    :type definition: :class: `django.contrib.postgres.fields.JSONField(default=dict)
    :keyword created: Created Time
    :type created: datetime
    """

    dataset = models.ForeignKey('dataset.DataSet', on_delete=models.PROTECT)
    definition = django.contrib.postgres.fields.JSONField(default=dict)
    created = models.DateTimeField(auto_now_add=True)

    objects = DataSetMemberManager()

    def get_definition(self):
        """Returns the dataset member definition

        :returns: The dataset member definition in v6
        :rtype: :class:`dataset.DataSetMemberDefinition`
        """

        if isinstance(self.definition, basestring):
            self.definition = {}

        return DataSetMemberDefinition(definition=self.definition)

    def get_definition_json(self):
        """Returns the dataset member definition in JSON format
        :returns: the dataset member definition in JSON
        :rtype: dict
        """
        return self.definition

    def get_v6_definition_json(self):
        """Returns the dataset member definition in V6 JSON format

        :returns: The dataset member definition in v6 of the JSON Schema
        :rtype: dict
        """

        return rest_utils.strip_schema_version(convert_member_definition_to_v6_json(self.get_definition_json()))

class DataSetFileManager(models.Manager):
    """Manages the datasetfile model"""

    def get_dataset_files(self, dataset_id):
        """Returns the dataset files associated with the given dataset_id

        :param dataset_id: The id of the associated dataset
        :type dataset_id: integer
        :returns: The DataSetFiles associated with that dataset_id
        :rtype: [:class:`dataset.models.DataSetFile`]
        """
        dataset = DataSet.objects.get(pk=dataset_id)
        files = self.all().filter(dataset=dataset)
        return files


"""
DataSetFile

* indexed foreign key to DataSet
* index foreign key to Scale file
* char field for file parameter name (from data set definition JSON)
* unique combined index on (DataSet ID, Scale file ID) ??
"""
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
    objects = DataSetFileManager

