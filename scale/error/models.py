"""Defines the database models for errors"""
from __future__ import unicode_literals
import logging

from django.db import models, transaction

from util.exceptions import ScaleLogicBug


logger = logging.getLogger(__name__)


CACHED_BUILTIN_ERROR_NAMES = {}  # {Name: Error ID}
CACHED_ERRORS = {}  # {Error ID: Error model}

# TODO: Once Seed job types are in place, we can update job errors to be cached by a combination of job type rev ID (?)
# and exit code
CACHED_JOB_ERROR_NAMES = {}  # {Name: Error ID}


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


def get_job_error(name):
    """Returns the job error with the given name, might require database access if the error is not currently cached

    :param name: The name of the error
    :type name: string
    :returns: The error with the given name
    :rtype: :class:`error.models.Error`
    """

    if name not in CACHED_JOB_ERROR_NAMES:
        error = Error.objects.get(name=name)
        _cache_error(error)

    error_id = CACHED_JOB_ERROR_NAMES[name]
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
    CACHED_ERRORS.clear()
    CACHED_JOB_ERROR_NAMES.clear()

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
        CACHED_JOB_ERROR_NAMES[error.name] = error.id
    else:
        CACHED_JOB_ERROR_NAMES[error.name] = error.id


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

    def get_by_natural_key(self, name):
        """Django method to retrieve an error for the given natural key

        :param name: The name of the error
        :type name: str
        :returns: The error defined by the natural key
        :rtype: :class:`error.models.Error`
        """

        return self.get(name=name)

    @transaction.atomic
    def get_or_create_seed_error(self, job_type_name, job_version, error):
        """Get existing error object or create new one

        :param job_type_name: Seed compliant name for job type
        :type job_type_name: str`
        :param job_version: Seed compliant (semver) version of job
        :type job_version: str
        :param error: Seed Manifest error object
        :type error: dict
        :return:
        """

        category = 'ALGORITHM' if 'job' in error['category'] else 'DATA'

        name = '-'.join([job_type_name, job_version, str(error['code'])])

        error_obj = Error.objects.get_or_create(name=name,
                                                defaults={
                                                    'title': error['title'],
                                                    'description': error['description'],
                                                    'category': category
                                                })
        logger.info(error_obj)
        return error_obj

    @transaction.atomic
    def create_error(self, name, title, description, category):
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

    :keyword name: The identifying name of the error used by clients for queries
    :type name: :class:`django.db.models.CharField`
    :keyword title: The human-readable name of the error
    :type title: :class:`django.db.models.CharField`
    :keyword description: A longer description of the error
    :type description: :class:`django.db.models.CharField`
    :keyword category: The category of the error
    :type category: :class:`django.db.models.CharField`
    :keyword is_builtin: Where the error was loaded during system installation.
    :type is_builtin: :class:`django.db.models.BooleanField`
    :keyword should_be_retried: Whether the error should be automatically retried
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

    name = models.CharField(db_index=True, max_length=50, unique=True)
    title = models.CharField(blank=True, max_length=50, null=True)
    description = models.CharField(max_length=250, null=True)
    category = models.CharField(db_index=True, choices=CATEGORIES, default='SYSTEM', max_length=50)
    is_builtin = models.BooleanField(db_index=True, default=False)
    should_be_retried = models.BooleanField(default=False)

    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    objects = ErrorManager()

    def natural_key(self):
        """Django method to define the natural key for an error as the name

        :returns: A tuple representing the natural key
        :rtype: tuple(str,)
        """

        return (self.name,)

    class Meta(object):
        """meta information for the db"""
        db_table = 'error'


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
