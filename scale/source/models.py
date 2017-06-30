"""Defines the database model for source files"""
from __future__ import unicode_literals

import logging

import django.contrib.gis.db.models as models
from django.db import transaction
from django.utils.timezone import now

import storage.geospatial_utils as geo_utils
from job.models import Job
from source.triggers.parse_trigger_handler import ParseTriggerHandler
from storage.brokers.broker import FileMove
from storage.models import ScaleFile


logger = logging.getLogger(__name__)


class SourceFileManager(models.GeoManager):
    """Provides additional methods for handling source files
    """

    def filter_sources(self, started=None, ended=None, time_field=None, is_parsed=None, file_name=None, order=None):
        """Returns a query for source models that filters on the given fields. The returned query includes the related
        workspace, job_type, and job fields, except for the workspace.json_config field. The related countries are set
        to be pre-fetched as part of the query.

        :param started: Query source files updated after this amount of time.
        :type started: :class:`datetime.datetime`
        :param ended: Query source files updated before this amount of time.
        :type ended: :class:`datetime.datetime`
        :param time_field: The time field to use for filtering.
        :type time_field: string
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
        sources = ScaleFile.objects.filter(file_type='SOURCE')
        sources = sources.select_related('workspace').defer('workspace__json_config')
        sources = sources.prefetch_related('countries')

        # Apply time range filtering
        if started:
            if time_field == 'data':
                sources = sources.filter(data_ended__gte=started)
            else:
                sources = sources.filter(last_modified__gte=started)
        if ended:
            if time_field == 'data':
                sources = sources.filter(data_started__lte=ended)
            else:
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

    def get_sources(self, started=None, ended=None, time_field=None, is_parsed=None, file_name=None, order=None):
        """Returns a list of source files within the given time range.

        :param started: Query source files updated after this amount of time.
        :type started: :class:`datetime.datetime`
        :param ended: Query source files updated before this amount of time.
        :type ended: :class:`datetime.datetime`
        :param time_field: The time field to use for filtering.
        :type time_field: string
        :param is_parsed: Query source files flagged as successfully parsed.
        :type is_parsed: bool
        :param file_name: Query source files with the given file name.
        :type file_name: str
        :param order: A list of fields to control the sort order.
        :type order: list[str]
        :returns: The list of source files that match the time range.
        :rtype: list[:class:`storage.models.ScaleFile`]
        """

        return self.filter_sources(started=started, ended=ended, time_field=time_field, is_parsed=is_parsed,
                                   file_name=file_name, order=order)

    def get_source_file_by_name(self, file_name):
        """Returns the source file with the given file name

        :param file_name: The name of the source file
        :type file_name: string
        :returns: The list of source files that match the time range.
        :rtype: :class:`storage.models.ScaleFile`

        :raises :class:`storage.models.ScaleFile.DoesNotExist`: If the file does not exist
        """

        return ScaleFile.objects.get(file_name=file_name, file_type='SOURCE')

    def get_source_ingests(self, source_file_id, started=None, ended=None, statuses=None, scan_ids=None,
                           strike_ids=None, order=None):
        """Returns a query for ingest models for the given source file. The returned query includes the related strike,
        scan, source_file, and source_file.workspace fields, except for the strike.configuration, scan.configuration,
        and source_file.workspace.json_config fields.

        :param source_file_id: The source file ID.
        :type source_file_id: int
        :param started: Query ingests updated after this amount of time.
        :type started: :class:`datetime.datetime`
        :param ended: Query ingests updated before this amount of time.
        :type ended: :class:`datetime.datetime`
        :param statuses: Query ingests with the a specific process status.
        :type statuses: [string]
        :param scan_ids: Query ingests created by a specific scan processor.
        :type scan_ids: [string]
        :param strike_ids: Query ingests created by a specific strike processor.
        :type strike_ids: [string]
        :param file_name: Query ingests with a specific file name.
        :type file_name: string
        :param order: A list of fields to control the sort order.
        :type order: [string]
        :returns: The ingest query
        :rtype: :class:`django.db.models.QuerySet`
        """

        from ingest.models import Ingest
        return Ingest.objects.filter_ingests(source_file_id=source_file_id, started=started, ended=ended,
                                             statuses=statuses, scan_ids=scan_ids, strike_ids=strike_ids, order=order)

    def get_source_jobs(self, source_file_id, started=None, ended=None, statuses=None, job_ids=None, job_type_ids=None,
                        job_type_names=None, job_type_categories=None, error_categories=None, include_superseded=False,
                        order=None):
        """Returns a query for the list of jobs that have used the given source file as input. The returned query
        includes the related job_type, job_type_rev, event, and error fields, except for the job_type.interface and
        job_type_rev.interface fields.

        :param source_file_id: The source file ID.
        :type source_file_id: int
        :param started: Query jobs updated after this amount of time.
        :type started: :class:`datetime.datetime`
        :param ended: Query jobs updated before this amount of time.
        :type ended: :class:`datetime.datetime`
        :param statuses: Query jobs with the a specific execution status.
        :type statuses: [string]
        :param job_ids: Query jobs associated with the identifier.
        :type job_ids: [int]
        :param job_type_ids: Query jobs of the type associated with the identifier.
        :type job_type_ids: [int]
        :param job_type_names: Query jobs of the type associated with the name.
        :type job_type_names: [string]
        :param job_type_categories: Query jobs of the type associated with the category.
        :type job_type_categories: [string]
        :param error_categories: Query jobs that failed due to errors associated with the category.
        :type error_categories: [string]
        :param include_superseded: Whether to include jobs that are superseded.
        :type include_superseded: bool
        :param order: A list of fields to control the sort order.
        :type order: [string]
        :returns: The list of jobs that match the time range.
        :rtype: [:class:`job.models.Job`]
        """

        # Order must end with job ID so we can do a distinct on the job ID and remove duplicate jobs
        if order:
            order.append('id')
        else:
            order = ['last_modified', 'id']
        jobs = Job.objects.filter_jobs(started=started, ended=ended, statuses=statuses, job_ids=job_ids,
                                       job_type_ids=job_type_ids, job_type_names=job_type_names,
                                       job_type_categories=job_type_categories, error_categories=error_categories,
                                       include_superseded=include_superseded, order=order)
        distinct = [field.replace('-', '') for field in order]  # Remove - char for reverse sort fields
        jobs = jobs.filter(job_file_links__ancestor_id=source_file_id).distinct(*distinct)
        return jobs

    def get_source_products(self, source_file_id, started=None, ended=None, time_field=None, batch_ids=None,
                            job_type_ids=None, job_type_names=None, job_type_categories=None, job_ids=None,
                            is_operational=None, is_published=None, is_superseded=None, file_name=None, 
                            job_output=None, recipe_ids=None, recipe_type_ids=None, recipe_job=None, order=None):
        """Returns a query for the list of products produced by the given source file ID. The returned query includes
        the related  workspace, job_type, and job fields, except for the workspace.json_config field. The related
        countries are set to be pre-fetched as part of the query.

        :param source_file_id: The source file ID.
        :type source_file_id: int
        :param started: Query product files updated after this amount of time.
        :type started: :class:`datetime.datetime`
        :param ended: Query product files updated before this amount of time.
        :type ended: :class:`datetime.datetime`
        :keyword time_field: The time field to use for filtering.
        :type time_field: string
        :param batch_ids: Query product files produced by batches with the given identifiers.
        :type batch_ids: list[int]
        :param job_type_ids: Query product files produced by jobs with the given type identifiers.
        :type job_type_ids: list[int]
        :param job_type_names: Query product files produced by jobs with the given type names.
        :type job_type_names: list[str]
        :param job_type_categories: Query product files produced by jobs with the given type categories.
        :type job_type_categories: list[str]
        :param job_ids: Query product files produced by jobs with the given identifiers.
        :type job_ids: list[int]
        :param is_operational: Query product files flagged as operational or R&D only.
        :type is_operational: bool
        :param is_published: Query product files flagged as currently exposed for publication.
        :type is_published: bool
        :param is_superseded: Query product files that have/have not been superseded.
        :type is_superseded: bool
        :param file_name: Query product files with the given file name.
        :type file_name: str
        :keyword job_output: Query product files with the given job output
        :type job_output: str
        :keyword recipe_ids: Query product files produced by a given recipe id
        :type recipe_ids: list[int]
        :keyword recipe_job: Query product files produced by a given recipe name
        :type recipe_job: str
        :keyword recipe_type_ids: Query product files produced by a given recipe types
        :type recipe_type_ids: list[int]
        :param order: A list of fields to control the sort order.
        :type order: list[str]
        :returns: The product file query
        :rtype: :class:`django.db.models.QuerySet`
        """

        from product.models import ProductFile
        products = ProductFile.objects.filter_products(started=started, ended=ended, time_field=time_field,
                                                       job_type_ids=job_type_ids, job_type_names=job_type_names,
                                                       job_type_categories=job_type_categories, job_ids=job_ids,
                                                       is_operational=is_operational, is_published=is_published,
                                                       is_superseded=None, file_name=file_name, job_output=job_output,
                                                       recipe_ids=recipe_ids, recipe_job=recipe_job,
                                                       recipe_type_ids=recipe_type_ids, order=order)
        products = products.filter(ancestors__ancestor_id=source_file_id)
        if batch_ids:
            products = products.filter(ancestors__batch_id__in=batch_ids)

        return products

    def get_details(self, source_id):
        """Gets additional details for the given source model

        :param source_id: The unique identifier of the source (file ID)
        :type source_id: int
        :returns: The source model with details
        :rtype: :class:`storage.models.ScaleFile`

        :raises :class:`storage.models.ScaleFile.DoesNotExist`: If the file does not exist
        """

        return ScaleFile.objects.all().select_related('workspace').get(pk=source_id, file_type='SOURCE')

    # TODO: remove when REST API v4 is removed
    def get_details_v4(self, source_id, include_superseded=False):
        """Gets additional details for the given source model based on related model attributes (v4 version).

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
        if data_started and not data_ended:
            src_file.data_started = data_started
            src_file.data_ended = data_started
        elif not data_started and data_ended:
            src_file.data_started = data_ended
            src_file.data_ended = data_ended
        elif not data_ended and not data_started:
            src_file.data_started = None
            src_file.data_ended = None
        else:
            src_file.data_started = data_started
            src_file.data_ended = data_ended
        for tag in data_types:
            src_file.add_data_type_tag(tag)
        if geom:
            src_file.geometry = geom
            src_file.center_point = geo_utils.get_center_point(geom)
        if props:
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

    VALID_TIME_FIELDS = ['data', 'last_modified']

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
