"""Defines the command line method for moving a file"""
from __future__ import unicode_literals

import json
import logging
import os
import signal
import sys
from collections import namedtuple

from django.core.management.base import BaseCommand

from messaging.manager import CommandMessageManager
from storage import move_files_job
from storage.models import Workspace


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Command that moves a stored file to a new remote path."""

    help = 'Moves a stored file to a new remote path'

    def handle(self, *args, **options):
        """See :meth:`django.core.management.base.BaseCommand.handle`.

        This method starts the file move process.
        """

        logger.info('Command starting: scale_move_files')
        # Register a listener to handle clean shutdowns
        signal.signal(signal.SIGTERM, self._onsigterm)

        file_ids = json.loads(os.environ.get('FILE_IDS'))
        new_workspace_name = json.loads(os.environ.get('NEW_WORKSPACE'))
        uri = json.loads(os.environ.get('NEW_PATH'))

        new_workspace = None
        if new_workspace_name:
            try:
                new_workspace = Workspace.objects.get(name=new_workspace_name)
            except Workspace.DoesNotExist:
                logger.error('Error running command scale_move_files: Workspace %s does not exist' % new_workspace_name)
                sys.exit(1)

        logger.info('Command starting: scale_move_files')
        logger.info('File IDs: %s', file_ids)
        
        move_files_job.move_files(file_ids=file_ids, new_workspace=new_workspace, new_file_path=uri)
        
        #add messages here or in the move files job to update urls in file meta-data

        logger.info('Command completed: scale_move_files')

        sys.exit(0)

    def _onsigterm(self, signum, _frame):
        """See signal callback registration: :py:func:`signal.signal`.

        This callback performs a clean shutdown when a TERM signal is received.
        """

        logger.info('Delete Files terminating due to receiving sigterm')
        sys.exit(1)