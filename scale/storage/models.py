"""Defines the database models for file information and workspaces"""
from __future__ import unicode_literals

import hashlib
import logging
import os
import re
from collections import namedtuple

import django.contrib.gis.db.models as models
import django.contrib.gis.geos as geos
import django.utils.timezone as timezone
import django.contrib.postgres.fields
from django.db import transaction

import storage.geospatial_utils as geospatial_utils
from storage.brokers.factory import get_broker
from storage.configuration.workspace_configuration import WorkspaceConfiguration
from storage.configuration.exceptions import InvalidWorkspaceConfiguration
from storage.configuration.json.workspace_config_1_0 import WorkspaceConfigurationV1
from storage.configuration.json.workspace_config_v6 import convert_config_to_v6_json, WorkspaceConfigurationV6
from storage.container import get_workspace_volume_path
from storage.exceptions import ArchivedWorkspace, DeletedFile, InvalidDataTypeTag, MissingVolumeMount
from storage.media_type import get_media_type
from util.os_helper import makedirs
from util import rest as rest_utils
from util.validation import ValidationWarning

logger = logging.getLogger(__name__)

# Allow alphanumerics, dashes, underscores, and spaces
VALID_TAG_PATTERN = re.compile('^[a-zA-Z0-9\\-_ ]+$')


class CountryDataManager(models.Manager):
    """Provides additional methods for handling country data
    """

    @transaction.atomic
    def update_border(self, name, border, effective=None):
        """Updates the country border geometry for an existing country, adding a new entry for the new effective date.

        :param name: The name of an existing country
        :type name: string
        :param border: The new border geometry. Either GEOSGeometry or geojson (which will be converted to GEOSGeometry)
        :type border: GEOSGeometry or dict
        :param effective: The effective date for the new border. If None, now() will be used
        :type effective: :class:`datetime.datetime`
        """

        if not isinstance(border, geos.geometry.GEOSGeometry):
            border, _ = geospatial_utils.parse_geo_json(border)

        # Acquire model lock
        cur = self.get(name=name)
        if cur:
            new_item = CountryData(name=cur.name, fips=cur.fips, gmi=cur.gmi,
                                   iso2=cur.iso2, iso3=cur.iso3,
                                   iso_num=cur.iso_num, border=border, effective=effective)
            new_item.save()

    def get_effective(self, target_date, name=None, iso2=None):
        """Get the country data entry for a name or iso2 abbreviation and target date such that this is the most
        recent entry whose effective date is before the target.

        :param target_date: The target date
        :type target_date: :class:`datetime.datetime`
        :param name: The name of the country. Mutually exclusive with iso2. One of these is required.
        :type name: string
        :param iso2: The iso2 abbreviation of the country. Mutually exclusive with name. One of these is required.
        :type iso2: string
        :returns: A query set
        :rtype: :class:`django.db.models.query.QuerySet`
        """
        assert ((name is not None and iso2 is None) or (iso2 is not None and name is None))
        if name is not None:
            return self.filter(name=name, effective__lte=target_date).order_by('-effective').first()
        else:
            return self.filter(iso2=iso2, effective__lte=target_date).order_by('-effective').first()

    def get_intersects(self, geom, target_date):
        """Get the countries whose borders intersect the specified geometry and whose effective date
        is before the target.

        :param geom: The geometry (point, poly, etc.) to search.
        :type geom: :class:`django.contrib.gis.geos.geometry.GEOSGeometry`
        :param target_date: The target date
        :type target_date: :class:`datetime.datetime`
        :returns: A dict of intersected countries mapped to entities
        :rtype: dict
        """

        tmp = self.filter(border__intersects=geom, effective__lte=target_date).order_by('-effective')
        rval = {}
        for val in tmp:
            if val.name in rval:
                if val.effective <= target_date and val.effective > rval[val.name].effective:
                    rval[val.name] = val
            elif val.effective <= target_date:
                rval[val.name] = val
        return rval


class CountryData(models.Model):
    """Represents country borders and official abbreviations

    :keyword name: The full name of the country
    :type name: :class:`django.db.models.CharField`
    :keyword fips: FIPS digraph for the country
    :type fips: :class:`django.db.models.CharField`
    :keyword gmi: gmi trigraph for the country
    :type gmi: :class:`django.db.models.CharField`
    :keyword iso2: ISO digraph for the country
    :type iso2: :class:`django.db.models.CharField`
    :keyword iso3: ISO trigraph for the country
    :type iso3: :class:`django.db.models.CharField`
    :keyword iso_num: ISO number for the country
    :type iso_num: :class:`django.db.models.IntegerField`
    :keyword border: Border geometry of this country
    :type border: :class:`django.contrib.gis.geos.geometry.GEOSGeometry`
    :keyword effective: When the country information including the border are effective.
    :type effective: :class:`django.db.models.DateTimeField`
    :keyword is_deleted: Whether the country has been deleted or not
    :type is_deleted: :class:`django.db.models.BooleanField`
    :keyword created: When the country model was created
    :type created: :class:`django.db.models.DateTimeField`
    :keyword deleted: When the country model was deleted
    :type deleted: :class:`django.db.models.DateTimeField`
    :keyword last_modified: When the country model was last modified
    :type last_modified: :class:`django.db.models.DateTimeField`
    """

    name = models.CharField(max_length=128)
    fips = models.CharField(max_length=2)
    gmi = models.CharField(max_length=3)
    iso2 = models.CharField(max_length=2)
    iso3 = models.CharField(max_length=3)
    iso_num = models.IntegerField()
    border = models.GeometryField(spatial_index=True, srid=4326)
    effective = models.DateTimeField()
    is_deleted = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    deleted = models.DateTimeField(blank=True, null=True)
    last_modified = models.DateTimeField(auto_now=True, db_index=True)

    objects = CountryDataManager()

    def __unicode__(self):
        """Unicode representation of a country which is the ISO3 code for this country.
        """
        return self.iso3

    class Meta(object):
        """meta information for the db"""
        db_table = 'country_data'
        unique_together = ("name", "effective")
        index_together = ["name", "effective"]


