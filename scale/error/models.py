"""Defines the database models for errors"""
from __future__ import unicode_literals
import logging

from django.db import models, transaction

from util.exceptions import ScaleLogicBug


logger = logging.getLogger(__name__)


CACHED_BUILTIN_ERROR_NAMES = {}  # {Error Name: Error ID}
CACHED_JOB_ERROR_NAMES = {}  # {Job Type Name: {Error Name: Error ID}}
# TODO: remove caching of legacy job error names when legacy-style job types are removed
CACHED_LEGACY_JOB_ERROR_NAMES = {}  # {Error Name: Error ID}
CACHED_ERRORS = {}  # {Error ID: Error model}


def get_builtin_error(name):
    """Returns the builtin error with the given name

    :param name: The name of the error
    :type name: string
    :returns: The error with the given name
    :rtype: :class:`error.models.Error`
    """

    if name not in CACHED_BUILTIN_ERROR_NAMES:
        raise ScaleLogicBug('Unknown builtin error: %s' % name)

    error_id = CACHED_BUILTIN_ERROR_NAMES[name]
    return CACHED_ERRORS[error_id]


def get_error(error_id):
    """Returns the error with the given ID, might require database access if the error is not currently cached

    :param error_id: The ID of the error
    :type error_id: int
    :returns: The error with the given ID
    :rtype: :class:`error.models.Error`
    """

    if error_id not in CACHED_ERRORS:
        error = Error.objects.get(id=error_id)
        _cache_error(error)

    return CACHED_ERRORS[error_id]


def get_job_error(job_type_name, error_name):
    """Returns the job error with the given name, might require database access if the error is not currently cached

    :param job_type_name: The name of the job type
    :type job_type_name: string
    :param error_name: The name of the error
    :type error_name: string
    :returns: The error with the given name
    :rtype: :class:`error.models.Error`
    """

    if job_type_name is None:
        # Legacy style job type
        if error_name not in CACHED_LEGACY_JOB_ERROR_NAMES:
            error = Error.objects.get(job_type_name__isnull=True, name=error_name)
            _cache_error(error)
        error_id = CACHED_LEGACY_JOB_ERROR_NAMES[error_name]
        return CACHED_ERRORS[error_id]

    if job_type_name not in CACHED_JOB_ERROR_NAMES or error_name not in CACHED_JOB_ERROR_NAMES[job_type_name]:
        error = Error.objects.get(job_type_name=job_type_name, name=error_name)
        _cache_error(error)

    error_id = CACHED_JOB_ERROR_NAMES[job_type_name][error_name]
    return CACHED_ERRORS[error_id]


def get_unknown_error():
    """Returns the error for an unknown cause

    :returns: The unknown error
    :rtype: :class:`error.models.Error`
    """

    return get_builtin_error('unknown')


def reset_error_cache():
    """Resets the error cache, used for testing
    """

    CACHED_BUILTIN_ERROR_NAMES.clear()
    CACHED_JOB_ERROR_NAMES.clear()
    CACHED_LEGACY_JOB_ERROR_NAMES.clear()
    CACHED_ERRORS.clear()

    Error.objects.cache_builtin_errors()


def _cache_error(error):
    """Caches the given error model

    :param error: The error to cache
    :type error: :class:`error.models.Error`
    """

    CACHED_ERRORS[error.id] = error
    if error.is_builtin:
        CACHED_BUILTIN_ERROR_NAMES[error.name] = error.id
        # TODO: this is a hack for legacy jobs that use builtin Scale errors, remove this after legacy jobs are removed
        CACHED_LEGACY_JOB_ERROR_NAMES[error.name] = error.id
    else:
        if error.job_type_name is None:
            CACHED_LEGACY_JOB_ERROR_NAMES[error.name] = error.id
        else:
            if error.job_type_name not in CACHED_JOB_ERROR_NAMES:
                CACHED_JOB_ERROR_NAMES[error.job_type_name] = {}
            CACHED_JOB_ERROR_NAMES[error.job_type_name][error.name] = error.id


