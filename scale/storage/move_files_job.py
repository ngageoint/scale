"""Defines the functions necessary to move a file to a different workspace/uri"""
from __future__ import unicode_literals

import logging
import os
import sys

from error.exceptions import ScaleError, get_error_by_exception
from messaging.manager import CommandMessageManager
from storage.brokers.broker import FileDownload, FileMove, FileUpload
from storage.messages.move_files import create_move_file_message
from storage.models import ScaleFile

logger = logging.getLogger(__name__)


GENERAL_FAIL_EXIT_CODE = 1


def move_files(file_ids, new_workspace=None, new_file_path=None):
    """Moves the given files to a different workspace/uri

    :param file_ids: List of ids of ScaleFile objects to move; should all be from the same workspace
    :type file_ids: [int]
    :param new_workspace: New workspace to move files to
    :type new_workspace: `storage.models.Workspace`
    :param new_file_path: New path for files
    :type new_file_path: string
    """
    
    try:
        messages = []
        files = ScaleFile.objects.all()
        files = files.select_related('workspace')
        files = files.defer('workspace__json_config')
        files = files.filter(id__in=file_ids).only('id', 'file_name', 'file_path', 'workspace')
        old_files = []
        old_workspace = files[0].workspace
        if new_workspace:
            # We need a local path to copy the file, try to get a direct path from the broker, if that fails we must
            # download the file and copy from there
            # TODO: a future refactor should make the brokers work off of file objects instead of paths so the extra
            # download is not necessary
    
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
                old_path = file.file_path
                old_workspace = file.workspace.name if file.workspace else "none"
                old_files.append(ScaleFile(file_name=file.file_name, file_path=file.file_path))
                file.file_path = new_file_path if new_file_path else file.file_path
                logger.info('Copying %s in workspace %s to %s in workspace %s', old_path, file.workspace.name,
                        file.file_path, new_workspace.name)
                file_upload = FileUpload(file, path)
                uploads.append(file_upload)
                message = create_move_file_message(file_id=file.id)
                messages.append(message)
    
            ScaleFile.objects.upload_files(new_workspace, uploads)
            CommandMessageManager().send_messages(messages)
        elif new_file_path:
            moves = []
            for file in files:
                logger.info('Moving %s to %s in workspace %s', file.file_path, new_file_path,
                            file.workspace.name)
                moves.append(FileMove(file, new_file_path))
                message = create_move_file_message(file_id=file.id)
                messages.append(message)
                
            ScaleFile.objects.move_files(moves)
        else:
            logger.info('No new workspace or file path. Doing nothing')
    
    
        CommandMessageManager().send_messages(messages)
        
        if new_workspace:
            # Copied files to new workspace, so delete file in old workspace (if workspace provides local path to do so)
            old_workspace.delete_files(old_files, update_model=False)

    except ScaleError as err:
        err.log()
        sys.exit(err.exit_code)
    except Exception as ex:
        exit_code = GENERAL_FAIL_EXIT_CODE
        err = get_error_by_exception(ex.__class__.__name__)
        if err:
            err.log()
            exit_code = err.exit_code
        else:
            logger.exception('Error performing move_files steps')
        sys.exit(exit_code)
