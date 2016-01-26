'''Defines the database model for source files'''
import logging
import os

import django.contrib.gis.db.models as models
from django.db import transaction
from django.utils.timezone import now

import storage.geospatial_utils as geo_utils
from source.triggers.parse_trigger_handler import ParseTriggerHandler
from storage.exceptions import DuplicateFile
from storage.models import ScaleFile
from util.command import execute_command_line


logger = logging.getLogger(__name__)


class SourceFileManager(models.GeoManager):
    '''Provides additional methods for handling source files
    '''

    def get_sources(self, started=None, ended=None, is_parsed=None, file_name=None, order=None):
        '''Returns a list of source files within the given time range.

        :param started: Query source files updated after this amount of time.
        :type started: :class:`datetime.datetime`
        :param ended: Query source files updated before this amount of time.
        :type ended: :class:`datetime.datetime`
        :param is_parsed: Query source files flagged as successfully parsed.
        :type is_parsed: bool
        :param file_name: Query source files with the given file name.
        :type file_name: str
        :param order: A list of fields to control the sort order.
        :type order: list[str]
        :returns: The list of source files that match the time range.
        :rtype: list[:class:`source.models.SourceFile`]
        '''

        # Fetch a list of source files
        sources = SourceFile.objects.all()
        sources = sources.select_related('workspace').defer('workspace__json_config')
        sources = sources.prefetch_related('countries')

        # Apply time range filtering
        if started:
            sources = sources.filter(last_modified__gte=started)
        if ended:
            sources = sources.filter(last_modified__lte=ended)

        if is_parsed is not None:
            sources = sources.filter(is_parsed=is_parsed)
        if file_name:
            sources = sources.filter(file_name=file_name)

        # Apply sorting
        if order:
            sources = sources.order_by(*order)
        else:
            sources = sources.order_by('last_modified')

        return sources

    @transaction.atomic
    def save_parse_results(self, src_file_id, geo_json, data_started, data_ended, data_types, new_workspace_path,
                           work_dir):
        '''Saves the given parse results to the source file for the given ID. All database changes occur in an atomic
        transaction.

        :param src_file_id: The ID of the source file
        :type src_file_id: int
        :param geo_json: The associated geojson data, possibly None
        :type geo_json: dict
        :param data_started: The start time of the data contained in the source file, possibly None
        :type data_started: :class:`datetime.datetime` or None
        :param data_ended: The end time of the data contained in the source file, possibly None
        :type data_ended: :class:`datetime.datetime` or None
        :param data_types: List of strings containing the data types tags for this source file.
        :type data_types: list
        :param new_workspace_path: New workspace path to move the source file to now that parse data is available. If
            None, the source file should not be moved.
        :type new_workspace_path: str
        :param work_dir: Absolute path to a local work directory available to assist in moving the source file. Only
            needed if new_workspace_path is not None.
        :type work_dir: str
        '''

        geom = None
        props = None
        if geo_json:
            geom, props = geo_utils.parse_geo_json(geo_json)

        # Acquire model lock
        src_file = SourceFile.objects.select_for_update().get(pk=src_file_id)
        src_file.is_parsed = True
        src_file.parsed = now()
        src_file.data_started = data_started
        src_file.data_ended = data_ended
        target_date = src_file.data_started
        if target_date is None:
            target_date = src_file.data_ended
        if target_date is None:
            target_date = src_file.created
        for tag in data_types:
            src_file.add_data_type_tag(tag)
        if geom:
            src_file.geometry = geom
            src_file.center_point = geo_utils.get_center_point(geom)
        src_file.meta_data = props
        # src_file already exists so we don't need to save/set_countries/save, just a single save is fine
        src_file.set_countries()
        src_file.save()

        # Move the source file if a new workspace path is provided
        if new_workspace_path:
            old_workspace_path = src_file.file_path
            ScaleFile.objects.move_files(work_dir, [(src_file, new_workspace_path)])

        try:
            # Check trigger rules for parsed source files
            ParseTriggerHandler().process_parsed_source_file(src_file)
        except Exception:
            # Move file back if there was an error
            if new_workspace_path:
                ScaleFile.objects.move_files(work_dir, [(src_file, old_workspace_path)])

            raise

    def store_file(self, work_dir, local_path, data_types, workspace, remote_path):
        '''Stores the given local source file in the workspace

        :param work_dir: Absolute path to a local work directory available to assist in storing the source file
        :type work_dir: str
        :param local_path: The absolute local path of the source file to store
        :type local_path: str
        :param data_types: The data type tags of the source file
        :type data_types: list of str
        :param workspace: The workspace to use for storing the source file
        :type workspace: :class:`storage.models.Workspace`
        :param remote_path: The relative path for storing the source file
        :type remote_path: str
        :returns: The model of the saved source file
        :rtype: :class:`source.models.SourceFile`
        '''

        file_name = os.path.basename(local_path)
        upload_dir = os.path.join(work_dir, 'upload')
        workspace_work_dir = os.path.join(work_dir, 'work')
        if not os.path.exists(upload_dir):
            logger.info('Creating %s', upload_dir)
            os.mkdir(upload_dir, 0755)
        if not os.path.exists(workspace_work_dir):
            logger.info('Creating %s', workspace_work_dir)
            os.mkdir(workspace_work_dir, 0755)
        upload_file_path = os.path.join(upload_dir, file_name)

        ScaleFile.objects.setup_upload_dir(upload_dir, workspace_work_dir, workspace)
        try:
            # Check for duplicate file, else create new file
            # TODO: fix race condition with many files with same name?
            try:
                src_file = SourceFile.objects.get(file_name=file_name)
                # Duplicate files that are deleted should be stored again
                if not src_file.is_deleted:
                    raise DuplicateFile(u'\'%s\' already exists' % file_name)
            except SourceFile.DoesNotExist:
                src_file = SourceFile()  # New file

            # Add a stable identifier based on the file name
            src_file.update_uuid(file_name)

            # Add tags and store the new/updated source file
            for tag in data_types:
                src_file.add_data_type_tag(tag)

            # Link source file into upload directory and upload it
            if not os.path.islink(upload_file_path):
                logger.info('Creating link %s -> %s', upload_file_path, local_path)
                execute_command_line(['ln', '-s', local_path, upload_file_path])
            return ScaleFile.objects.upload_files(upload_dir, workspace_work_dir, workspace,
                                                  [(src_file, file_name, remote_path)])[0]
        finally:
            ScaleFile.objects.cleanup_upload_dir(upload_dir, workspace_work_dir, workspace)


class SourceFile(ScaleFile):
    '''Represents a source data file that is available for processing. This is an extension of the
    :class:`storage.models.ScaleFile` model.

    :keyword file: The corresponding ScaleFile model
    :type file: :class:`django.db.models.OneToOneField`

    :keyword is_parsed: Whether the source file has been parsed or not
    :type is_parsed: :class:`django.db.models.BooleanField`
    :keyword parsed: When the source file was parsed
    :type parsed: :class:`django.db.models.DateTimeField`
    '''

    file = models.OneToOneField(u'storage.ScaleFile', primary_key=True, parent_link=True)

    is_parsed = models.BooleanField(default=False)
    parsed = models.DateTimeField(blank=True, null=True)

    objects = SourceFileManager()

    class Meta(object):
        '''meta information for the db'''
        db_table = u'source_file'