class ErrorManager(models.Manager):
    """Provides additional methods for handling errors"""

    def cache_builtin_errors(self):
        """Queries all errors that are built into the system and caches them for fast retrieval
        """

        for error in self.filter(is_builtin=True).iterator():
            _cache_error(error)

    def get_errors(self, started=None, ended=None, order=None):
        """Returns a list of errors within the given time range.

        :param started: Query errors updated after this amount of time.
        :type started: :class:`datetime.datetime`
        :param ended: Query errors updated before this amount of time.
        :type ended: :class:`datetime.datetime`
        :param order: A list of fields to control the sort order.
        :type order: list[str]
        :returns: The list of errors that match the time range.
        :rtype: list[:class:`error.models.Error`]
        """

        # Fetch a list of errors
        errors = self.all()

        # Apply time range filtering
        if started:
            errors = errors.filter(last_modified__gte=started)
        if ended:
            errors = errors.filter(last_modified__lte=ended)

        # Apply sorting
        if order:
            errors = errors.order_by(*order)
        else:
            errors = errors.order_by('last_modified')
        return errors

    def get_by_natural_key(self, job_type_name, error_name):
        """Django method to retrieve an error for the given natural key

        :param job_type_name: The name of the job type
        :type job_type_name: string
        :param name: The name of the error
        :type name: string
        :returns: The error defined by the natural key
        :rtype: :class:`error.models.Error`
        """

        return self.get(job_type_name=job_type_name, name=error_name)

    def save_job_error_models(self, job_type_name, error_models):
        """Saves the given job error models to the database

        :param job_type_name: The job type name
        :type job_type_name: string
        :param error_models: The error models
        :type error_models: list
        """

        error_names = [error.name for error in error_models]
        existing_errors = {err.name: err for err in self.filter(job_type_name=job_type_name, name__in=error_names)}
        for error_model in error_models:
            if error_model.name in existing_errors:
                # Error already exists, grab ID so save() will perform an update
                error_model.id = existing_errors[error_model.name].id
                error_model.created = existing_errors[error_model.name].created # Keep created value unchanged
            error_model.save()

    # TODO - this is for creating errors for legacy job types, remove when legacy job types are removed
    def create_legacy_error(self, name, title, description, category):
        """Create a new error in the database.

        :param name: The name of the error
        :type name: str
        :param title: The title of the error
        :type title: str
        :param description: A longer description of the error
        :type description: str
        :param category: The category of the error
        :type: str in Error.CATEGORIES
        """

        error = Error()
        error.name = name
        error.title = title
        error.description = description
        error.category = category
        error.save()
        return error


class Error(models.Model):
    """Represents an error that occurred during processing

    :keyword name: The identifying name of the error
    :type name: :class:`django.db.models.CharField`
    :keyword job_type_name: The name of the job type that relates to this error
    :type job_type_name: :class:`django.db.models.CharField`
    :keyword title: The human-readable name of the error
    :type title: :class:`django.db.models.CharField`
    :keyword description: A longer description of the error
    :type description: :class:`django.db.models.CharField`
    :keyword category: The category of the error
    :type category: :class:`django.db.models.CharField`
    :keyword is_builtin: Where the error is a builtin Scale error that does not relate to a particular job type
    :type is_builtin: :class:`django.db.models.BooleanField`
    :keyword should_be_retried: Whether a job failure with this error should be automatically retried
    :type should_be_retried: :class:`django.db.models.BooleanField`

    :keyword created: When the error model was created
    :type created: :class:`django.db.models.DateTimeField`
    :keyword last_modified: When the error model was last modified
    :type last_modified: :class:`django.db.models.DateTimeField`
    """

    CATEGORIES = (
        ('SYSTEM', 'SYSTEM'),
        ('ALGORITHM', 'ALGORITHM'),
        ('DATA', 'DATA'),
    )

    name = models.CharField(max_length=50)
    job_type_name = models.CharField(blank=True, max_length=250, null=True)
    title = models.CharField(blank=True, max_length=50, null=True)
    description = models.CharField(blank=True, max_length=250, null=True)
    category = models.CharField(choices=CATEGORIES, default='SYSTEM', max_length=50)
    is_builtin = models.BooleanField(db_index=True, default=False)
    should_be_retried = models.BooleanField(default=False)

    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    objects = ErrorManager()

    def natural_key(self):
        """Django method to define the natural key for an error as the name

        :returns: A tuple representing the natural key
        :rtype: tuple
        """

        return (self.job_type_name, self.name)
    
    def create(self):
        return super.create()

    class Meta(object):
        """Meta information for the db"""
        db_table = 'error'
        unique_together = ('job_type_name', 'name')


class LogEntry(models.Model):
    """Represents a log entry that occurred during processing

    :keyword host: The name of the cluster node that generated the LogRecord
    :type host: :class:`django.db.models.CharField`
    :keyword level: The severity/importance of the log entry
    :type level: :class:`django.db.models.CharField`
    :keyword message: The message generated from the cluster node
    :type message: :class:`django.db.models.TextField`
    :keyword created: When the log entry was created
    :type created: :class:`django.db.models.DateTimeField`
    :keyword stacktrace: A stack trace of the LogRecord if one is available
    :type stacktrace: :class:`django.db.models.TextField`
    """

    host = models.CharField(max_length=128)
    level = models.CharField(max_length=32)
    message = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    stacktrace = models.TextField(null=True)

    class Meta(object):
        """meta information for the db"""
        db_table = 'logentry'
