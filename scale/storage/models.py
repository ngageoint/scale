"""Defines the database models for file information and workspaces"""
from __future__ import unicode_literals

import hashlib
import logging
import os
import re

import djorm_pgjson.fields
from django.db import transaction
from django.db.models.aggregates import Sum
from django.utils.text import get_valid_filename

import django.contrib.gis.db.models as models
import django.contrib.gis.geos as geos
import storage.geospatial_utils as geospatial_utils
from storage.brokers.factory import get_broker
from storage.exceptions import ArchivedWorkspace, DeletedFile, InvalidDataTypeTag
from storage.media_type import get_media_type
from storage.nfs import nfs_umount


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
        :type name: str
        :param border: The new border geometry. Either GEOSGeometry or geojson (which will be converted to GEOSGeometry)
        :type border: GEOSGeometry or str
        :param effective: The effective date for the new border. If None, now() will be used
        :type data_started: :class:`datetime.datetime`
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
        :type name: str
        :param iso2: The iso2 abbreviation of the country. Mutually exclusive with name. One of these is required.
        :type name: str
        :rval: A query set
        :rtype: :class:`django.db.models.query.QuerySet`
        """
        assert((name is not None and iso2 is None) or (iso2 is not None and name is None))
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
        :rval: A dict of intersected countries mapped to enties
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

    def cleanup_download_dir(self, download_dir, work_dir):
        """Performs any cleanup necessary for a previous download_files() call

        :param download_dir: Absolute path to the local directory for the files to download
        :type download_dir: str
        :param work_dir: Absolute path to a local work directory available to assist in downloading
        :type work_dir: str
        """

        download_dir = os.path.normpath(download_dir)
        work_dir = os.path.normpath(work_dir)
        workspace_root_dir = self._get_workspace_root_dir(work_dir)

        for workspace in Workspace.objects.all():
            workspace_work_dir = self._get_workspace_work_dir(work_dir, workspace)
            if os.path.exists(workspace_work_dir):
                workspace.cleanup_download_dir(download_dir, workspace_work_dir)
                logger.info('Deleting %s', workspace_work_dir)
                os.rmdir(workspace_work_dir)

        if os.path.exists(workspace_root_dir):
            logger.info('Deleting %s', workspace_root_dir)
            os.rmdir(workspace_root_dir)

    def cleanup_move_dir(self, work_dir):
        """Performs any cleanup necessary for a previous move_files() call

        :param work_dir: Absolute path to a local work directory available to assist in moving
        :type work_dir: str
        :param workspace: The workspace to upload files into
        :type workspace: :class:`storage.models.Workspace`
        """

        work_dir = os.path.normpath(work_dir)

        workspace_root_dir = self._get_workspace_root_dir(work_dir)

        if os.path.exists(workspace_root_dir):
            for name in os.listdir(workspace_root_dir):
                sub_dir = os.path.join(workspace_root_dir, name)
                nfs_umount(sub_dir)
                logger.info('Deleting %s', sub_dir)
                os.rmdir(sub_dir)
            logger.info('Deleting %s', workspace_root_dir)
            os.rmdir(workspace_root_dir)

    def cleanup_upload_dir(self, upload_dir, work_dir, workspace):
        """Performs any cleanup necessary for a previous setup_upload_dir() call

        :param upload_dir: Absolute path to the local directory of the files to upload
        :type upload_dir: str
        :param work_dir: Absolute path to a local work directory available to assist in uploading
        :type work_dir: str
        :param workspace: The workspace to upload files into
        :type workspace: :class:`storage.models.Workspace`
        """

        upload_dir = os.path.normpath(upload_dir)
        work_dir = os.path.normpath(work_dir)

        delete_root_dir = self._get_delete_root_dir(work_dir)
        delete_work_dir = self._get_delete_work_dir(work_dir, workspace)
        workspace_root_dir = self._get_workspace_root_dir(work_dir)
        workspace_work_dir = self._get_workspace_work_dir(work_dir, workspace)

        if os.path.exists(workspace_work_dir):
            workspace.cleanup_upload_dir(upload_dir, workspace_work_dir)
            logger.info('Deleting %s', workspace_work_dir)
            os.rmdir(workspace_work_dir)
            if not os.listdir(workspace_root_dir):
                logger.info('Deleting %s', workspace_root_dir)
                os.rmdir(workspace_root_dir)

        if os.path.exists(delete_work_dir):
            nfs_umount(delete_work_dir)
            logger.info('Deleting %s', delete_work_dir)
            os.rmdir(delete_work_dir)
            if not os.listdir(delete_root_dir):
                logger.info('Deleting %s', delete_root_dir)
                os.rmdir(delete_root_dir)

    def download_files(self, download_dir, work_dir, files_to_download):
        """Downloads the given Scale files into the given download directory. After all use of the downloaded files is
        complete, the caller should call cleanup_download_dir(). Each ScaleFile model should have its related workspace
        field populated.

        :param download_dir: Absolute path to the local directory for the files to download
        :type download_dir: str
        :param work_dir: Absolute path to a local work directory available to assist in downloading. This directory must
            not be within the download directory.
        :type work_dir: str
        :param files_to_download: List of tuples (Scale file, destination path relative to download directory)
        :type files_to_download: list of (:class:`storage.models.ScaleFile`, str)
        """

        download_dir = os.path.normpath(download_dir)
        work_dir = os.path.normpath(work_dir)

        # {Workspace ID: (workspace, list of (file_path, local_path))}
        wp_dict = {}
        # Organize files by workspace
        for entry in files_to_download:
            scale_file = entry[0]
            download_path = entry[1]
            workspace_path = scale_file.file_path
            workspace = scale_file.workspace
            if not workspace.is_active:
                raise ArchivedWorkspace('%s is no longer active' % workspace.name)
            if scale_file.is_deleted:
                raise DeletedFile('%s has been deleted' % scale_file.file_name)
            if workspace.id in wp_dict:
                wp_list = wp_dict[workspace.id][1]
            else:
                wp_list = []
                wp_dict[workspace.id] = (workspace, wp_list)
            wp_list.append((workspace_path, download_path))

        # Retrieve files for each workspace
        for wp_id in wp_dict:
            workspace = wp_dict[wp_id][0]
            download_file_list = wp_dict[wp_id][1]
            workspace_work_dir = self._get_workspace_work_dir(work_dir, workspace)
            logger.info('Creating %s', workspace_work_dir)
            os.makedirs(workspace_work_dir, mode=0755)
            workspace.setup_download_dir(download_dir, workspace_work_dir)
            workspace.download_files(download_dir, workspace_work_dir, download_file_list)

    def get_total_file_size(self, file_ids):
        """Returns the total file size of the given file IDs in bytes

        :param files: List of file IDs
        :type files: list[int]
        :returns: Total file size in bytes
        :rtype: long
        """

        results = ScaleFile.objects.filter(id__in=file_ids).aggregate(Sum('file_size'))

        file_size = 0
        if 'file_size__sum' in results:
            file_size_sum = results['file_size__sum']
            if file_size_sum is not None:
                file_size = long(file_size_sum)
        return file_size

    @transaction.atomic
    def move_files(self, work_dir, files_to_move):
        """Moves the given Scale files to the new workspace location. Each ScaleFile model should have its related
        workspace field populated and the caller must have obtained a model lock on each using select_for_update().

        :param work_dir: Absolute path to a local work directory available to assist in moving
        :type work_dir: str
        :param files_to_move: List of tuples (Scale file, destination workspace path)
        :type files_to_move: list of (:class:`storage.models.ScaleFile`, str)
        """

        # {Workspace ID: (workspace, list of (workspace_path, new_workspace_path))}
        wp_dict = {}
        # Organize files by workspace
        for entry in files_to_move:
            scale_file = entry[0]
            new_workspace_path = self._correct_workspace_path(entry[1])
            workspace_path = scale_file.file_path
            workspace = scale_file.workspace
            if not workspace.is_active:
                raise ArchivedWorkspace('%s is no longer active' % workspace.name)
            if scale_file.is_deleted:
                raise DeletedFile('%s has been deleted' % scale_file.file_name)
            if workspace.id in wp_dict:
                wp_list = wp_dict[workspace.id][1]
            else:
                wp_list = []
                wp_dict[workspace.id] = (workspace, wp_list)
            wp_list.append((workspace_path, new_workspace_path))
            # Update workspace path in model
            scale_file.file_path = new_workspace_path
            scale_file.save()

        # Move files for each workspace
        for wp_id in wp_dict:
            workspace = wp_dict[wp_id][0]
            move_file_list = wp_dict[wp_id][1]
            workspace_work_dir = self._get_workspace_work_dir(work_dir, workspace)
            logger.info('Creating %s', workspace_work_dir)
            os.makedirs(workspace_work_dir, mode=0755)
            workspace.move_files(workspace_work_dir, move_file_list)

    def setup_upload_dir(self, upload_dir, work_dir, workspace):
        """Sets up the given upload directory to upload Scale files into the given workspace. Note that moving/copying
        files into an upload directory after this method has been called may be expensive as the setup upload directory
        may not be a local directory.

        :param upload_dir: Absolute path to the local directory of the files to upload
        :type upload_dir: str
        :param work_dir: Absolute path to a local work directory available to assist in uploading. This directory must
            not be within the upload directory.
        :type work_dir: str
        :param workspace: The workspace to upload files into
        :type workspace: :class:`storage.models.Workspace`
        """

        upload_dir = os.path.normpath(upload_dir)
        work_dir = os.path.normpath(work_dir)
        workspace_work_dir = self._get_workspace_work_dir(work_dir, workspace)

        if not os.path.exists(workspace_work_dir):
            logger.info('Creating %s', workspace_work_dir)
            os.makedirs(workspace_work_dir, mode=0755)

        workspace.setup_upload_dir(upload_dir, workspace_work_dir)

    def upload_files(self, upload_dir, work_dir, workspace, files_to_upload):
        """Uploads the given files in the given upload directory into the workspace. This method assumes that
        setup_upload_dir() has already been called with the same upload and work directories. The ScaleFile models will
        be saved in an atomic database transaction.

        :param upload_dir: Absolute path to the local directory of the files to upload
        :type upload_dir: str
        :param work_dir: Absolute path to a local work directory available to assist in uploading
        :type work_dir: str
        :param workspace: The workspace to upload files into
        :type workspace: :class:`storage.models.Workspace`
        :param files_to_upload: List of tuples (ScaleFile model, source path relative to upload directory, workspace
            path for storing the file)
        :type files_to_upload: list of (:class:`storage.models.ScaleFile`, str, str)
        :returns: The list of the saved file models
        :rtype: list of :class:`storage.models.ScaleFile`
        """

        upload_dir = os.path.normpath(upload_dir)
        work_dir = os.path.normpath(work_dir)
        workspace_work_dir = self._get_workspace_work_dir(work_dir, workspace)

        file_list = []
        wksp_upload_list = []   # Info to pass the workspace so it can upload files
        wksp_delete_list = []   # Info needed to delete the files if the database save fails
        for entry in files_to_upload:
            scale_file = entry[0]
            upload_path = entry[1]
            workspace_path = entry[2]
            full_upload_path = os.path.join(upload_dir, upload_path)
            media_type = scale_file.media_type

            # Determine file properties
            file_name = os.path.basename(full_upload_path)
            if not media_type:
                media_type = get_media_type(file_name)
            file_size = os.path.getsize(full_upload_path)

            scale_file.file_name = file_name
            scale_file.media_type = media_type
            scale_file.file_size = file_size
            scale_file.file_path = workspace_path
            scale_file.workspace = workspace
            scale_file.is_deleted = False
            scale_file.deleted = None

            file_list.append(scale_file)
            wksp_upload_list.append((upload_path, workspace_path))
            wksp_delete_list.append(workspace_path)

        try:
            # Store files in workspace
            workspace.upload_files(upload_dir, workspace_work_dir, wksp_upload_list)

            with transaction.atomic():
                for scale_file in file_list:
                    # save to create a pkey, update the country list, then save again
                    scale_file.save()
                    scale_file.set_countries()
                    scale_file.save()

            return file_list
        except Exception as ex:
            # Attempt to clean up failed files before propagating exception
            try:
                delete_work_dir = self._get_delete_work_dir(work_dir, workspace)
                logger.info('Creating %s', delete_work_dir)
                os.makedirs(delete_work_dir, mode=0755)
                workspace.delete_files(delete_work_dir, wksp_delete_list)
            except Exception:
                # Failure to delete should not override ex
                logger.exception('Error cleaning up files that failed to upload')
            raise ex

    def _correct_workspace_path(self, workspace_path):
        """Applies any needed corrections to the given workspace path (path should be normalized and relative)

        :param workspace_path: The workspace path to correct
        :type workspace_path: str
        :returns: The corrected workspace path
        :rtype: str
        """

        # Make sure path is relative
        if os.path.isabs(workspace_path):
            root_path = os.path.abspath(os.sep)
            workspace_path = os.path.relpath(workspace_path, root_path)

        return os.path.normpath(workspace_path)

    def _get_delete_root_dir(self, work_dir):
        """Returns the root directory for workspace sub-directories used for deleting files

        :param work_dir: Absolute path to a local work directory available to Scale
        :type work_dir: str
        """

        return os.path.join(work_dir, 'delete')

    def _get_delete_work_dir(self, work_dir, workspace):
        """Returns a work sub-directory used to delete files from the given workspace

        :param work_dir: Absolute path to a local work directory available to Scale
        :type work_dir: str
        :param workspace: The workspace
        :type workspace: :class:`storage.models.Workspace`
        """

        return os.path.join(self._get_delete_root_dir(work_dir), get_valid_filename(workspace.name))

    def _get_workspace_root_dir(self, work_dir):
        """Returns the root directory for workspace work sub-directories

        :param work_dir: Absolute path to a local work directory available to Scale
        :type work_dir: str
        """

        return os.path.join(work_dir, 'workspaces')

    def _get_workspace_work_dir(self, work_dir, workspace):
        """Returns a work sub-directory for the given workspace

        :param work_dir: Absolute path to a local work directory available to Scale
        :type work_dir: str
        :param workspace: The workspace
        :type workspace: :class:`storage.models.Workspace`
        """

        return os.path.join(self._get_workspace_root_dir(work_dir), get_valid_filename(workspace.name))


class ScaleFile(models.Model):
    """Represents a file that is stored within a Scale workspace

    :keyword id: The ID of the file
    :type id: :class:`storage.models.BigAutoField`
    :keyword file_name: The name of the file
    :type file_name: :class:`django.db.models.CharField`
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
    :type meta_data: :class:`djorm_pgjson.fields.JSONField`
    :keyword countries: List of countries represented in this file as indicated by the file's geometry.
    :type countries: :class:`django.db.models.ManyToManyField` of :class:`storage.models.CountryData`
    """

    file_name = models.CharField(max_length=250, db_index=True)
    media_type = models.CharField(max_length=250)
    file_size = models.BigIntegerField()
    data_type = models.TextField(blank=True)
    file_path = models.CharField(max_length=1000)
    workspace = models.ForeignKey('storage.Workspace', on_delete=models.PROTECT)
    is_deleted = models.BooleanField(default=False)
    uuid = models.CharField(db_index=True, max_length=32)

    created = models.DateTimeField(auto_now_add=True)
    deleted = models.DateTimeField(blank=True, null=True)
    last_modified = models.DateTimeField(auto_now=True, db_index=True)

    # Optional geospatial fields
    data_started = models.DateTimeField(blank=True, null=True, db_index=True)
    data_ended = models.DateTimeField(blank=True, null=True)
    geometry = models.GeometryField('Geometry', blank=True, null=True, srid=4326)
    center_point = models.PointField(blank=True, null=True, srid=4326)
    meta_data = djorm_pgjson.fields.JSONField()
    countries = models.ManyToManyField(CountryData)

    objects = ScaleFileManager()

    def update_uuid(self, *args):
        """Computes and sets a new UUID value for this file by hashing the given arguments.

        :param args: One or more input objects to hash.
        :type args: list[str]
        :returns: The generated unique identifier.
        :rtype: str
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
        :type tag: str
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
        :rtype: set of str
        """

        tags = set()
        if self.data_type:
            for tag in self.data_type.split(','):
                tags.add(tag)
        return tags

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

    def _set_data_type_tags(self, tags):
        """Sets the data type tags on the model

        :param tags: The data type tags
        :type tags: set of str
        """

        self.data_type = ','.join(tags)

    def _get_url(self):
        """Gets the absolute URL used to download this file.

        Note that this property is only supported if the associated workspace supports HTTP downloads.

        :returns: The file download URL.
        :rtype: str
        """

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
    url = property(_get_url)

    class Meta(object):
        """meta information for the db"""
        db_table = 'scale_file'


class WorkspaceManager(models.Manager):
    """Provides additional methods for handling workspaces."""

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
        :type names: list[str]
        :param order: A list of fields to control the sort order.
        :type order: list[str]
        :returns: The list of workspaces that match the time range.
        :rtype: list[:class:`storage.models.Workspace`]
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


class Workspace(models.Model):
    """Represents a storage location where files can be stored and retrieved
    for processing

    :keyword name: The stable name of the workspace used by clients for queries
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
    :type json_config: :class:`djorm_pgjson.fields.JSONField`
    :keyword is_move_enabled: Whether the workspace allows files to be moved within it
    :type is_move_enabled: :class:`django.db.models.BooleanField`

    :keyword used_size: The number of used bytes, may be None (unknown)
    :type used_size: :class:`django.db.models.BigIntegerField`
    :keyword total_size: The total size of the workspace file system in bytes, may be None (unknown)
    :type total_size: :class:`django.db.models.BigIntegerField`

    :keyword created: When the workspace was created
    :type created: :class:`django.db.models.DateTimeField`
    :keyword archived: When the workspace was archived (no longer active)
    :type archived: :class:`django.db.models.DateTimeField`
    :keyword last_modified: When the workspace was last modified
    :type last_modified: :class:`django.db.models.DateTimeField`
    """

    name = models.CharField(db_index=True, max_length=50, unique=True)
    title = models.CharField(blank=True, max_length=50, null=True)
    description = models.CharField(blank=True, max_length=500)
    base_url = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    json_config = djorm_pgjson.fields.JSONField()
    is_move_enabled = models.BooleanField(default=True)

    used_size = models.BigIntegerField(blank=True, null=True)
    total_size = models.BigIntegerField(blank=True, null=True)

    created = models.DateTimeField(auto_now_add=True)
    archived = models.DateTimeField(blank=True, null=True)
    last_modified = models.DateTimeField(auto_now=True)

    objects = WorkspaceManager()

    def cleanup_download_dir(self, download_dir, work_dir):
        """Performs any cleanup necessary for a previous setup_download_dir() call

        :param download_dir: Absolute path to the local directory for the files to download
        :type download_dir: str
        :param work_dir: Absolute path to a local work directory available to the workspace
        :type work_dir: str
        """

        broker = self._get_broker()
        broker.cleanup_download_dir(download_dir, work_dir)

    def cleanup_upload_dir(self, upload_dir, work_dir):
        """Performs any cleanup necessary for a previous setup_upload_dir() call

        :param upload_dir: Absolute path to the local directory of the files to upload
        :type upload_dir: str
        :param work_dir: Absolute path to a local work directory available to the workspace
        :type work_dir: str
        """

        broker = self._get_broker()
        broker.cleanup_upload_dir(upload_dir, work_dir)

    def delete_files(self, work_dir, workspace_paths):
        """Deletes the workspace files with the given workspace paths

        :param work_dir: Absolute path to a local work directory available to the workspace
        :type work_dir: str
        :param workspace_paths: The relative workspace paths of the files to delete
        :type workspace_paths: list of str
        """

        broker = self._get_broker()
        broker.delete_files(work_dir, workspace_paths)

    def download_files(self, download_dir, work_dir, files_to_download):
        """Downloads the given workspace files into the given download directory. This method assumes that
        setup_download_dir() has already been called with the same download and work directories.

        :param download_dir: Absolute path to the local directory for the files to download
        :type download_dir: str
        :param work_dir: Absolute path to a local work directory available to the workspace
        :type work_dir: str
        :param files_to_download: List of tuples (workspace path of a file to download, destination path relative to
            download directory)
        :type files_to_download: list of (str, str)
        """

        broker = self._get_broker()
        broker.download_files(download_dir, work_dir, files_to_download)

    def move_files(self, work_dir, files_to_move):
        """Moves the workspace files to the new workspace paths

        :param work_dir: Absolute path to a local work directory available to the workspace
        :type work_dir: str
        :param files_to_move: List of tuples (current workspace path of a file to move, new workspace path for the file)
        :type files_to_move: list of (str, str)
        """

        broker = self._get_broker()
        broker.move_files(work_dir, files_to_move)

    def setup_download_dir(self, download_dir, work_dir):
        """Sets up the given download directory to download files from the workspace

        :param download_dir: Absolute path to the local directory for the files to download
        :type download_dir: str
        :param work_dir: Absolute path to a local work directory available to the workspace
        :type work_dir: str
        """

        broker = self._get_broker()
        broker.setup_download_dir(download_dir, work_dir)

    def setup_upload_dir(self, upload_dir, work_dir):
        """Sets up the given upload directory to upload files into the workspace

        :param upload_dir: Absolute path to the local directory of the files to upload
        :type upload_dir: str
        :param work_dir: Absolute path to a local work directory available to the workspace
        :type work_dir: str
        """

        broker = self._get_broker()
        broker.setup_upload_dir(upload_dir, work_dir)

    def upload_files(self, upload_dir, work_dir, files_to_upload):
        """Uploads the given files in the given upload directory into the workspace. This method assumes that
        setup_upload_dir() has already been called with the same upload and work directories.

        :param upload_dir: Absolute path to the local directory of the files to upload
        :type upload_dir: str
        :param work_dir: Absolute path to a local work directory available to the workspace
        :type work_dir: str
        :param files_to_upload: List of tuples (source path relative to upload directory, workspace path for storing the
            file)
        :type files_to_upload: list of (str, str)
        """

        broker = self._get_broker()
        broker.upload_files(upload_dir, work_dir, files_to_upload)

    def _get_broker(self):
        """Returns the configured broker for this workspace

        :returns: The configured broker
        :rtype: :class:`storage.brokers.broker.Broker`
        """

        broker_config = self.json_config['broker']
        broker_type = broker_config['type']
        broker = get_broker(broker_type)
        broker.load_config(broker_config)
        return broker

    class Meta(object):
        """meta information for the db"""
        db_table = 'workspace'