class ScaleFileManager(models.Manager):
    """Provides additional methods for handling Scale files
    """

    def delete_files(self, files):
        """Deletes the given files from the remove storage system. Each ScaleFile model should have its related
        workspace field populated. This method will update the ScaleFile model and save the changes in the database.

        :param files: List of files to delete
        :type files: [:class:`storage.models.ScaleFile`]

        :raises :class:`storage.exceptions.ArchivedWorkspace`: If one of the files has a workspace that is archived
        :raises :class:`storage.exceptions.MissingRemoteMount`: If a required mount location is missing
        """

        wp_dict = {}  # {Workspace ID: (workspace, [file])}
        # Organize files by workspace
        for scale_file in files:
            workspace = scale_file.workspace
            if not workspace.is_active:
                raise ArchivedWorkspace('%s is no longer active' % workspace.name)
            if workspace.id in wp_dict:
                wp_list = wp_dict[workspace.id][1]
            else:
                wp_list = []
                wp_dict[workspace.id] = (workspace, wp_list)
            wp_list.append(scale_file)

        # Delete files for each workspace
        for wp_id in wp_dict:
            workspace = wp_dict[wp_id][0]
            wp_file_deletes = wp_dict[wp_id][1]
            workspace.delete_files(wp_file_deletes)

    def download_files(self, file_downloads):
        """Downloads the given files to the given local file system paths. Each ScaleFile model should have its related
        workspace field populated.

        :param file_downloads: List of files to download
        :type file_downloads: [:class:`storage.brokers.broker.FileDownload`]

        :raises :class:`storage.exceptions.ArchivedWorkspace`: If one of the files has a workspace that is archived
        :raises :class:`storage.exceptions.DeletedFile`: If one of the files is deleted
        :raises :class:`storage.exceptions.MissingRemoteMount`: If a required mount location is missing
        """

        wp_dict = {}  # {Workspace ID: (workspace, [file download])}
        # Organize files by workspace
        for file_download in file_downloads:
            workspace = file_download.file.workspace
            if not workspace.is_active:
                raise ArchivedWorkspace('%s is no longer active' % workspace.name)
            if file_download.file.is_deleted:
                raise DeletedFile(file_download.file.file_name)
            if workspace.id in wp_dict:
                wp_list = wp_dict[workspace.id][1]
            else:
                wp_list = []
                wp_dict[workspace.id] = (workspace, wp_list)
            wp_list.append(file_download)

        # Download files for each workspace
        for wp_id in wp_dict:
            workspace = wp_dict[wp_id][0]
            wp_file_downloads = wp_dict[wp_id][1]
            workspace.download_files(wp_file_downloads)

    def get_details(self, file_id):
        """Returns the file for the given ID with all detail fields included.

        There are currently no additional fields included.

        :param file_id: The unique identifier of the workspace.
        :type file_id: int
        :returns: The file with all detail fields included.
        :rtype: :class:`storage.models.ScaleFile`
        """

        # Attempt to get the workspace
        scale_file = ScaleFile.objects.get(pk=file_id)

        return scale_file
        
    def filter_files_v5(self, started=None, ended=None, time_field=None, file_name=None):
        """Returns a query for Scale files that is filtered on the given fields.

        :param started: Query Scale files updated after this amount of time.
        :type started: :class:`datetime.datetime`
        :param ended: Query Scale files updated before this amount of time.
        :type ended: :class:`datetime.datetime`
        :keyword time_field: The time field to use for filtering.
        :type time_field: string
        :param file_name: Query Scale files with the given file name.
        :type file_name: str
        :returns: The Scale file query
        :rtype: :class:`django.db.models.QuerySet`
        """

        # Fetch a list of source files
        files = ScaleFile.objects.all()
        files = files.select_related('workspace')
        files = files.defer('workspace__json_config')
        files = files.prefetch_related('countries')

        # Apply file_name filtering if present
        if file_name:
            files = files.filter(file_name=file_name)

        # Apply time range filtering
        if started:
            if time_field == 'source':
                files = files.filter(source_started__gte=started)
            elif time_field == 'data':
                files = files.filter(data_started__gte=started)
            else:
                files = files.filter(last_modified__gte=started)
        if ended:
            if time_field == 'source':
                files = files.filter(source_ended__lte=ended)
            elif time_field == 'data':
                files = files.filter(data_ended__lte=ended)
            else:
                files = files.filter(last_modified__lte=ended)

        files = files.order_by('last_modified')
        return files
        
    def filter_files(self, data_started=None, data_ended=None, source_started=None, source_ended=None,
                        source_sensor_classes=None, source_sensors=None, source_collections=None,
                        source_tasks=None, mod_started=None, mod_ended=None, job_type_ids=None, job_type_names=None,
                        job_ids=None, is_published=None, is_superseded=None, file_names=None, job_outputs=None, 
                        recipe_ids=None, recipe_type_ids=None, recipe_nodes=None, batch_ids=None, order=None):
        """Returns a query for product models that filters on the given fields. The returned query includes the related
        workspace, job_type, and job fields, except for the workspace.json_config field. The related countries are set
        to be pre-fetched as part of the query.

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
        :param source_task: Query files with the given source task.
        :type source_task: list
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
        :returns: The product file query
        :rtype: :class:`django.db.models.QuerySet`
        """

        # Fetch a list of product files
        files = ScaleFile.objects.all()
        files = files.select_related('workspace', 'job_type', 'job', 'job_exe', 'recipe', 'recipe_type', 'batch')
        files = files.defer('workspace__json_config', 'job__input', 'job__output', 'job_exe__environment',
                                  'job_exe__configuration', 'job_exe__job_metrics', 'job_exe__stdout',
                                  'job_exe__stderr', 'job_exe__results', 'job_exe__results_manifest',
                                  'job_type__manifest', 'job_type__docker_params', 'job_type__configuration',
                                  'job_type__error_mapping', 'recipe__input', 'recipe_type__definition',
                                  'batch__definition')
        files = files.prefetch_related('countries')

        # Apply time range filtering
        if data_started:
            files = files.filter(data_started__gte=data_started)
        if data_ended:
            files = files.filter(data_ended__lte=data_ended)

        if source_started:
            files = files.filter(source_started__gte=source_started)
        if source_ended:
            files = files.filter(source_ended__lte=source_ended)

        if source_sensor_classes:
            files = files.filter(source_sensor_class__in=source_sensor_classes)
        if source_sensors:
            files = files.filter(source_sensor__in=source_sensors)
        if source_collections:
            files = files.filter(source_collection__in=source_collections)
        if source_tasks:
            files = files.filter(source_task__in=source_tasks)

        if mod_started:
            files = files.filter(last_modified__gte=mod_started)
        if mod_ended:
            files = files.filter(last_modified__lte=mod_ended)

        if job_type_ids:
            files = files.filter(job_type_id__in=job_type_ids)
        if job_type_names:
            files = files.filter(job_type__name__in=job_type_names)
        if job_ids:
            files = files.filter(job_id__in=job_ids)
        if is_published is not None:
            files = files.filter(is_published=is_published)
        if is_superseded is not None:
            files = files.filter(is_superseded=is_superseded)
        if file_names:
            files = files.filter(file_name__in=file_names)
        if job_outputs:
            files = files.filter(job_output__in=job_outputs)
        if recipe_ids:
            files = files.filter(recipe_id__in=recipe_ids)
        if recipe_nodes:
            files = files.filter(recipe_node__in=recipe_nodes)
        if recipe_type_ids:
            files = files.filter(recipe_type__in=recipe_type_ids)
        if batch_ids:
            files = files.filter(batch_id__in=batch_ids)

        # Apply sorting
        if order:
            files = files.order_by(*order)
        else:
            files = files.order_by('last_modified')

        return files

    def get_files_for_job_summary(self, file_ids):
        """Returns the file models with the given IDs. Each scale_file model only contains the needed fields for
        calculating summary data for a job's inputs. The returned list is a queryset iterator, so only access it once.

        :param file_ids: The file IDs
        :type file_ids: list
        :returns: The scale_file models that match the given IDs
        :rtype: list
        """

        return self.filter(id__in=file_ids).only('id', 'file_size', 'source_started', 'source_ended').iterator()

    def get_files_for_queued_jobs(self, file_ids):
        """Returns the file models with the given IDs. Each scale_file model only contains the needed fields for
        configuring queued jobs. The returned list is a queryset iterator, so only access it once.

        :param file_ids: The file IDs
        :type file_ids: list
        :returns: The scale_file models that match the given IDs
        :rtype: list
        """

        file_qry = self.select_related('workspace').filter(id__in=file_ids)
        file_qry = file_qry.only('id', 'file_type', 'file_path', 'is_deleted', 'workspace__name')
        return file_qry.iterator()

    def move_files(self, file_moves):
        """Moves the given files to the new file system paths. Each ScaleFile model should have its related workspace
        field populated. This method will update the file_path field in each ScaleFile model to the new path (it may
        also change other ScaleFile fields) and save the changes in the database.

        :param file_moves: List of files to move
        :type file_moves: [:class:`storage.brokers.broker.FileMove`]

        :raises :class:`storage.exceptions.ArchivedWorkspace`: If one of the files has a workspace that is archived
        :raises :class:`storage.exceptions.DeletedFile`: If one of the files is deleted
        :raises :class:`storage.exceptions.MissingRemoteMount`: If a required mount location is missing
        """

        wp_dict = {}  # {Workspace ID: (workspace, [file move])}
        # Organize files by workspace
        for file_move in file_moves:
            workspace = file_move.file.workspace
            if not workspace.is_active:
                raise ArchivedWorkspace('%s is no longer active' % workspace.name)
            if file_move.file.is_deleted:
                raise DeletedFile(file_move.file.file_name)
            if workspace.id in wp_dict:
                wp_list = wp_dict[workspace.id][1]
            else:
                wp_list = []
                wp_dict[workspace.id] = (workspace, wp_list)
            wp_list.append(file_move)

        # Move files for each workspace
        for wp_id in wp_dict:
            workspace = wp_dict[wp_id][0]
            wp_file_moves = wp_dict[wp_id][1]
            workspace.move_files(wp_file_moves)

    def upload_files(self, workspace, file_uploads):
        """Uploads the given files from the given local file system paths into the given workspace. Each ScaleFile model
        should have its file_path field populated with the relative location where the file should be stored within the
        workspace. This method will update the workspace and other fields (including possibly changing file_path) in
        each ScaleFile model and will save the models to the database.

        :param workspace: The workspace to upload files into
        :type workspace: :class:`storage.models.Workspace`
        :param file_uploads: List of files to upload
        :type file_uploads: [:class:`storage.brokers.broker.FileUpload`]
        :returns: The list of saved file models
        :rtype: [:class:`storage.models.ScaleFile`]

        :raises :class:`storage.exceptions.ArchivedWorkspace`: If one of the files has a workspace that is archived
        :raises :class:`storage.exceptions.MissingRemoteMount`: If a required mount location is missing
        """

        if not workspace.is_active:
            raise ArchivedWorkspace('%s is no longer active' % workspace.name)

        file_list = []
        for file_upload in file_uploads:
            scale_file = file_upload.file
            scale_file.workspace = workspace
            scale_file.is_deleted = False
            scale_file.deleted = None
            file_list.append(scale_file)

        # Store files in workspace
        workspace.upload_files(file_uploads)

        # Populate the country list for all files that were saved
        for file_upload in file_uploads:
            scale_file = file_upload.file
            if scale_file.pk:
                scale_file.set_countries()
                scale_file.save()

        return file_list


