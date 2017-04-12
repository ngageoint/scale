"""Defines the command line method for moving a file"""
from __future__ import unicode_literals

import logging
import sys

from django.core.management.base import BaseCommand

from storage.brokers.broker import FileMove
from storage.models import ScaleFile

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Command that moves a stored file to a new remote path."""

    help = 'Moves a stored file to a new remote path'
    
    def add_arguments(self, parser):
        parser.add_argument('file_id', type=int,
                            help='ID of the ScaleFile object to delete.')
        parser.add_argument('remote_path', help='Path to the remote target location.')

    def handle(self, *args, **options):
        """See :meth:`django.core.management.base.BaseCommand.handle`.

        This method starts the file move process.
        """

        logger.info('Command starting: scale_move_file')

        file_id = options.get('file_id')
        remote_path = options.get('remote_path')
        
        # Attempt to fetch the file model
        try:
            scale_file = ScaleFile.objects.get(pk=file_id)
        except ScaleFile.DoesNotExist:
            logger.exception('Stored file does not exist: %s', file_id)
            sys.exit(1)

        try:
            ScaleFile.objects.move_files([FileMove(scale_file, remote_path)])
        except:
            logger.exception('Unknown error occurred, exit code 1 returning')
            sys.exit(1)
        logger.info('Command completed: scale_move_file')
