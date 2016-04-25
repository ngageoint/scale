"""Defines the database models for various system metrics."""
from __future__ import unicode_literals

import datetime
import logging
import sys

import django.contrib.gis.db.models as models
import django.utils.timezone as timezone
from django.db import transaction

from error.models import Error
from job.models import Job, JobExecution, JobType
from ingest.models import Ingest, Strike
from metrics.registry import MetricsPlotData, MetricsType, MetricsTypeGroup, MetricsTypeFilter

logger = logging.getLogger(__name__)


class PlotBigIntegerField(models.BigIntegerField):
    """Custom field used to indicate a model attribute can be used as a plot value.

    :keyword verbose_name: The display name of the field.
    :type verbose_name: string
    :keyword name: The internal database name of the field.
    :type name: string
    :keyword aggregate: The math operation used to compute the value. Examples: avg, max, min, sum
    :type aggregate: string
    :keyword group: The base field name used to group together related values. For example, a field may have several
        aggregate variations that all reference the same base attribute.
    :type group: string
    :keyword units: The mathematical units applied to the value. Examples: seconds, minutes, hours
    :type units: string
    """

    def __init__(self, verbose_name=None, name=None, aggregate=None, group=None, units=None, **kwargs):
        self.aggregate = aggregate
        self.group = group
        self.units = units

        super(PlotBigIntegerField, self).__init__(verbose_name, name, **kwargs)


class PlotIntegerField(models.IntegerField):
    """Custom field used to indicate a model attribute can be used as a plot value.

    :keyword verbose_name: The display name of the field.
    :type verbose_name: string
    :keyword name: The internal database name of the field.
    :type name: string
    :keyword aggregate: The math operation used to compute the value. Examples: avg, max, min, sum
    :type aggregate: string
    :keyword group: The base field name used to group together related values. For example, a field may have several
        aggregate variations that all reference the same base attribute.
    :type group: string
    :keyword units: The mathematical units applied to the value. Examples: seconds, minutes, hours
    :type units: string
    """

    def __init__(self, verbose_name=None, name=None, aggregate=None, group=None, units=None, **kwargs):
        self.aggregate = aggregate
        self.group = group
        self.units = units

        super(PlotIntegerField, self).__init__(verbose_name, name, **kwargs)

PLOT_FIELD_TYPES = [PlotBigIntegerField, PlotIntegerField]


class MetricsErrorManager(models.Manager):
    """Provides additional methods for computing daily error metrics."""

    def calculate(self, date):
        """See :meth:`metrics.registry.MetricsTypeProvider.calculate`."""

        started = datetime.datetime.combine(date, datetime.time.min).replace(tzinfo=timezone.utc)
        ended = datetime.datetime.combine(date, datetime.time.max).replace(tzinfo=timezone.utc)

        # Fetch all the job executions with an error for the requested day
        job_exes = JobExecution.objects.filter(error__is_builtin=True, ended__gte=started, ended__lte=ended)
        job_exes = job_exes.select_related('error')
        job_exes = job_exes.defer('environment', 'results', 'results_manifest', 'stdout', 'stderr')

        # Calculate the overall counts based on job status
        entry_map = {}
        for job_exe in job_exes.iterator():
            if job_exe.error not in entry_map:
                entry = MetricsError(error=job_exe.error, occurred=date, created=timezone.now())
                entry.total_count = 0
                entry_map[job_exe.error] = entry
            entry = entry_map[job_exe.error]
            entry.total_count += 1

        # Save the new metrics to the database
        self._replace_entries(date, entry_map.values())

    def get_metrics_type(self, include_choices=False):
        """See :meth:`metrics.registry.MetricsTypeProvider.get_metrics_type`."""

        # Create the metrics type definition
        metrics_type = MetricsType('errors', 'Errors', 'Metrics for jobs grouped by errors.')
        metrics_type.filters = [MetricsTypeFilter('name', 'string'), MetricsTypeFilter('category', 'string')]
        metrics_type.groups = MetricsError.GROUPS
        metrics_type.set_columns(MetricsError, PLOT_FIELD_TYPES)

        # Optionally include all the possible error choices
        if include_choices:
            metrics_type.choices = Error.objects.filter(is_builtin=True)

        return metrics_type

    def get_plot_data(self, started=None, ended=None, choice_ids=None, columns=None):
        """See :meth:`metrics.registry.MetricsTypeProvider.get_plot_data`."""

        # Fetch all the matching job type metrics based on query filters
        entries = MetricsError.objects.all().order_by('occurred')
        if started:
            entries = entries.filter(occurred__gte=started)
        if ended:
            entries = entries.filter(occurred__lte=ended)
        if choice_ids:
            entries = entries.filter(error_id__in=choice_ids)
        if not columns:
            columns = self.get_metrics_type().columns
        column_names = [c.name for c in columns]
        entries = entries.values('error_id', 'occurred', *column_names)

        # Convert the database models to plot models
        return MetricsPlotData.create(entries, 'occurred', 'error_id', choice_ids, columns)

    @transaction.atomic
    def _replace_entries(self, date, entries):
        """Replaces all the existing metric entries for the given date with new ones.

        :param date: The date when job executions associated with the metrics ended.
        :type date: datetime.date
        :param entries: The new metrics model to save.
        :type entries: list[:class:`metrics.models.MetricsError`]
        """

        # Delete all the previous metrics entries
        MetricsError.objects.filter(occurred=date).delete()

        # Save all the new metrics models
        MetricsError.objects.bulk_create(entries)


