"""Defines the command line method for running a destroy file task"""
from __future__ import unicode_literals

import logging
import signal
import sys
from optparse import make_option

from django.core.management.base import BaseCommand

import storage.destroy_file_job as destroy_file_job

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Command that executes the destroy file process for a given file
    """

    help = 'Perform a file destruction operation on a file'

    def add_arguments(self, parser):
        parser.add_argument('-f', '--file_path', action='store', type=str,
                            help='Absolute path of the file to delete')
        parser.add_argument('-j', '--job_id', action='store', type=int,
                            help='ID of the Job model')

    def handle(self, *args, **options):
        """See :meth:`django.core.management.base.BaseCommand.handle`.

        This method starts the file destruction process.
        """

        # Register a listener to handle clean shutdowns
        signal.signal(signal.SIGTERM, self._onsigterm)

        file_path = options.get('file_path')
        job_id = options.get('job_id')

        logger.info('Command starting: scale_destroy_file')
        logger.info('File path: %s', file_path)
        logger.info('Job ID: %i', job_id)

        destroy_file_job.destroy_file(file_path, job_id)

        logger.info('Command completed: scale_destroy_file')

    def _onsigterm(self, signum, _frame):
        """See signal callback registration: :py:func:`signal.signal`.

        This callback performs a clean shutdown when a TERM signal is received.
        """

        logger.info('Destroy File terminating due to receiving sigterm')
        sys.exit(1)
