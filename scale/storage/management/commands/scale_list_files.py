"""Defines the command line method for listing files within a workspace"""
from __future__ import unicode_literals

import logging
import sys
from optparse import make_option

from django.core.management.base import BaseCommand
from mock import patch

from storage.models import Workspace

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Command for listing files within a workspace."""

    help = 'Lists files within a workspace.'

    def add_arguments(self, parser):
        parser.add_argument('-r', '--recursive', action='store_true', 
                            dest='recursive', default=False,
                            help='Recursively process workspace tree.')
        parser.add_argument('-l', '--local', action='store_true', dest='local',
                            default=False, help='Local patch for testing. Remote will match host_path.')
        parser.add_argument('-w', '--workspace-id', help='Workspace ID to traverse.')

    def handle(self, *args, **options):
        """See :meth:`django.core.management.base.BaseCommand.handle`.

        This method will list the entire contents of a workspace.
        """

        logger.info('Command starting: scale_list_files')

        if 'workspace_id' in options:
            workspace_id = options['workspace_id']
        else:
            logger.error('Workspace ID must be specified.')
            sys.exit(1)

        # Attempt to fetch the workspace model by workspace id
        try:
            workspace = Workspace.objects.get(pk=workspace_id)
        except Workspace.DoesNotExist:
            logger.exception('Workspace does not exist: %s', workspace_id)
            sys.exit(1)

        try:
            conf = workspace.json_config
            # Patch _get_volume_path for local testing outside of docker.
            # This is useful for testing when Scale isn't managing mounts.
            if options['local'] and 'broker' in conf and 'host_path' in conf['broker']:
                with patch.object(Workspace, '_get_volume_path',
                                  return_value=conf['broker']['host_path']) as mock_method:
                    results = workspace.list_files(options['recursive'])
            else:
                results = workspace.list_files(options['recursive'])
                
            for result in results:
                logger.info(file)
        except:
            logger.exception('Unknown error occurred, exit code 1 returning')
            sys.exit(1)
        logger.info('Command completed: scale_list_files')