class MetricsError(models.Model):
    """Tracks all the error metrics grouped by error type.

    :keyword error: The error type associated with these metrics.
    :type error: :class:`django.db.models.ForeignKey`
    :keyword occurred: The date when the errors included in this model were created.
    :type occurred: :class:`django.db.models.DateField`

    :keyword total_count: The total number of errors of this type that occurred for the day.
    :type total_count: :class:`metrics.models.PlotIntegerField`

    :keyword created: When the model was first created.
    :type created: :class:`django.db.models.DateTimeField`
    """
    GROUPS = [
        MetricsTypeGroup('overview', 'Overview', 'Overall counts based on error type.'),
    ]

    error = models.ForeignKey('error.Error', on_delete=models.PROTECT)
    occurred = models.DateField(db_index=True)

    total_count = PlotIntegerField(aggregate='sum', blank=True, group='overview',
                                   help_text='Number of jobs that failed with a particular error type.', null=True,
                                   units='count', verbose_name='Total Count')

    created = models.DateTimeField(auto_now_add=True)

    objects = MetricsErrorManager()

    class Meta(object):
        """meta information for the db"""
        db_table = 'metrics_error'


class MetricsIngestManager(models.Manager):
    """Provides additional methods for computing daily ingest metrics."""

    def calculate(self, date):
        """See :meth:`metrics.registry.MetricsTypeProvider.calculate`."""

        started = datetime.datetime.combine(date, datetime.time.min).replace(tzinfo=timezone.utc)
        ended = datetime.datetime.combine(date, datetime.time.max).replace(tzinfo=timezone.utc)

        # Fetch all the ingests relevant for metrics
        ingests = Ingest.objects.filter(status__in=['DEFERRED', 'INGESTED', 'ERRORED', 'DUPLICATE'],
                                        ingest_ended__gte=started, ingest_ended__lte=ended)
        ingests = ingests.select_related('strike').defer('strike__configuration')

        # Calculate the overall counts based on ingest status
        entry_map = {}
        for ingest in ingests.iterator():
            if ingest.strike not in entry_map:
                entry = MetricsIngest(strike=ingest.strike, occurred=date, created=timezone.now())
                entry.deferred_count = 0
                entry.ingested_count = 0
                entry.errored_count = 0
                entry.duplicate_count = 0
                entry.total_count = 0
                entry_map[ingest.strike] = entry
            entry = entry_map[ingest.strike]
            self._update_metrics(date, ingest, entry)

        # Save the new metrics to the database
        self._replace_entries(date, entry_map.values())

    def get_metrics_type(self, include_choices=False):
        """See :meth:`metrics.registry.MetricsTypeProvider.get_metrics_type`."""

        # Create the metrics type definition
        metrics_type = MetricsType('ingests', 'Ingests', 'Metrics for ingests grouped by strike process.')
        metrics_type.filters = [MetricsTypeFilter('name', 'string')]
        metrics_type.groups = MetricsIngest.GROUPS
        metrics_type.set_columns(MetricsIngest, PLOT_FIELD_TYPES)

        # Optionally include all the possible strike choices
        if include_choices:
            metrics_type.choices = Strike.objects.all()

        return metrics_type

    def get_plot_data(self, started=None, ended=None, choice_ids=None, columns=None):
        """See :meth:`metrics.registry.MetricsTypeProvider.get_plot_data`."""

        # Fetch all the matching ingest metrics based on query filters
        entries = MetricsIngest.objects.all().order_by('occurred')
        if started:
            entries = entries.filter(occurred__gte=started)
        if ended:
            entries = entries.filter(occurred__lte=ended)
        if choice_ids:
            entries = entries.filter(strike_id__in=choice_ids)
        if not columns:
            columns = self.get_metrics_type().columns
        column_names = [c.name for c in columns]
        entries = entries.values('strike_id', 'occurred', *column_names)

        # Convert the database models to plot models
        return MetricsPlotData.create(entries, 'occurred', 'strike_id', choice_ids, columns)

    def _update_metrics(self, date, ingest, entry):
        """Updates the metrics model attributes for a single ingest.

        :param date: The date when ingests associated with the metrics ended.
        :type date: datetime.date
        :param ingest: The ingest from which to derive statistics.
        :type ingest: :class:`ingest.models.Ingest`
        :param entry: The metrics model to update.
        :type entry: :class:`metrics.models.MetricsIngest`
        """
        if ingest.status == 'DEFERRED':
            entry.deferred_count += 1
            entry.total_count += 1
        elif ingest.status == 'INGESTED':
            entry.ingested_count += 1
            entry.total_count += 1
        elif ingest.status == 'ERRORED':
            entry.errored_count += 1
            entry.total_count += 1
        elif ingest.status == 'DUPLICATE':
            entry.duplicate_count += 1
            entry.total_count += 1

        # Update file size metrics
        if ingest.file_size:
            entry._file_count = (entry._file_count if hasattr(entry, '_file_count') else 0) + 1
            entry.file_size_sum = (entry.file_size_sum or 0) + ingest.file_size
            entry.file_size_min = min(entry.file_size_min or sys.maxint, ingest.file_size)
            entry.file_size_max = max(entry.file_size_max or 0, ingest.file_size)
            entry.file_size_avg = entry.file_size_sum / entry._file_count

        # Update elapsed transfer time metrics
        if ingest.transfer_started and ingest.transfer_ended:
            transfer_secs = max((ingest.transfer_ended - ingest.transfer_started).total_seconds(), 0)
            entry._transfer_count = (entry._transfer_count if hasattr(entry, '_transfer_count') else 0) + 1
            entry.transfer_time_sum = (entry.transfer_time_sum or 0) + transfer_secs
            entry.transfer_time_min = min(entry.transfer_time_min or sys.maxint, transfer_secs)
            entry.transfer_time_max = max(entry.transfer_time_max or 0, transfer_secs)
            entry.transfer_time_avg = entry.transfer_time_sum / entry._transfer_count

        # Update elapsed ingest time metrics
        if ingest.status == 'INGESTED' and ingest.ingest_started and ingest.ingest_ended:
            ingest_secs = max((ingest.ingest_ended - ingest.ingest_started).total_seconds(), 0)
            entry._ingest_count = (entry._ingest_count if hasattr(entry, '_ingest_count') else 0) + 1
            entry.ingest_time_sum = (entry.ingest_time_sum or 0) + ingest_secs
            entry.ingest_time_min = min(entry.ingest_time_min or sys.maxint, ingest_secs)
            entry.ingest_time_max = max(entry.ingest_time_max or 0, ingest_secs)
            entry.ingest_time_avg = entry.ingest_time_sum / entry._ingest_count

        return entry

    @transaction.atomic
    def _replace_entries(self, date, entries):
        """Replaces all the existing metric entries for the given date with new ones.

        :param date: The date when ingests associated with the metrics ended.
        :type date: datetime.date
        :param entries: The new metrics model to save.
        :type entries: list[:class:`metrics.models.MetricsIngest`]
        """

        # Delete all the previous metrics entries
        MetricsIngest.objects.filter(occurred=date).delete()

        # Save all the new metrics models
        MetricsIngest.objects.bulk_create(entries)


