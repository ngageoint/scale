"""Defines the command line method for deleting a file"""
from __future__ import unicode_literals

import logging
import sys

from django.core.management.base import BaseCommand

from storage.models import ScaleFile

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Command that deletes a stored file from the remote file system."""

    help = 'Deletes a stored file from the remote file system'

    def handle(self, file_id, **options):
        """See :meth:`django.core.management.base.BaseCommand.handle`.

        This method starts the file delete process.
        """

        logger.info('Command starting: scale_delete_file')

        # Attempt to fetch the file model
        try:
            scale_file = ScaleFile.objects.get(pk=file_id)
        except ScaleFile.DoesNotExist:
            logger.exception('Stored file does not exist: %s', file_id)
            sys.exit(1)

        try:
            ScaleFile.objects.delete_files([scale_file])
        except:
            logger.exception('Unknown error occurred, exit code 1 returning')
            sys.exit(1)
        logger.info('Command completed: scale_delete_file')
