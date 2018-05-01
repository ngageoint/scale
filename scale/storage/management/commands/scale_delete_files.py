"""Defines the command line method for running a delete files task"""
from __future__ import unicode_literals

import ast
import json
import logging
import os
import signal
import sys
from collections import namedtuple

from django.core.management.base import BaseCommand

import storage.delete_files_job as delete_files_job
from error.exceptions import ScaleError, get_error_by_exception
from storage.brokers.factory import get_broker
from storage.configuration.workspace_configuration import WorkspaceConfiguration
from messaging.manager import CommandMessageManager
from storage import delete_files_job
from storage.messages.delete_files import create_delete_files_messages

logger = logging.getLogger(__name__)

GENERAL_FAIL_EXIT_CODE = 1


def eval_input(string):
    """Evaluates the input string
    """

    return ast.literal_eval(string.lstrip())


class Command(BaseCommand):
    """Command that executes the delete file process for a given file
    """

    help = 'Perform a file destruction operation on a file'

    def add_arguments(self, parser):
        parser.add_argument('-f', '--files', nargs='+', type=json.loads, required=True,
                            help='File path and ID in a JSON string.  Submit multiple if needed.' +
                            ' e.g: "{"file_path":"some.file", "id":"399", "workspace":"cool_workspace_name"}"')
        parser.add_argument('-w', '--workspace', action='append', type=eval_input, required=True,
                            help='Named workspace configuration in a JSON string. Submit multiple if needed.' +
                            ' e.g: "{"cool_workspace_name": {...} }"')
        parser.add_argument('-p', '--purge', action='store', type=bool, required=True,
                            help='Purge all records for the given file')

    def handle(self, *args, **options):
        """See :meth:`django.core.management.base.BaseCommand.handle`.

        This method starts the file destruction process.
        """

        # Register a listener to handle clean shutdowns
        signal.signal(signal.SIGTERM, self._onsigterm)

        files = options.get('files')
        workspace_list = options.get('workspace')
        purge = options.get('purge')

        workspaces = self._detect_workspaces(workspace_list)
        files = self._configure_files(files, workspaces)

        logger.info('Command starting: scale_delete_files')
        logger.info('File IDs: %s', [x.id for x in files])

        for wrkspc_name, wrkspc in workspaces.iteritems():
            delete_files_job.delete_files(files=[f for f in files if f.workspace == wrkspc_name],
                                          broker=wrkspc['broker'], volume_path=wrkspc['volume_path'])

        messages = create_delete_files_messages(files=files, purge=purge)
        CommandMessageManager().send_messages(messages)

        logger.info('Command completed: scale_delete_files')

        sys.exit(0)

    def _configure_files(self, file_list, workspaces):
        """Parses and returns files associated with their respective workspace.

        :param file_list: The file list that was given
        :type file_list: [dict]
        :return: All workspaces by given name with associated broker and volume_path
        :rtype: dict
        """

        scale_file = namedtuple('ScaleFile', ['id', 'file_path', 'workspace'])

        files = []
        for f in file_list:
            try:
                wrkspc = workspaces[f['workspace']]
            except KeyError:
                exit_code = GENERAL_FAIL_EXIT_CODE
                logger.exception('Workspace referenced in files list not found in given workspaces')
                sys.exit(exit_code)

            files.append(scale_file(id=int(f['id']), file_path=f['file_path'], workspace=f['workspace']))
        return files

    def _detect_workspaces(self, workspace_list):
        """Parses, validates, and returns workspace information for the given workspaces

        :param workspace_list: The workspace list that was given
        :type workspace_list: [dict]
        :return: All workspaces by given name with associated broker and volume_path
        :rtype: dict
        """

        workspaces = {}
        for workspace in workspace_list:
            name = workspace.keys()[0]
            wrkspc = WorkspaceConfiguration(workspace[name])
            wrkspc.validate_broker()
            valid_wrkspc = wrkspc.get_dict()

            workspaces[name] = {
                'broker': get_broker(valid_wrkspc['broker']['type']),
                'volume_path' : valid_wrkspc['broker']['host_path']
            }

        return workspaces

    def _onsigterm(self, signum, _frame):
        """See signal callback registration: :py:func:`signal.signal`.

        This callback performs a clean shutdown when a TERM signal is received.
        """

        logger.info('Delete Files terminating due to receiving sigterm')
        sys.exit(1)