class MetricsIngest(models.Model):
    """Tracks all the ingest metrics grouped by strike process.

    :keyword strike: The strike process associated with these metrics.
    :type strike: :class:`django.db.models.ForeignKey`
    :keyword occurred: The date when the ingests included in this model were ended.
    :type occurred: :class:`django.db.models.DateField`

    :keyword deferred_count: The total number of deferred ingests.
    :type deferred_count: :class:`metrics.models.PlotIntegerField`
    :keyword ingested_count: The total number of successfully completed ingests.
    :type ingested_count: :class:`metrics.models.PlotIntegerField`
    :keyword errored_count: The total number of failed ingests.
    :type errored_count: :class:`metrics.models.PlotIntegerField`
    :keyword duplicate_count: The total number of duplicated ingests.
    :type duplicate_count: :class:`metrics.models.PlotIntegerField`

    :keyword file_size_sum: The total size of ingested files in bytes.
    :type file_size_sum: :class:`metrics.models.PlotBigIntegerField`
    :keyword file_size_min: The minimum size of ingested files in bytes.
    :type file_size_min: :class:`metrics.models.PlotBigIntegerField`
    :keyword file_size_max: The maximum size of ingested files in bytes.
    :type file_size_max: :class:`metrics.models.PlotBigIntegerField`
    :keyword file_size_avg: The average size of ingested files in bytes.
    :type file_size_avg: :class:`metrics.models.PlotBigIntegerField`

    :keyword transfer_time_sum: The total time spent transferring ingested files in seconds.
    :type transfer_time_sum: :class:`metrics.models.PlotIntegerField`
    :keyword transfer_time_min: The minimum time spent transferring ingested files in seconds.
    :type transfer_time_min: :class:`metrics.models.PlotIntegerField`
    :keyword transfer_time_max: The maximum time spent transferring ingested files in seconds.
    :type transfer_time_max: :class:`metrics.models.PlotIntegerField`
    :keyword transfer_time_avg: The average time spent transferring ingested files in seconds.
    :type transfer_time_avg: :class:`metrics.models.PlotIntegerField`

    :keyword ingest_time_sum: The total time spent ingesting files in seconds.
    :type ingest_time_sum: :class:`metrics.models.PlotIntegerField`
    :keyword ingest_time_min: The minimum time spent ingesting files in seconds.
    :type ingest_time_min: :class:`metrics.models.PlotIntegerField`
    :keyword ingest_time_max: The maximum time spent ingesting files in seconds.
    :type ingest_time_max: :class:`metrics.models.PlotIntegerField`
    :keyword ingest_time_avg: The average time spent ingesting files in seconds.
    :type ingest_time_avg: :class:`metrics.models.PlotIntegerField`

    :keyword created: When the model was first created.
    :type created: :class:`django.db.models.DateTimeField`
    """
    GROUPS = [
        MetricsTypeGroup('overview', 'Overview', 'Overall counts based on ingest status.'),
        MetricsTypeGroup('file_size', 'File Size', 'Size information about ingested files.'),
        MetricsTypeGroup('transfer_time', 'Transfer Time', 'When files were being transferred before ingest.'),
        MetricsTypeGroup('ingest_time', 'Ingest Time', 'When files were processed during ingest.'),
    ]

    strike = models.ForeignKey('ingest.Strike', on_delete=models.PROTECT)
    occurred = models.DateField(db_index=True)

    deferred_count = PlotIntegerField(aggregate='sum', blank=True, group='overview',
                                      help_text='Number of files deferred (ignored) by the ingest process.', null=True,
                                      units='count', verbose_name='Deferred Count')
    ingested_count = PlotIntegerField(aggregate='sum', blank=True, group='overview',
                                      help_text='Number of files successfully ingested.', null=True, units='count',
                                      verbose_name='Ingested Count')
    errored_count = PlotIntegerField(aggregate='sum', blank=True, group='overview',
                                     help_text='Number of files that failed to ingest.', null=True, units='count',
                                     verbose_name='Errored Count')
    duplicate_count = PlotIntegerField(aggregate='sum', blank=True, group='overview',
                                       help_text='Number of files that were duplicates of previous ingests.', null=True,
                                       units='count', verbose_name='Duplicate Count')
    total_count = PlotIntegerField(aggregate='sum', blank=True, group='overview',
                                   help_text='Number of deferred, ingested, errored, and duplicate ingests.', null=True,
                                   units='count', verbose_name='Total Count')

    file_size_sum = PlotBigIntegerField(aggregate='sum', blank=True, group='file_size',
                                        help_text='Total size of ingested files.', null=True, units='bytes',
                                        verbose_name='File Size (Sum)')
    file_size_min = PlotBigIntegerField(aggregate='min', blank=True, group='file_size',
                                        help_text='Minimum size of ingested files.', null=True, units='bytes',
                                        verbose_name='File Size (Min)')
    file_size_max = PlotBigIntegerField(aggregate='max', blank=True, group='file_size',
                                        help_text='Maximum size of ingested files.',
                                        null=True, units='bytes', verbose_name='File Size (Max)')
    file_size_avg = PlotBigIntegerField(aggregate='avg', blank=True, group='file_size',
                                        help_text='Average size of ingested files.', null=True,
                                        units='bytes', verbose_name='File Size (Avg)')

    transfer_time_sum = PlotIntegerField(aggregate='sum', blank=True, group='transfer_time',
                                         help_text='Total time spent transferring files before ingest.', null=True,
                                         units='seconds', verbose_name='Transfer Time (Sum)')
    transfer_time_min = PlotIntegerField(aggregate='min', blank=True, group='transfer_time',
                                         help_text='Minimum time spent transferring files before ingest.', null=True,
                                         units='seconds', verbose_name='Transfer Time (Min)')
    transfer_time_max = PlotIntegerField(aggregate='max', blank=True, group='transfer_time',
                                         help_text='Maximum time spent transferring files before ingest.', null=True,
                                         units='seconds', verbose_name='Transfer Time (Max)')
    transfer_time_avg = PlotIntegerField(aggregate='avg', blank=True, group='transfer_time',
                                         help_text='Average time spent transferring files before ingest.',
                                         null=True, units='seconds', verbose_name='Transfer Time (Avg)')

    ingest_time_sum = PlotIntegerField(aggregate='sum', blank=True, group='ingest_time',
                                       help_text='Total time spent processing files during ingest.',
                                       null=True, units='seconds', verbose_name='Ingest Time (Sum)')
    ingest_time_min = PlotIntegerField(aggregate='min', blank=True, group='ingest_time',
                                       help_text='Minimum time spent processing files during ingest.',
                                       null=True, units='seconds', verbose_name='Ingest Time (Min)')
    ingest_time_max = PlotIntegerField(aggregate='max', blank=True, group='ingest_time',
                                       help_text='Maximum time spent processing files during ingest.',
                                       null=True, units='seconds', verbose_name='Ingest Time (Max)')
    ingest_time_avg = PlotIntegerField(aggregate='avg', blank=True, group='ingest_time',
                                       help_text='Average time spent processing files during ingest.',
                                       null=True, units='seconds', verbose_name='Ingest Time (Avg)')

    created = models.DateTimeField(auto_now_add=True)

    objects = MetricsIngestManager()

    class Meta(object):
        """meta information for the db"""
        db_table = 'metrics_ingest'


