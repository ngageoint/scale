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
from storage.brokers.broker import FileDownload, FileMove, FileUpload
from storage.brokers.factory import get_broker
from storage.configuration.json.workspace_config_v6 import WorkspaceConfigurationV6
from storage.messages.move_files import create_move_files_messages


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

        files_list = json.loads(os.environ.get('FILES'))
        workspaces = json.loads(os.environ.get('WORKSPACES'))
        uris = json.loads(os.environ.get('URIS'))

        workspaces = self._configure_workspaces(workspaces)
        files = self._configure_files(files_list, workspaces)

        logger.info('Command starting: scale_move_files')
        logger.info('File IDs: %s', [x.id for x in files])
        
        for wrkspc_name, wrkspc in workspaces.iteritems():
            move_files_job.move_files(files=[f for f in files if f.workspace == wrkspc_name],
                                          broker=wrkspc['broker'], volume_path=wrkspc['volume_path'])

        messages = create_move_files_messages(files=files, workspace=workspace, uri=uri)
        CommandMessageManager().send_messages(messages)

        logger.info('Command completed: scale_move_files')

        sys.exit(0)

    def _configure_files(self, files_list):
        """Parses and returns files associated with their respective workspace.

        :param files_list: The file list that was given
        :type files_list: [dict]
        :return: All workspaces by given name with associated broker and volume_path
        :rtype: dict
        """

        scale_file = namedtuple('ScaleFile', ['id', 'file_path', 'workspace'])

        files = []
        for f in files_list:
            files.append(scale_file(id=int(f['id']), file_path=f['file_path'], workspace=f['workspace']))
        return files

    def _configure_workspace(self, workspace):
        """Parses, validates, and returns workspace information for the given workspace

        :param workspace: The workspace
        :type workspace: dict
        :return: Workspace with associated broker and volume_path
        :rtype: dict
        """

        name = workspace.keys()[0]
        wrkspc = WorkspaceConfigurationV6(workspace[name]).get_configuration()
        wrkspc.validate_broker()
        valid_wrkspc = wrkspc.get_dict()

        ret_workspace = {
            'broker': get_broker(valid_wrkspc['broker']['type']),
            'volume_path' : valid_wrkspc['broker']['host_path']
        }

        return ret_workspace

    def _onsigterm(self, signum, _frame):
        """See signal callback registration: :py:func:`signal.signal`.

        This callback performs a clean shutdown when a TERM signal is received.
        """

        logger.info('Delete Files terminating due to receiving sigterm')
        sys.exit(1)