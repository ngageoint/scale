"""Defines the command line method for running a destroy file task"""
from __future__ import unicode_literals

import json
import logging
import signal
import sys

from django.core.management.base import BaseCommand

import storage.destroy_file_job as destroy_file_job
from messaging.manager import CommandMessageManager
from storage.messages.delete_files import create_delete_files_messages
from storage.models import ScaleFile

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Command that executes the destroy file process for a given file
    """

    help = 'Perform a file destruction operation on a file'

    def add_arguments(self, parser):
        parser.add_argument('-f', '--files', nargs='+', type=json.loads, required=True,
                            help='File path and ID in a dictionary string.' +
                                 ' e.g: "{"file_path":"/some/path/to.file", "file_id":"399"}"')
        parser.add_argument('-j', '--job_id', action='store', type=int, required=True,
                            help='ID of the Job model')
        parser.add_argument('-p', '--purge', action='store', type=bool, required=True,
                            help='Purge all records for the given file')

    def handle(self, *args, **options):
        """See :meth:`django.core.management.base.BaseCommand.handle`.

        This method starts the file destruction process.
        """

        # Register a listener to handle clean shutdowns
        signal.signal(signal.SIGTERM, self._onsigterm)

        files = options.get('files')
        job_id = options.get('job_id')
        purge = options.get('purge')

        file_ids = [int(x['file_id']) for x in files]

        logger.info('Command starting: scale_destroy_file')
        logger.info('File IDs: %s', file_ids)
        logger.info('Job ID: %i', job_id)

        for f in files:
            destroy_file_job.destroy_file(f['file_path'], job_id)

        messages = create_delete_files_messages(file_ids=file_ids, purge=purge)
        CommandMessageManager().send_messages(messages)

        logger.info('Command completed: scale_destroy_file')

    def _onsigterm(self, signum, _frame):
        """See signal callback registration: :py:func:`signal.signal`.

        This callback performs a clean shutdown when a TERM signal is received.
        """

        logger.info('Destroy File terminating due to receiving sigterm')
        sys.exit(1)