class MetricsJobTypeManager(models.Manager):
    """Provides additional methods for computing daily job type metrics."""

    def calculate(self, date):
        """See :meth:`metrics.registry.MetricsTypeProvider.calculate`."""

        started = datetime.datetime.combine(date, datetime.time.min).replace(tzinfo=timezone.utc)
        ended = datetime.datetime.combine(date, datetime.time.max).replace(tzinfo=timezone.utc)

        # Fetch all the jobs relevant for metrics
        jobs = Job.objects.filter(status__in=['CANCELED', 'COMPLETED', 'FAILED'], ended__gte=started, ended__lte=ended)
        jobs = jobs.select_related('job_type', 'error').defer('data', 'docker_params', 'results')

        # Calculate the overall counts based on job status
        entry_map = {}
        for job in jobs.iterator():
            if job.job_type not in entry_map:
                entry = MetricsJobType(job_type=job.job_type, occurred=date, created=timezone.now())
                entry.completed_count = 0
                entry.failed_count = 0
                entry.canceled_count = 0
                entry.total_count = 0
                entry.error_system_count = 0
                entry.error_data_count = 0
                entry.error_algorithm_count = 0
                entry_map[job.job_type] = entry
            entry = entry_map[job.job_type]
            self._update_counts(date, job, entry)

        # Fetch all the completed job executions for the requested day
        job_exes = JobExecution.objects.filter(status__in=['COMPLETED'], ended__gte=started, ended__lte=ended)
        job_exes = job_exes.select_related('job__job_type')
        job_exes = job_exes.defer('environment', 'results', 'results_manifest', 'stdout', 'stderr')

        # Calculate the metrics per job execution grouped by job type
        for job_exe in job_exes.iterator():
            job_type = job_exe.job.job_type
            entry = entry_map[job_type]
            self._update_times(date, job_exe, entry)

        # Save the new metrics to the database
        self._replace_entries(date, entry_map.values())

    def get_metrics_type(self, include_choices=False):
        """See :meth:`metrics.registry.MetricsTypeProvider.get_metrics_type`."""

        # Create the metrics type definition
        metrics_type = MetricsType('job-types', 'Job Types', 'Metrics for jobs and executions grouped by job type.')
        metrics_type.filters = [MetricsTypeFilter('name', 'string'), MetricsTypeFilter('version', 'string')]
        metrics_type.groups = MetricsJobType.GROUPS
        metrics_type.set_columns(MetricsJobType, PLOT_FIELD_TYPES)

        # Optionally include all the possible job type choices
        if include_choices:
            metrics_type.choices = JobType.objects.all()

        return metrics_type

    def get_plot_data(self, started=None, ended=None, choice_ids=None, columns=None):
        """See :meth:`metrics.registry.MetricsTypeProvider.get_plot_data`."""

        # Fetch all the matching job type metrics based on query filters
        entries = MetricsJobType.objects.all().order_by('occurred')
        if started:
            entries = entries.filter(occurred__gte=started)
        if ended:
            entries = entries.filter(occurred__lte=ended)
        if choice_ids:
            entries = entries.filter(job_type_id__in=choice_ids)
        if not columns:
            columns = self.get_metrics_type().columns
        column_names = [c.name for c in columns]
        entries = entries.values('job_type_id', 'occurred', *column_names)

        # Convert the database models to plot models
        return MetricsPlotData.create(entries, 'occurred', 'job_type_id', choice_ids, columns)

    def _update_counts(self, date, job, entry):
        """Updates the metrics model attributes for a single job.

        :param date: The date when jobs associated with the metrics ended.
        :type date: datetime.date
        :param job: The job from which to derive statistics.
        :type job: :class:`job.models.Job`
        :param entry: The metrics model to update.
        :type entry: :class:`metrics.models.MetricsJobType`
        """
        if job.status == 'COMPLETED':
            entry.completed_count += 1
            entry.total_count += 1
        elif job.status == 'FAILED':
            entry.failed_count += 1
            entry.total_count += 1
        elif job.status == 'CANCELED':
            entry.canceled_count += 1
            entry.total_count += 1

        if job.error:
            if job.error.category == 'SYSTEM':
                entry.error_system_count += 1
            elif job.error.category == 'DATA':
                entry.error_data_count += 1
            elif job.error.category == 'ALGORITHM':
                entry.error_algorithm_count += 1

    def _update_times(self, date, job_exe, entry):
        """Updates the metrics model attributes for a single job execution.

        :param date: The date when job executions associated with the metrics ended.
        :type date: datetime.date
        :param job_exe: The job execution from which to derive statistics.
        :type job_exe: :class:`job.models.JobExecution`
        :param entry: The metrics model to update.
        :type entry: :class:`metrics.models.MetricsJobType`
        """

        # Update elapsed queue time metrics
        queue_secs = None
        if job_exe.queued and job_exe.started:
            queue_secs = max((job_exe.started - job_exe.queued).total_seconds(), 0)
            entry.queue_time_sum = (entry.queue_time_sum or 0) + queue_secs
            entry.queue_time_min = min(entry.queue_time_min or sys.maxint, queue_secs)
            entry.queue_time_max = max(entry.queue_time_max or 0, queue_secs)
            entry.queue_time_avg = entry.queue_time_sum / entry.completed_count

        # Update elapsed pre-task time metrics
        pre_secs = None
        if job_exe.pre_started and job_exe.pre_completed:
            pre_secs = max((job_exe.pre_completed - job_exe.pre_started).total_seconds(), 0)
            entry.pre_time_sum = (entry.pre_time_sum or 0) + pre_secs
            entry.pre_time_min = min(entry.pre_time_min or sys.maxint, pre_secs)
            entry.pre_time_max = max(entry.pre_time_max or 0, pre_secs)
            entry.pre_time_avg = entry.pre_time_sum / entry.completed_count

        # Update elapsed actual job time metrics
        job_secs = None
        if job_exe.job_started and job_exe.job_completed:
            job_secs = max((job_exe.job_completed - job_exe.job_started).total_seconds(), 0)
            entry.job_time_sum = (entry.job_time_sum or 0) + job_secs
            entry.job_time_min = min(entry.job_time_min or sys.maxint, job_secs)
            entry.job_time_max = max(entry.job_time_max or 0, job_secs)
            entry.job_time_avg = entry.job_time_sum / entry.completed_count

        # Update elapsed post-task time metrics
        post_secs = None
        if job_exe.post_started and job_exe.post_completed:
            post_secs = max((job_exe.post_completed - job_exe.post_started).total_seconds(), 0)
            entry.post_time_sum = (entry.post_time_sum or 0) + post_secs
            entry.post_time_min = min(entry.post_time_min or sys.maxint, post_secs)
            entry.post_time_max = max(entry.post_time_max or 0, post_secs)
            entry.post_time_avg = entry.post_time_sum / entry.completed_count

        # Update elapsed overall run and stage time metrics
        if job_exe.started and job_exe.ended:
            run_secs = max((job_exe.ended - job_exe.started).total_seconds(), 0)
            entry.run_time_sum = (entry.run_time_sum or 0) + run_secs
            entry.run_time_min = min(entry.run_time_min or sys.maxint, run_secs)
            entry.run_time_max = max(entry.run_time_max or 0, run_secs)
            entry.run_time_avg = entry.run_time_sum / entry.completed_count

            stage_secs = max(run_secs - ((pre_secs or 0) + (job_secs or 0) + (post_secs or 0)), 0)
            entry.stage_time_sum = (entry.stage_time_sum or 0) + stage_secs
            entry.stage_time_min = min(entry.stage_time_min or sys.maxint, stage_secs)
            entry.stage_time_max = max(entry.stage_time_max or 0, stage_secs)
            entry.stage_time_avg = entry.stage_time_sum / entry.completed_count
        return entry

    @transaction.atomic
    def _replace_entries(self, date, entries):
        """Replaces all the existing metric entries for the given date with new ones.

        :param date: The date when job executions associated with the metrics ended.
        :type date: datetime.date
        :param entries: The new metrics model to save.
        :type entries: list[:class:`metrics.models.MetricsJobType`]
        """

        # Delete all the previous metrics entries
        MetricsJobType.objects.filter(occurred=date).delete()

        # Save all the new metrics models
        MetricsJobType.objects.bulk_create(entries)


