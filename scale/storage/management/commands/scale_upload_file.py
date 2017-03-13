"""Defines the command line method for uploading a file"""
from __future__ import unicode_literals

import logging
import os
import sys
from optparse import make_option

from django.core.management.base import BaseCommand

from storage.brokers.broker import FileUpload
from storage.models import ScaleFile, Workspace

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Command that uploads a local file to the storage system."""

    help = 'Uploads a local file to the storage system'

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workspace', action='store', type='str',
                            help='The name of the workspace used to store the file')

    def handle(self, local_path, remote_path, **options):
        """See :meth:`django.core.management.base.BaseCommand.handle`.

        This method starts the file upload process.
        """

        workspace_name = options.get('workspace')

        logger.info('Command starting: scale_upload_file')
        logger.info(' - Workspace: %s', workspace_name)

        # Validate the file paths
        file_name = os.path.basename(local_path)
        if not os.path.exists(local_path):
            logger.exception('Local file does not exist: %s', local_path)
            sys.exit(1)

        # Attempt to fetch the workspace model
        try:
            workspace = Workspace.objects.get(name=workspace_name)
        except Workspace.DoesNotExist:
            logger.exception('Workspace does not exist: %s', workspace_name)
            sys.exit(1)

        # Attempt to set up a file model
        try:
            scale_file = ScaleFile.objects.get(file_name=file_name)
        except ScaleFile.DoesNotExist:
            scale_file = ScaleFile()
            scale_file.update_uuid(file_name)
        scale_file.file_path = remote_path

        try:
            ScaleFile.objects.upload_files(workspace, [FileUpload(scale_file, local_path)])
        except:
            logger.exception('Unknown error occurred, exit code 1 returning')
            sys.exit(1)
        logger.info('Command completed: scale_upload_file')