class ScaleFile(models.Model):
    """Represents a file that is stored within a Scale workspace

    :keyword file_name: The name of the file
    :type file_name: :class:`django.db.models.CharField`
    :keyword file_type: The (Scale) type of the file
    :type file_type: :class:`django.db.models.CharField`
    :keyword media_type: The IANA media type of the file
    :type media_type: :class:`django.db.models.CharField`
    :keyword file_size: The size of the file in bytes
    :type file_size: :class:`django.db.models.BigIntegerField`
    :keyword data_type: A comma-separated string listing the data type "tags" for the file
    :type data_type: :class:`django.db.models.TextField`
    :keyword file_path: The relative path of the file in its workspace
    :type file_path: :class:`django.db.models.CharField`
    :keyword workspace: The workspace that stores this file
    :type workspace: :class:`django.db.models.ForeignKey`
    :keyword is_deleted: Whether the file has been deleted or not
    :type is_deleted: :class:`django.db.models.BooleanField`
    :keyword uuid: A universally unique identifier for the source record. It ensures that subsequent updates of the
        record will result in the same UUID, which can then be used as a stable permanent link in applications.
    :type uuid: :class:`django.db.models.CharField`

    :keyword created: When the file model was created
    :type created: :class:`django.db.models.DateTimeField`
    :keyword deleted: When the file was deleted
    :type deleted: :class:`django.db.models.DateTimeField`
    :keyword last_modified: When the file model was last modified
    :type last_modified: :class:`django.db.models.DateTimeField`

    :keyword data_started: The start time of the data in this file
    :type data_started: :class:`django.db.models.DateTimeField`
    :keyword data_ended: The end time of the data in this file
    :type data_ended: :class:`django.db.models.DateTimeField`
    :keyword geometry: Geometry representing the data in this file
    :type geometry: :class:`django.contrib.gis.db.models.GeometryField`
    :keyword center_point: The center point of this file geometry
    :type center_point: :class:`django.contrib.gis.db.models.PointField`
    :keyword meta_data: JSON meta-data about this file
    :type meta_data: :class:`django.contrib.postgres.fields.JSONField`
    :keyword countries: List of countries represented in this file as indicated by the file's geometry.
    :type countries: :class:`django.db.models.ManyToManyField` of :class:`storage.models.CountryData`

    :keyword is_parsed: Whether the source file has been parsed or not
    :type is_parsed: :class:`django.db.models.BooleanField`
    :keyword parsed: When the source file was parsed
    :type parsed: :class:`django.db.models.DateTimeField`

    :keyword job_exe: The job execution that created this product
    :type job_exe: :class:`django.db.models.ForeignKey`
    :keyword job: The job that created this product
    :type job: :class:`django.db.models.ForeignKey`
    :keyword job_type: The type of the job that created this product
    :type job_type: :class:`django.db.models.ForeignKey`
    :keyword job_output: The output name from the job interface
    :type job_output: :class:`django.db.models.CharField`
    :keyword recipe: The identifier of a recipe this file is associated with
    :type recipe: :class:`django.db.models.ForeignKey`
    :keyword recipe_node: The name of the node within the recipe
    :type recipe_node: :class:`django.db.models.CharField`
    :keyword recipe_node: The name of the job within the recipe
    :type recipe_node: :class:`django.db.models.CharField`
    :keyword recipe_type: The type of recipe that the file is associated with
    :type recipe_type: :class:`django.db.models.ForeignKey`
    :keyword batch: The identifier of the batch this file is associated with
    :type batch: :class:`django.db.models.ForeignKey`
    :keyword source_started: The earliest start time from all source files
    :type source_started: :class:`django.db.models.DateTimeField`
    :keyword source_ended: The latest end time from all source files
    :type source_ended: :class:`django.db.models.DateTimeField`
    :keyword is_operational: Whether this product was produced by an operational job type (True) or by a job type that
        is still in a research & development (R&D) phase (False)
    :type is_operational: :class:`django.db.models.BooleanField`
    :keyword has_been_published: Whether this product has ever been published. A product becomes published when its job
        execution completes successfully. A product that has been published will appear in the API call to retrieve
        product updates.
    :type has_been_published: :class:`django.db.models.BooleanField`
    :keyword is_published: Whether this product is currently published. A published product has had its job execution
        complete successfully and has not been unpublished.
    :type is_published: :class:`django.db.models.BooleanField`
    :keyword is_superseded: Whether this product has been superseded by another product with the same UUID
    :type is_superseded: :class:`django.db.models.BooleanField`
    :keyword published: When this product was published (its job execution was completed)
    :type published: :class:`django.db.models.DateTimeField`
    :keyword unpublished: When this product was unpublished
    :type unpublished: :class:`django.db.models.DateTimeField`
    :keyword superseded: When this product was superseded
    :type superseded: :class:`django.db.models.DateTimeField`
    """

    FILE_TYPES = (
        ('SOURCE', 'SOURCE'),
        ('PRODUCT', 'PRODUCT'),
    )

    VALID_TIME_FIELDS = ['source', 'data', 'last_modified']

    file_name = models.CharField(max_length=250, db_index=True)
    file_type = models.CharField(choices=FILE_TYPES, default='SOURCE', max_length=50, db_index=True)
    media_type = models.CharField(max_length=250)
    file_size = models.BigIntegerField()
    data_type = models.TextField(blank=True)
    file_path = models.CharField(max_length=1000)
    workspace = models.ForeignKey('storage.Workspace', on_delete=models.PROTECT)
    is_deleted = models.BooleanField(default=False)
    uuid = models.CharField(db_index=True, max_length=32)

    created = models.DateTimeField(auto_now_add=True, db_index=True)
    deleted = models.DateTimeField(blank=True, null=True)
    last_modified = models.DateTimeField(auto_now=True, db_index=True)

    meta_data = django.contrib.postgres.fields.JSONField(default=dict)

    # Optional geospatial fields
    geometry = models.GeometryField('Geometry', blank=True, null=True, srid=4326)
    center_point = models.PointField(blank=True, null=True, srid=4326)
    countries = models.ManyToManyField(CountryData)

    # Optional temporal fields
    data_started = models.DateTimeField(blank=True, null=True, db_index=True)
    data_ended = models.DateTimeField(blank=True, null=True, db_index=True)

    # Supplemental sensor metadata fields
    source_started = models.DateTimeField(blank=True, null=True, db_index=True)
    source_ended = models.DateTimeField(blank=True, null=True, db_index=True)
    source_sensor_class = models.TextField(blank=True, null=True, db_index=True)
    source_sensor = models.TextField(blank=True, null=True, db_index=True)
    source_collection = models.TextField(blank=True, null=True, db_index=True)
    source_task = models.TextField(blank=True, null=True, db_index=True)

    # Source file fields
    is_parsed = models.BooleanField(default=False)
    parsed = models.DateTimeField(blank=True, null=True)

    # Product file fields
    job_exe = models.ForeignKey('job.JobExecution', blank=True, null=True, on_delete=models.PROTECT)
    job = models.ForeignKey('job.Job', blank=True, null=True, on_delete=models.PROTECT)
    job_type = models.ForeignKey('job.JobType', blank=True, null=True, on_delete=models.PROTECT)
    job_output = models.CharField(null=True, blank=True, max_length=250)
    recipe = models.ForeignKey('recipe.Recipe', blank=True, null=True, on_delete=models.PROTECT)
    recipe_node = models.CharField(null=True, blank=True, max_length=250)
    recipe_type = models.ForeignKey('recipe.RecipeType', blank=True, null=True, on_delete=models.PROTECT)
    batch = models.ForeignKey('batch.Batch', blank=True, null=True, on_delete=models.PROTECT)
    is_operational = models.BooleanField(default=True)
    has_been_published = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)
    is_superseded = models.BooleanField(default=False)
    published = models.DateTimeField(blank=True, null=True)
    unpublished = models.DateTimeField(blank=True, null=True)
    superseded = models.DateTimeField(blank=True, null=True)

    objects = ScaleFileManager()

    def update_uuid(self, *args):
        """Computes and sets a new UUID value for this file by hashing the given arguments.

        :param args: One or more input objects to hash.
        :type args: [string]
        :returns: The generated unique identifier.
        :rtype: string
        """

        # Make sure a value is passed to avoid silently creating useless identifiers
        if not args:
            raise ValueError('UUID calculation requires at least one input argument.')

        # Compound each input argument into the computed hash
        builder = hashlib.md5()
        for arg in args:
            if arg is not None:
                builder.update(str(arg))

        # Format the identifier as a 32-character hex representation
        self.uuid = builder.hexdigest()
        return self.uuid

    def add_data_type_tag(self, tag):
        """Adds a new data type tag to the file. A valid tag contains only alphanumeric characters, underscores, and
        spaces.

        :param tag: The data type tag to add
        :type tag: string
        :raises InvalidDataTypeTag: If the given tag is invalid
        """

        if not VALID_TAG_PATTERN.match(tag):
            raise InvalidDataTypeTag('%s is an invalid data type tag' % tag)

        tags = self.get_data_type_tags()
        tags.add(tag)
        self._set_data_type_tags(tags)

    def get_data_type_tags(self):
        """Returns the set of data type tags associated with this file

        :returns: The set of data type tags
        :rtype: {string}
        """

        tags = set()
        if self.data_type:
            for tag in self.data_type.split(','):
                tags.add(tag)
        return tags

    def set_basic_fields(self, file_name, file_size, media_type=None, data_type=None):
        """Sets the basic fields for the Scale file

        :param file_name: The name of the file
        :type file_name: string
        :param file_size: The size of the file in bytes
        :type file_size: long
        :param media_type: The IANA media type of the file
        :type media_type: string
        :param data_type: The set of data type tags for the file
        :type data_type: set
        """

        if not media_type:
            media_type = get_media_type(file_name)

        self.file_name = file_name
        self.file_size = file_size
        self.media_type = media_type
        if data_type:
            for tag in data_type:
                self.add_data_type_tag(tag)

    def set_countries(self):
        """Clears the countries list then recreates it from the CountryData table.
        If no geometry is available, this will remain empty.
        The country border effective date will use (in order or preference) data_started, data_ended, or created.
        """
        self.countries.clear()
        if self.geometry is None:
            return
        target_date = self.created
        if self.data_started is not None:
            target_date = self.data_started
        elif self.data_ended is not None:
            target_date = self.data_ended
        apply(self.countries.add, CountryData.objects.get_intersects(self.geometry, target_date).values())

    def set_deleted(self):
        """Marks the current file as deleted and updates the corresponding fields."""
        self.is_deleted = True
        self.is_published = False
        when = timezone.now()
        self.deleted = when
        self.unpublished = when

    def _set_data_type_tags(self, tags):
        """Sets the data type tags on the model

        :param tags: The data type tags
        :type tags: {string}
        """

        self.data_type = ','.join(tags)

    def _get_url(self):
        """Gets the absolute URL used to download this file.

        Note that this property is only supported if the associated workspace supports HTTP downloads.

        :returns: The file download URL.
        :rtype: string
        """

        try:
            # Make sure a valid path can be created
            if self.workspace.base_url and self.file_path:

                # Make sure there are no duplicate slashes
                base_url = self.workspace.base_url
                if base_url.endswith('/'):
                    base_url = base_url[:-1]
                relative_url = self.file_path
                if relative_url.startswith('/'):
                    relative_url = relative_url[1:]

                # Combine the workspace and file path
                return '%s/%s' % (base_url, relative_url)
        except Workspace.DoesNotExist:
            # No-op for when Workspace is not set
            pass

    url = property(_get_url)

    class Meta(object):
        """meta information for the db"""
        db_table = 'scale_file'

