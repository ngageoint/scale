"""Defines the functions necessary to move a file to a different workspace/uri"""
from __future__ import unicode_literals

import logging
import os
import sys

from error.exceptions import ScaleError, get_error_by_exception


logger = logging.getLogger(__name__)


GENERAL_FAIL_EXIT_CODE = 1


def move_files(files, volume_path, broker):
    """Moves the given files to a different workspace/uri

    :param files: List of named tuples containing path and ID of the file to move.
    :type files: [collections.namedtuple]
    :param volume_path: Absolute path to the local container location onto which the volume file system was mounted,
            None if this broker does not use a container volume
    :type volume_path: string
    :param broker: The storage broker
    :type broker: `storage.brokers.broker.Broker`
    """
    if ingest.new_workspace:
        # We need a local path to copy the file, try to get a direct path from the broker, if that fails we must
        # download the file and copy from there
        # TODO: a future refactor should make the brokers work off of file objects instead of paths so the extra
        # download is not necessary
        paths = ingest.workspace.get_file_system_paths([source_file])
        if paths:
            local_path = paths[0]
        else:
            local_path = os.path.join('/tmp', file_name)
            file_download = FileDownload(source_file, local_path, False)
            ScaleFile.objects.download_files([file_download])
        source_file.file_path = ingest.new_file_path if ingest.new_file_path else ingest.file_path
        logger.info('Copying %s in workspace %s to %s in workspace %s', ingest.file_path, ingest.workspace.name,
                    source_file.file_path, ingest.new_workspace.name)
        file_upload = FileUpload(source_file, local_path)
        ScaleFile.objects.upload_files(ingest.new_workspace, [file_upload])
    elif ingest.new_file_path:
        logger.info('Moving %s to %s in workspace %s', ingest.file_path, ingest.new_file_path,
                    ingest.workspace.name)
        file_move = FileMove(source_file, ingest.new_file_path)
        ScaleFile.objects.move_files([file_move])
    else:
        logger.info('Registering %s in workspace %s', ingest.file_path, ingest.workspace.name)
        _save_source_file(source_file)


if ingest.new_workspace:
    # Copied file to new workspace, so delete file in old workspace (if workspace provides local path to do so)
    file_with_old_path = SourceFile.create()
    file_with_old_path.file_name = file_name
    file_with_old_path.file_path = ingest.file_path
    paths = ingest.workspace.get_file_system_paths([file_with_old_path])
    if paths:
        _delete_file(paths[0])
    logger.info('Moving %i files', len(files))
    try:
        broker.move_files(volume_path=volume_path, files=files)
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

    return
