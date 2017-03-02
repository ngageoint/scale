"""Defines the functions necessary to perform the ingest of a source file"""
from __future__ import unicode_literals

import logging
import os

from django.db import transaction
from django.utils.timezone import now

from ingest.models import Ingest
from ingest.triggers.ingest_trigger_handler import IngestTriggerHandler
from source.models import SourceFile
from storage.brokers.broker import FileDownload, FileMove, FileUpload
from storage.models import ScaleFile
from util.retry import retry_database_query

logger = logging.getLogger(__name__)


def perform_ingest(ingest_id):
    """Performs the ingest for the given ingest ID

    :param ingest_id: The ID of the ingest to perform
    :type ingest_id: int
    """

    ingest = _get_ingest(ingest_id)
    file_name = ingest.file_name

    if ingest.status in ['INGESTED', 'DUPLICATE']:
        logger.warning('%s already marked %s, nothing to do', file_name, ingest.status)
        return

    _start_ingest(ingest)
    if ingest.status != 'INGESTING':
        return

    try:
        source_file = ingest.source_file
        if source_file.is_deleted:
            # Source file still marked as deleted, so we must copy/move/register the file
            source_file.set_basic_fields(file_name, ingest.file_size, ingest.media_type, ingest.get_data_type_tags())
            source_file.update_uuid(file_name)  # Add a stable identifier based on the file name
            source_file.workspace = ingest.workspace
            source_file.file_path = ingest.file_path
            source_file.is_deleted = False
            source_file.is_parsed = False
            source_file.deleted = None
            source_file.parsed = None

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

    except Exception:
        _complete_ingest(ingest, 'ERRORED')
        raise

    _complete_ingest(ingest, 'INGESTED')
    logger.info('Ingest successful for %s', file_name)


@retry_database_query
def _complete_ingest(ingest, status):
    """Completes the given ingest in an atomic transaction

    :param ingest: The ingest model
    :type ingest: :class:`ingest.models.Ingest`
    :param status: The final status of the ingest
    :type status: string
    """

    # Atomically mark ingest status and run ingest trigger rules
    with transaction.atomic():
        logger.info('Marking ingest for %s as %s', ingest.file_name, status)
        ingest.status = status
        if status == 'INGESTED':
            ingest.ingest_ended = now()
        ingest.save()
        if status == 'INGESTED':
            IngestTriggerHandler().process_ingested_source_file(ingest.source_file, ingest.ingest_ended)


def _delete_file(file_path):
    """Deletes the given ingest file

    :param file_path: The absolute path of the file to delete
    :type file_path: string
    """

    if os.path.exists(file_path):
        logger.info('Deleting %s', file_path)
        os.remove(file_path)


@retry_database_query
def _get_ingest(ingest_id):
    """Returns the ingest for the given ID

    :param ingest_id: The ingest ID
    :type ingest_id: int
    :returns: The ingest model
    :rtype: :class:`ingest.models.Ingest`
    """

    return Ingest.objects.select_related().get(id=ingest_id)


def _get_source_file(file_name):
    """Returns an existing or new (un-saved) source file model for the given file name

    :param file_name: The name of the source file
    :type file_name: string
    :returns: The source file model
    :rtype: :class:`source.models.SourceFile`
    """

    try:
        src_file = SourceFile.objects.get_source_file_by_name(file_name)
    except ScaleFile.DoesNotExist:
        src_file = SourceFile.create()  # New file
        src_file.file_name = file_name
        src_file.is_deleted = True
    return src_file


@retry_database_query
def _save_source_file(source_file):
    """Saves the given source file model in the database

    :param source_file: The source file model
    :type source_file: :class:`source.models.SourceFile`
    """

    source_file.save()


@retry_database_query
def _start_ingest(ingest):
    """Starts the given ingest and links it to the source file that is being ingested

    :param ingest: The ingest model
    :type ingest: :class:`ingest.models.Ingest`
    """

    file_name = ingest.file_name
    if not ingest.source_file:
        # This ingest job is running for the first time (source_file not yet set)
        source_file = _get_source_file(file_name)
        if source_file.id:  # If source file already exists...
            if source_file.is_deleted:
                logger.info('Re-ingesting deleted file %s', file_name)
            else:
                logger.warning('File %s was already ingested and is not deleted, marking as DUPLICATE', file_name)
                ingest.source_file = source_file
                _complete_ingest(ingest, 'DUPLICATE')
                return
        else:
            logger.info('Ingesting %s for the first time', file_name)
            # Set required attributes to save the model for the first time
            source_file.set_basic_fields(file_name, ingest.file_size, ingest.media_type, ingest.get_data_type_tags())
            source_file.update_uuid(file_name)  # Add a stable identifier based on the file name
            source_file.workspace = ingest.workspace
            source_file.file_path = ingest.file_path
            source_file.save()
        ingest.source_file = source_file
    else:
        # This ingest job must have failed previously
        logger.info('This ingest job has previously failed, ingesting %s from where it left off', file_name)
    ingest.status = 'INGESTING'
    ingest.ingest_started = now()
    ingest.save()