WorkspaceValidation = namedtuple('WorkspaceValidation', ['is_valid', 'errors', 'warnings'])

class WorkspaceManager(models.Manager):
    """Provides additional methods for handling workspaces."""

    @transaction.atomic
    def create_workspace(self, name, title, description, configuration, base_url=None, is_active=True):
        """Creates a new Workspace with the given configuration and returns the new Workspace model.
        The Workspace model will be saved in the database and all changes to the database will occur in an atomic
        transaction.

        :param name: The identifying name of this Workspace
        :type name: string
        :param title: The human-readable name of this Workspace
        :type title: string
        :param description: A description of this Workspace
        :type description: string
        :param configuration: The Workspace configuration
        :type configuration: :class:`storage.configuration.workspace_configuration.WorkspaceConfiguration`
        :param base_url: The URL prefix used to download files stored in the Workspace.
        :type base_url: string
        :param is_active: Whether or not the Workspace is available for use.
        :type is_active: bool
        :returns: The new Workspace
        :rtype: :class:`storage.models.Workspace`

        :raises :class:`storage.configuration.exceptions.InvalidWorkspaceConfiguration`: If the configuration is invalid
        """

        # Validate the configuration, no exception is success
        configuration.validate_broker()

        workspace = Workspace()
        workspace.name = name
        workspace.title = title
        workspace.description = description
        workspace.json_config = configuration.get_dict()
        workspace.base_url = base_url
        workspace.is_active = is_active
        workspace.save()
        return workspace

    @transaction.atomic
    def edit_workspace(self, workspace_id, title=None, description=None, configuration=None, base_url=None,
                       is_active=None):
        """Edits the given Workspace and saves the changes in the database. All database changes occur in an atomic
        transaction. An argument of None for a field indicates that the field should not change.

        :param workspace_id: The unique identifier of the Workspace to edit
        :type workspace_id: int
        :param title: The human-readable name of this Workspace
        :type title: string
        :param description: A description of this Workspace
        :type description: string
        :param configuration: The Workspace configuration
        :type configuration: :class:`storage.configuration.workspace_configuration.WorkspaceConfiguration`
        :param base_url: The URL prefix used to download files stored in the Workspace.
        :type base_url: string
        :param is_active: Whether or not the Workspace is available for use.
        :type is_active: bool

        :raises :class:`storage.configuration.exceptions.InvalidWorkspaceConfiguration`: If the configuration is invalid
        """

        workspace = Workspace.objects.get(pk=workspace_id)

        # Validate the configuration, no exception is success
        if configuration:
            configuration.validate_broker()
            workspace.json_config = configuration.get_dict()

        # Update editable fields
        if title:
            workspace.title = title
        if description:
            workspace.description = description
        if base_url:
            workspace.base_url = base_url
        if is_active is not None:
            workspace.is_active = is_active
        workspace.save()

    def get_details(self, workspace_id):
        """Returns the workspace for the given ID with all detail fields included.

        There are currently no additional fields included.

        :param workspace_id: The unique identifier of the workspace.
        :type workspace_id: int
        :returns: The workspace with all detail fields included.
        :rtype: :class:`storage.models.Workspace`
        """

        # Attempt to get the workspace
        workspace = Workspace.objects.get(pk=workspace_id)

        return workspace

    def get_workspaces(self, started=None, ended=None, names=None, order=None):
        """Returns a list of workspaces within the given time range.

        :param started: Query workspaces updated after this amount of time.
        :type started: :class:`datetime.datetime`
        :param ended: Query workspaces updated before this amount of time.
        :type ended: :class:`datetime.datetime`
        :param names: Query workspaces with the given name.
        :type names: [string]
        :param order: A list of fields to control the sort order.
        :type order: [string]
        :returns: The list of workspaces that match the time range.
        :rtype: [:class:`storage.models.Workspace`]
        """

        # Fetch a list of workspaces
        workspaces = Workspace.objects.all()

        # Apply time range filtering
        if started:
            workspaces = workspaces.filter(last_modified__gte=started)
        if ended:
            workspaces = workspaces.filter(last_modified__lte=ended)

        # Apply additional filters
        if names:
            workspaces = workspaces.filter(name__in=names)

        # Apply sorting
        if order:
            workspaces = workspaces.order_by(*order)
        else:
            workspaces = workspaces.order_by('last_modified')
        return workspaces

    def validate_workspace_v5(self, name, json_config):
        """Validates a new workspace prior to attempting a save

        :param name: The identifying name of a Workspace to validate
        :type name: string
        :param json_config: The Workspace configuration
        :type json_config: dict
        :returns: A list of warnings discovered during validation.
        :rtype: list[:class:`storage.configuration.workspace_configuration.ValidationWarning`]

        :raises :class:`storage.configuration.exceptions.InvalidWorkspaceConfiguration`: If the configuration is invalid
        """
        warnings = []

        # Validate the configuration, no exception is success
        config = WorkspaceConfigurationV1(json_config, do_validate=True).get_configuration()

        # Check for issues when changing an existing workspace configuration
        try:
            workspace = Workspace.objects.get(name=name)

            # Assign to short names in the interest of single-line conditional
            old_conf = workspace.json_config
            new_conf = json_config

            if new_conf['broker'] and old_conf['broker'] and new_conf['broker']['type'] != old_conf['broker']['type']:
                warnings.append(ValidationWarning('broker_type',
                                                  'Changing the broker type may disrupt queued/running jobs.'))
        except Workspace.DoesNotExist:
            pass

        # Add broker-specific warnings
        warnings.extend(config.validate_broker())
        return warnings
        
    def validate_workspace_v6(self, name, configuration):
        """Validates a new workspace prior to attempting a save

        :param name: The identifying name of a Workspace to validate
        :type name: string
        :param configuration: The Workspace configuration
        :type configuration: dict
        :returns: The workspace validation.
        :rtype: :class:`storage.models.WorkspaceValidation`
        """
        
        is_valid = True
        errors = []
        warnings = []
        
        config = None

        # Validate the configuration, no exception is success
        try:
            config = WorkspaceConfigurationV6(configuration, do_validate=True).get_configuration()
            # Add broker-specific warnings
            warnings.extend(config.validate_broker())
        except InvalidWorkspaceConfiguration as ex:
            is_valid = False
            errors.append(ex.error)
            message = 'Workspace configuration invalid'
            logger.exception(message)
            pass

        # Check for issues when changing an existing workspace configuration
        try:
            workspace = Workspace.objects.get(name=name)

            # Assign to short names in the interest of single-line conditional
            old_conf = workspace.json_config
            new_conf = configuration

            if new_conf['broker'] and old_conf['broker'] and new_conf['broker']['type'] != old_conf['broker']['type']:
                warnings.append(ValidationWarning('broker_type',
                                                  'Changing the broker type may disrupt queued/running jobs.'))
        except Workspace.DoesNotExist:
            pass

        return WorkspaceValidation(is_valid, errors, warnings)



