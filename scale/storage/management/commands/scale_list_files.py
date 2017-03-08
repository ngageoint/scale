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

    option_list = BaseCommand.option_list + (
        make_option('-r', '--recursive', action='store_true', dest='recursive',
                    default=False, help='Recursively process workspace tree.'),
        make_option('-l', '--local', action='store_true', dest='local',
                    default=False, help='Local patch for testing. Remote will match '
                                        'host_path.'),
        make_option('-w', '--workspace-id',
                    help='Workspace ID to traverse.'),
    )

    help = 'Lists files within a workspace.'

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
                    results = workspace.list_files(options['recursive'], self.callback)
                    logger.info('Results that were not returned via callback: %s' % results)
            else:
                results = workspace.list_files(options['recursive'], self.callback)
                logger.info('Results that were not returned via callback: %s' % results)
        except:
            logger.exception('Unknown error occurred, exit code 1 returning')
            sys.exit(1)
        logger.info('Command completed: scale_list_files')

    # Callback definition to support updates as workspace is traversed
    def callback(self, files):
        for file in files:
            logger.info(file)
