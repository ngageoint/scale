"""error models"""
from __future__ import unicode_literals
import logging

from django.db import models, transaction

logger = logging.getLogger(__name__)


CACHED_BUILTIN_ERRORS = {}  # {Name: Error model}


class ErrorManager(models.Manager):
    """Provides additional methods for handling errors
    """

    def get_builtin_error(self, name):
        """Returns the builtin error with the given name

        :param name: The name of the error
        :type name: str
        :returns: The error with the given name
        :rtype: :class:`error.models.Error`
        """

        if name not in CACHED_BUILTIN_ERRORS:
            error = Error.objects.get(name=name)
            CACHED_BUILTIN_ERRORS[name] = error
        return CACHED_BUILTIN_ERRORS[name]

    def get_database_error(self):
        """Returns the error for a database problem

        :returns: The database error
        :rtype: :class:`error.models.Error`
        """
        return self.get_builtin_error('database')

    def get_filesystem_error(self):
        """Returns the error for a filesystem problem

        :returns: The filesystem error
        :rtype: :class:`error.models.Error`
        """
        return self.get_builtin_error('filesystem-io')

    def get_nfs_error(self):
        """Returns the error for an NFS problem

        :returns: The NFS error
        :rtype: :class:`error.models.Error`
        """
        return self.get_builtin_error('nfs')

    def get_unknown_error(self):
        """Returns the error for an unknown cause

        :returns: The unknown error
        :rtype: :class:`error.models.Error`
        """
        return self.get_builtin_error('unknown')

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
        errors = Error.objects.all()

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

    :keyword name: The stable name of the error used by clients for queries
    :type name: :class:`django.db.models.CharField`
    :keyword title: The human-readable name of the error
    :type title: :class:`django.db.models.CharField`
    :keyword description: A longer description of the error
    :type description: :class:`django.db.models.CharField`
    :keyword category: The category of the error
    :type category: :class:`django.db.models.CharField`

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

    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    objects = ErrorManager()

    def natural_key(self):
        """Django method to define the natural key for an error as the error
        name

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
