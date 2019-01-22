"""Defines the functions necessary to move a file to a different workspace/uri"""
from __future__ import unicode_literals

import logging
import os
import sys

from error.exceptions import ScaleError, get_error_by_exception
from storage.brokers.broker import FileDownload, FileMove, FileUpload
from storage.models import ScaleFile

logger = logging.getLogger(__name__)


GENERAL_FAIL_EXIT_CODE = 1


def move_files(files, new_workspace=None, new_file_path=None):
    """Moves the given files to a different workspace/uri

    :param files: List of ScaleFile objects to move
    :type files: [:class:`storage.models.ScaleFile`]
    :param new_workspace: New workspace to move files to
    :type new_workspace: `storage.models.Workspace`
    :param new_file_path: New path for files
    :type new_file_path: string
    """
    
    old_files = []
    old_workspace = None
    if new_workspace:
        # We need a local path to copy the file, try to get a direct path from the broker, if that fails we must
        # download the file and copy from there
        # TODO: a future refactor should make the brokers work off of file objects instead of paths so the extra
        # download is not necessary
        old_workspace = files[0].workspace
        paths = old_workspace.get_file_system_paths([files])
        local_paths = []
        if paths:
            local_paths = paths
        else:
            file_downloads = []
            for file in files:
                local_path = os.path.join('/tmp', file.file_name)
                file_downloads.append(FileDownload(file, local_path, False))
                local_paths.append(local_path)
            ScaleFile.objects.download_files(file_downloads)

        uploads = []
        for file, path in zip(files, local_paths):
            old = file.file_path
            old_files.append(ScaleFile(file_name=file.file_name, file_path=file.file_path))
            file.file_path = new_file_path if new_file_path else file.file_path
            logger.info('Copying %s in workspace %s to %s in workspace %s', old, old_workspace.name,
                    file.file_path, new_workspace.name)
            file_upload = FileUpload(file, path)
            uploads.append(file_upload)

        ScaleFile.objects.upload_files(new_workspace, uploads)
    elif new_file_path:
        moves = []
        for file in files:
            logger.info('Moving %s to %s in workspace %s', file.file_path, new_file_path,
                        file.workspace.name)
            moves.append(FileMove(file, new_file_path))
        ScaleFile.objects.move_files(moves)
    else:
        logger.info('No new workspace or file path. Doing nothing')


    if new_workspace:
        # Copied files to new workspace, so delete file in old workspace (if workspace provides local path to do so)
        old_workspace.delete_files(old_files, update_model=False)

    return

def _delete_file(file_path):
    """Deletes the given ingest file

    :param file_path: The absolute path of the file to delete
    :type file_path: string
    """

    if os.path.exists(file_path):
        logger.info('Deleting %s', file_path)
        os.remove(file_path)