class Workspace(models.Model):
    """Represents a storage location where files can be stored and retrieved
    for processing

    :keyword name: The identifying name of the workspace used by clients for queries
    :type name: :class:`django.db.models.CharField`
    :keyword title: The human-readable name of the workspace
    :type title: :class:`django.db.models.CharField`
    :keyword description: An optional description of the workspace
    :type description: :class:`django.db.models.CharField`
    :keyword base_url: The base URL used to retrieve files from this workspace if supported.
    :type base_url: str
    :keyword is_active: Whether the workspace is active (can be used and displayed)
    :type is_active: :class:`django.db.models.BooleanField`

    :keyword json_config: JSON configuration describing how to store/retrieve files for this workspace
    :type json_config: :class:`django.contrib.postgres.fields.JSONField`
    :keyword is_move_enabled: Whether the workspace allows files to be moved within it
    :type is_move_enabled: :class:`django.db.models.BooleanField`

    :keyword created: When the workspace was created
    :type created: :class:`django.db.models.DateTimeField`
    :keyword deprecated: When the workspace was archived (no longer active)
    :type deprecated: :class:`django.db.models.DateTimeField`
    :keyword last_modified: When the workspace was last modified
    :type last_modified: :class:`django.db.models.DateTimeField`
    """

    name = models.CharField(db_index=True, max_length=50, unique=True)
    title = models.CharField(blank=True, max_length=50, null=True)
    description = models.CharField(blank=True, max_length=500)
    base_url = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    json_config = django.contrib.postgres.fields.JSONField(default=dict)
    is_move_enabled = models.BooleanField(default=True)

    created = models.DateTimeField(auto_now_add=True)
    deprecated = models.DateTimeField(blank=True, null=True)
    last_modified = models.DateTimeField(auto_now=True)

    objects = WorkspaceManager()

    @property
    def volume(self):
        """If this workspace's broker uses a container volume, this property returns the information needed to set up a
        volume that can be mounted into the task container. If this workspace's broker does not use a container volume,
        this property should be None.

        :returns: The container volume information needed for this workspace's broker, possibly None
        :rtype: :class:`storage.brokers.broker.BrokerVolume`
        """

        return self.get_broker().volume

    @property
    def workspace_volume_path(self):
        """Returns the absolute local path within the container onto which the broker's container volume is mounted

        :returns: The absolute local path within the container for the broker's volume
        :rtype: string
        """

        return get_workspace_volume_path(self.name)

    def delete_files(self, files):
        """Deletes the given files using the workspace's broker and saves the ScaleFile model changes in the database.
        If this workspace's broker uses a container volume, the workspace expects this volume file system to already be
        mounted at workspace_volume_path or an exception will be raised.

        :param files: List of files to delete
        :type files: [:class:`storage.models.ScaleFile`]

        :raises :class:`storage.exceptions.MissingVolumeMount`: If the required volume mount is missing
        """

        volume_path = self._get_volume_path()
        self.get_broker().delete_files(volume_path, files)

    def download_files(self, file_downloads):
        """Downloads the given files to the given local file system paths using the workspace's broker. If this
        workspace's broker uses a container volume, the workspace expects this volume file system to already be mounted
        at workspace_volume_path or an exception will be raised.

        :param file_downloads: List of files to download
        :type file_downloads: [:class:`storage.brokers.broker.FileDownload`]

        :raises :class:`storage.exceptions.MissingVolumeMount`: If the required volume mount is missing
        """

        volume_path = self._get_volume_path()

        # Create parent directories for the local download paths if necessary
        for file_download in file_downloads:
            file_download_dir = os.path.dirname(file_download.local_path)
            if not os.path.exists(file_download_dir):
                logger.info('Creating %s', file_download_dir)
                makedirs(file_download_dir, mode=0755)

        self.get_broker().download_files(volume_path, file_downloads)

    def get_broker(self):
        """Returns the configured broker for this workspace

        :returns: The configured broker
        :rtype: :class:`storage.brokers.broker.Broker`
        """

        if not hasattr(self, '_broker'):
            ws_config = WorkspaceConfigurationV6(self.json_config).get_configuration()
            ws_config.validate_broker()

            broker_config = self.json_config['broker']
            broker_type = broker_config['type']
            broker = get_broker(broker_type)
            broker.load_configuration(broker_config)
            self._broker = broker
        return self._broker

    def get_file_system_paths(self, files):
        """Returns the local file system paths for the given files, if supported by the workspace's broker. If this
        workspace's broker uses a container volume, the workspace expects this volume file system to already be mounted
        at workspace_volume_path or an exception will be raised.

        :param files: List of files
        :type files: [:class:`storage.models.ScaleFile`]
        :returns: The list of local file system paths if supported, None otherwise
        :rtype: [string]
        """

        volume_path = self._get_volume_path()
        return self.get_broker().get_file_system_paths(volume_path, files)

    def get_configuration(self):
        """Returns the workspace configuration object

        :returns: The configuration in v2 of the JSON schema
        :rtype: dict
        """

        return WorkspaceConfigurationV6(self.json_config).get_configuration()

    def get_v6_configuration_json(self):
        """Returns the workspace configuration in v6 of the JSON schema

        :returns: The workspace configuration in v6 of the JSON schema
        :rtype: dict
        """

        return rest_utils.strip_schema_version(convert_config_to_v6_json(self.get_configuration()).get_dict())

    def list_files(self, recursive):
        """Lists files within a workspace, with optional full tree recursion.

        :param recursive: Flag to indicate whether file searching should be done recursively
        :type recursive: boolean
        :return: Generator of files matching given expression
        :rtype: Generator[:class:`storage.brokers.broker.FileDetails`]
        """
        volume_path = self._get_volume_path()

        logger.info('Beginning%s file list for workspace: %s' % (' recursive' if recursive else '',
                                                                   self.name))
        return self.get_broker().list_files(volume_path, recursive)

    def move_files(self, file_moves):
        """Moves the given files to the new file system paths and saves the ScaleFile model changes in the database. If
        this workspace's broker uses a container volume, the workspace expects this volume file system to already be
        mounted at workspace_volume_path or an exception will be raised.

        :param file_moves: List of files to move
        :type file_moves: [:class:`storage.brokers.broker.FileMove`]

        :raises :class:`storage.exceptions.MissingVolumeMount`: If the required volume mount is missing
        """

        volume_path = self._get_volume_path()
        self.get_broker().move_files(volume_path, file_moves)

    def upload_files(self, file_uploads):
        """Uploads the given files from the given local file system paths and saves the ScaleFile models in the
        database. If this workspace's broker uses a container volume, the workspace expects this volume file system to
        already be mounted at workspace_volume_path or an exception will be raised.

        :param file_uploads: List of files to upload
        :type file_uploads: [:class:`storage.brokers.broker.FileUpload`]

        :raises :class:`storage.exceptions.MissingVolumeMount`: If the required volume mount is missing
        """

        volume_path = self._get_volume_path()
        self.get_broker().upload_files(volume_path, file_uploads)

    def _get_volume_path(self):
        """Returns the local container location for this workspace's container volume if it uses one, otherwise returns
        None. If the workspace uses a container volume and it is missing, an exception is raised.

        :returns: The absolute local path within the container for the container volume, possibly None
        :rtype: string
        :raises :class:`storage.exceptions.MissingVolumeMount`: If the required volume mount is missing
        """

        volume_path = None
        if self.volume:
            volume_path = self.workspace_volume_path
            if not os.path.exists(volume_path):
                raise MissingVolumeMount('Expected file system mounted at %s' % volume_path)
        return volume_path

    class Meta(object):
        """meta information for the db"""
        db_table = 'workspace'