class MetricsJobType(models.Model):
    """Tracks all the job execution metrics grouped by job type.

    :keyword job_type: The type of job associated with these metrics.
    :type job_type: :class:`django.db.models.ForeignKey`
    :keyword occurred: The date when the job executions included in this model were ended.
    :type occurred: :class:`django.db.models.DateField`

    :keyword completed_count: The total number of completed job executions.
    :type completed_count: :class:`metrics.models.PlotIntegerField`
    :keyword failed_count: The total number of failed job executions.
    :type failed_count: :class:`metrics.models.PlotIntegerField`
    :keyword canceled_count: The total number of canceled job executions.
    :type canceled_count: :class:`metrics.models.PlotIntegerField`
    :keyword total_count: The total number of ended job executions (completed, failed, canceled).
    :type total_count: :class:`metrics.models.PlotIntegerField`

    :keyword error_system_count: The number of failed job executions due to a system error.
    :type error_system_count: :class:`metrics.models.PlotIntegerField`
    :keyword error_data_count: The number of failed job executions due to a data error.
    :type error_data_count: :class:`metrics.models.PlotIntegerField`
    :keyword error_algorithm_count: The number of failed job executions due to an algorithm error.
    :type error_algorithm_count: :class:`metrics.models.PlotIntegerField`

    :keyword queue_time_sum: The total time job executions were queued in seconds.
    :type queue_time_sum: :class:`metrics.models.PlotIntegerField`
    :keyword queue_time_min: The minimum time a job execution was queued in seconds.
    :type queue_time_min: :class:`metrics.models.PlotIntegerField`
    :keyword queue_time_max: The maximum time a job execution was queued in seconds.
    :type queue_time_max: :class:`metrics.models.PlotIntegerField`
    :keyword queue_time_avg: The average time job executions were queued in seconds.
    :type queue_time_avg: :class:`metrics.models.PlotIntegerField`

    :keyword pre_time_sum: The total time job executions were executing pre-task steps in seconds.
    :type pre_time_sum: :class:`metrics.models.PlotIntegerField`
    :keyword pre_time_min: The minimum time a job execution was executing pre-task steps in seconds.
    :type pre_time_min: :class:`metrics.models.PlotIntegerField`
    :keyword pre_time_max: The maximum time a job execution was executing pre-task steps in seconds.
    :type pre_time_max: :class:`metrics.models.PlotIntegerField`
    :keyword pre_time_avg: The average time job executions were executing pre-task steps in seconds.
    :type pre_time_avg: :class:`metrics.models.PlotIntegerField`

    :keyword job_time_sum: The total time job executions were executing the actual job task in seconds.
    :type job_time_sum: :class:`metrics.models.PlotIntegerField`
    :keyword job_time_min: The minimum time a job execution was executing the actual job task in seconds.
    :type job_time_min: :class:`metrics.models.PlotIntegerField`
    :keyword job_time_max: The maximum time a job execution was executing the actual job task in seconds.
    :type job_time_max: :class:`metrics.models.PlotIntegerField`
    :keyword job_time_avg: The average time job executions were executing the actual job task in seconds.
    :type job_time_avg: :class:`metrics.models.PlotIntegerField`

    :keyword post_time_sum: The total time job executions were executing post-task steps in seconds.
    :type post_time_sum: :class:`metrics.models.PlotIntegerField`
    :keyword post_time_min: The minimum time a job execution was executing post-task steps in seconds.
    :type post_time_min: :class:`metrics.models.PlotIntegerField`
    :keyword post_time_max: The maximum time a job execution was executing post-task steps in seconds.
    :type post_time_max: :class:`metrics.models.PlotIntegerField`
    :keyword post_time_avg: The average time job executions were executing post-task steps in seconds.
    :type post_time_avg: :class:`metrics.models.PlotIntegerField`

    :keyword run_time_sum: The total time job executions were running in seconds.
    :type run_time_sum: :class:`metrics.models.PlotIntegerField`
    :keyword run_time_min: The minimum time a job execution was running in seconds.
    :type run_time_min: :class:`metrics.models.PlotIntegerField`
    :keyword run_time_max: The maximum time a job execution was running in seconds.
    :type run_time_max: :class:`metrics.models.PlotIntegerField`
    :keyword run_time_avg: The average time job executions were running in seconds.
    :type run_time_avg: :class:`metrics.models.PlotIntegerField`

    :keyword stage_time_sum: The total time job executions spent in system staging between tasks in seconds.
    :type stage_time_sum: :class:`metrics.models.PlotIntegerField`
    :keyword stage_time_min: The minimum time a job execution spent in system staging between tasks in seconds.
    :type stage_time_min: :class:`metrics.models.PlotIntegerField`
    :keyword stage_time_max: The maximum time a job execution spent in system staging between tasks in seconds.
    :type stage_time_max: :class:`metrics.models.PlotIntegerField`
    :keyword stage_time_avg: The average time job executions spent in system staging between tasks in seconds.
    :type stage_time_avg: :class:`metrics.models.PlotIntegerField`

    :keyword created: When the model was first created.
    :type created: :class:`django.db.models.DateTimeField`
    """
    GROUPS = [
        MetricsTypeGroup('overview', 'Overview', 'Overall counts based on job status.'),
        MetricsTypeGroup('errors', 'Errors', 'Overall error counts based on category.'),
        MetricsTypeGroup('queue_time', 'Queue Time', 'When jobs were in the queue.'),
        MetricsTypeGroup('pre_time', 'Pre-task Time', 'When jobs were being prepared.'),
        MetricsTypeGroup('job_time', 'Job Task Time', 'When jobs were executing their actual goal.'),
        MetricsTypeGroup('post_time', 'Post-task Time', 'When jobs were being cleaned up.'),
        MetricsTypeGroup('run_time', 'Run Time', 'When related tasks were run (pre, job, post).'),
        MetricsTypeGroup('stage_time', 'Stage Time', 'Times related to the overhead of the system.'),
    ]

    job_type = models.ForeignKey('job.JobType', on_delete=models.PROTECT)
    occurred = models.DateField(db_index=True)

    completed_count = PlotIntegerField(aggregate='sum', blank=True, group='overview',
                                       help_text='Number of successfully completed jobs.', null=True, units='count',
                                       verbose_name='Completed Count')
    failed_count = PlotIntegerField(aggregate='sum', blank=True, group='overview',
                                    help_text='Number of incomplete failed jobs.', null=True, units='count',
                                    verbose_name='Failed Count')
    canceled_count = PlotIntegerField(aggregate='sum', blank=True, group='overview',
                                      help_text='Number of incomplete canceled jobs.', null=True, units='count',
                                      verbose_name='Canceled Count')
    total_count = PlotIntegerField(aggregate='sum', blank=True, group='overview',
                                   help_text='Number of completed, failed, and canceled jobs.', null=True,
                                   units='count', verbose_name='Total Count')

    error_system_count = PlotIntegerField(aggregate='sum', blank=True, group='errors',
                                          help_text='Number of failed jobs due to a system error.', null=True,
                                          units='count', verbose_name='System Error Count')
    error_data_count = PlotIntegerField(aggregate='sum', blank=True, group='errors',
                                        help_text='Number of failed jobs due to a data error.', null=True,
                                        units='count', verbose_name='Data Error Count')
    error_algorithm_count = PlotIntegerField(aggregate='sum', blank=True, group='errors',
                                             help_text='Number of failed jobs due to an algorithm error.', null=True,
                                             units='count', verbose_name='Algorithm Error Count')

    queue_time_sum = PlotIntegerField(aggregate='sum', blank=True, group='queue_time',
                                      help_text='Total time the job waited in the queue.', null=True, units='seconds',
                                      verbose_name='Queue Time (Sum)')
    queue_time_min = PlotIntegerField(aggregate='min', blank=True, group='queue_time',
                                      help_text='Minimum time the job waited in the queue.', null=True, units='seconds',
                                      verbose_name='Queue Time (Min)')
    queue_time_max = PlotIntegerField(aggregate='max', blank=True, group='queue_time',
                                      help_text='Maximum time the job waited in the queue.',
                                      null=True, units='seconds', verbose_name='Queue Time (Max)')
    queue_time_avg = PlotIntegerField(aggregate='avg', blank=True, group='queue_time',
                                      help_text='Average time the job waited in the queue.', null=True,
                                      units='seconds', verbose_name='Queue Time (Avg)')

    pre_time_sum = PlotIntegerField(aggregate='sum', blank=True, group='pre_time',
                                    help_text='Total time spent preparing the job task.', null=True, units='seconds',
                                    verbose_name='Pre-task Time (Sum)')
    pre_time_min = PlotIntegerField(aggregate='min', blank=True, group='pre_time',
                                    help_text='Minimum time spent preparing the job task.', null=True, units='seconds',
                                    verbose_name='Pre-task Time (Min)')
    pre_time_max = PlotIntegerField(aggregate='max', blank=True, group='pre_time',
                                    help_text='Maximum time spent preparing the job task.', null=True, units='seconds',
                                    verbose_name='Pre-task Time (Max)')
    pre_time_avg = PlotIntegerField(aggregate='avg', blank=True, group='pre_time',
                                    help_text='Average time spent preparing the job task.',
                                    null=True, units='seconds', verbose_name='Pre-task Time (Avg)')

    job_time_sum = PlotIntegerField(aggregate='sum', blank=True, group='job_time',
                                    help_text='Total time spent running the job task.',
                                    null=True, units='seconds', verbose_name='Job Task Time (Sum)')
    job_time_min = PlotIntegerField(aggregate='min', blank=True, group='job_time',
                                    help_text='Minimum time spent running the job task.',
                                    null=True, units='seconds', verbose_name='Job Task Time (Min)')
    job_time_max = PlotIntegerField(aggregate='max', blank=True, group='job_time',
                                    help_text='Maximum time spent running the job task.',
                                    null=True, units='seconds', verbose_name='Job Task Time (Max)')
    job_time_avg = PlotIntegerField(aggregate='avg', blank=True, group='job_time',
                                    help_text='Average time spent running the job task.',
                                    null=True, units='seconds', verbose_name='Job Task Time (Avg)')

    post_time_sum = PlotIntegerField(aggregate='sum', blank=True, group='post_time',
                                     help_text='Total time spent finalizing the job task.',
                                     null=True, units='seconds', verbose_name='Post-task Time (Sum)')
    post_time_min = PlotIntegerField(aggregate='min', blank=True, group='post_time',
                                     help_text='Minimum time spent finalizing the job task.',
                                     null=True, units='seconds', verbose_name='Post-task Time (Min)')
    post_time_max = PlotIntegerField(aggregate='max', blank=True, group='post_time',
                                     help_text='Maximum time spent finalizing the job task.',
                                     null=True, units='seconds', verbose_name='Post-task Time (Max)')
    post_time_avg = PlotIntegerField(aggregate='avg', blank=True, group='post_time',
                                     help_text='Average time spent finalizing the job task.',
                                     null=True, units='seconds', verbose_name='Post-task Time (Avg)')

    run_time_sum = PlotIntegerField(aggregate='sum', blank=True, group='run_time',
                                    help_text='Total time spent running the pre, job, and post tasks.',
                                    null=True, units='seconds', verbose_name='Run Time (Sum)')
    run_time_min = PlotIntegerField(aggregate='min', blank=True, group='run_time',
                                    help_text='Minimum time spent running the pre, job, and post tasks.',
                                    null=True, units='seconds', verbose_name='Run Time (Min)')
    run_time_max = PlotIntegerField(aggregate='max', blank=True, group='run_time',
                                    help_text='Maximum time spent running the pre, job, and post tasks.',
                                    null=True, units='seconds', verbose_name='Run Time (Max)')
    run_time_avg = PlotIntegerField(aggregate='avg', blank=True, group='run_time',
                                    help_text='Average time spent running the pre, job, and post tasks.',
                                    null=True, units='seconds', verbose_name='Run Time (Avg)')

    stage_time_sum = PlotIntegerField(aggregate='sum', blank=True, group='stage_time',
                                      help_text='Total overhead time spent managing tasks.',
                                      null=True, units='seconds', verbose_name='Stage Time (Sum)')
    stage_time_min = PlotIntegerField(aggregate='min', blank=True, group='stage_time',
                                      help_text='Minimum overhead time spent managing tasks.',
                                      null=True, units='seconds', verbose_name='Stage Time (Min)')
    stage_time_max = PlotIntegerField(aggregate='min', blank=True, group='stage_time',
                                      help_text='Maximum overhead time spent managing tasks.',
                                      null=True, units='seconds', verbose_name='Stage Time (Max)')
    stage_time_avg = PlotIntegerField(aggregate='avg', blank=True, group='stage_time',
                                      help_text='Average overhead time spent managing tasks.',
                                      null=True, units='seconds', verbose_name='Stage Time (Avg)')

    created = models.DateTimeField(auto_now_add=True)

    objects = MetricsJobTypeManager()

    class Meta(object):
        """meta information for the db"""
        db_table = 'metrics_job_type'
