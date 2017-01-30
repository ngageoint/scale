"""Defines the database model for source files"""
from __future__ import unicode_literals

import logging

import django.contrib.gis.db.models as models
from django.db import transaction
from django.utils.timezone import now

import storage.geospatial_utils as geo_utils
from source.triggers.parse_trigger_handler import ParseTriggerHandler
from storage.brokers.broker import FileMove
from storage.models import ScaleFile


logger = logging.getLogger(__name__)


class SourceFileManager(models.GeoManager):
    """Provides additional methods for handling source files
    """

    def get_source_file_by_name(self, file_name):
        """Returns the source file with the given file name

        :param file_name: The name of the source file
        :type file_name: string
        :returns: The list of source files that match the time range.
        :rtype: :class:`storage.models.ScaleFile`

        :raises :class:`storage.models.ScaleFile.DoesNotExist`: If the file does not exist
        """

        return ScaleFile.objects.get(file_name=file_name, file_type='SOURCE')

    def get_sources(self, started=None, ended=None, is_parsed=None, file_name=None, order=None):
        """Returns a list of source files within the given time range.

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
        :rtype: list[:class:`storage.models.ScaleFile`]
        """

        # Fetch a list of source files
        sources = ScaleFile.objects.all()
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

    def get_details(self, source_id, include_superseded=False):
        """Gets additional details for the given source model based on related model attributes.

        :param source_id: The unique identifier of the source.
        :type source_id: int
        :param include_superseded: Whether or not superseded products should be included.
        :type include_superseded: bool
        :returns: The source with extra related attributes: ingests and products.
        :rtype: :class:`storage.models.ScaleFile`

        :raises :class:`storage.models.ScaleFile.DoesNotExist`: If the file does not exist
        """

        # Attempt to fetch the requested source
        source = ScaleFile.objects.all().select_related('workspace')
        source = source.get(pk=source_id, file_type='SOURCE')

        # Attempt to fetch all ingests for the source
        # Use a localized import to make higher level application dependencies optional
        try:
            from ingest.models import Ingest
            source.ingests = Ingest.objects.filter(source_file=source).order_by('created')
        except:
            source.ingests = []

        # Attempt to fetch all products derived from the source
        products = ScaleFile.objects.filter(ancestors__ancestor_id=source.id, file_type='PRODUCT')
        # Exclude superseded products by default
        if not include_superseded:
            products = products.filter(is_superseded=False)
        products = products.select_related('job_type', 'workspace').defer('workspace__json_config')
        products = products.prefetch_related('countries').order_by('created')
        source.products = products

        return source

    @transaction.atomic
    def save_parse_results(self, src_file_id, geo_json, data_started, data_ended, data_types, new_workspace_path):
        """Saves the given parse results to the source file for the given ID. All database changes occur in an atomic
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
        :type data_types: [string]
        :param new_workspace_path: New workspace path to move the source file to now that parse data is available. If
            None, the source file should not be moved.
        :type new_workspace_path: str
        """

        geom = None
        props = None
        if geo_json:
            geom, props = geo_utils.parse_geo_json(geo_json)

        # Acquire model lock
        src_file = ScaleFile.objects.select_for_update().get(pk=src_file_id, file_type='SOURCE')
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

        try:
            # Try to update corresponding ingest models with this file's data time
            from ingest.models import Ingest
            Ingest.objects.filter(source_file_id=src_file_id).update(data_started=data_started, data_ended=data_ended)
        except ImportError:
            pass

        # Move the source file if a new workspace path is provided and the workspace allows it
        old_workspace_path = src_file.file_path
        if new_workspace_path and src_file.workspace.is_move_enabled:
            ScaleFile.objects.move_files([FileMove(src_file, new_workspace_path)])

        try:
            # Check trigger rules for parsed source files
            ParseTriggerHandler().process_parsed_source_file(src_file)
        except Exception:
            # Move file back if there was an error
            if new_workspace_path and src_file.workspace.is_move_enabled:
                ScaleFile.objects.move_files([FileMove(src_file, old_workspace_path)])
            raise


class SourceFile(ScaleFile):
    """Represents a source data file that is available for processing. This is a proxy model of the
    :class:`storage.models.ScaleFile` model. It has the same set of fields, but a different manager that provides
    functionality specific to source files.
    """

    @classmethod
    def create(cls):
        """Creates a new source file

        :returns: The new source file
        :rtype: :class:`source.models.SourceFile`
        """

        src_file = SourceFile()
        src_file.file_type = 'SOURCE'
        return src_file

    objects = SourceFileManager()

    class Meta(object):
        """meta information for the db"""
        proxy = True
