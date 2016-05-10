"""Defines the functions necessary to perform the ingest of a source file"""
from __future__ import unicode_literals

import logging
import os

from django.db import transaction

import django.utils.timezone as timezone
from ingest.container import SCALE_INGEST_MOUNT_PATH
from ingest.models import Ingest
from ingest.triggers.ingest_trigger_handler import IngestTriggerHandler
from job.execution.cleanup import cleanup_job_exe
from job.models import JobExecution
from source.models import SourceFile
from storage.exceptions import DuplicateFile
from storage.nfs import nfs_mount, nfs_umount
from util.retry import retry_database_query


logger = logging.getLogger(__name__)


def perform_ingest(ingest_id, mount):
    """Performs the ingest for the given ingest ID

    :param ingest_id: The ID of the ingest to perform
    :type ingest_id: int
    :param mount: The file system to mount in the form of host:/dir/path
    :type mount: string
    """

    # TODO: refactor to combine _get_ingest(), _get_job_exe_id(), and _set_ingesting_status() in one database
    # transaction with as few queries as possible, include retries
    ingest = _get_ingest(ingest_id)
    job_exe_id = _get_job_exe_id(ingest)
    if not os.path.exists(SCALE_INGEST_MOUNT_PATH):
        logger.info('Creating %s', SCALE_INGEST_MOUNT_PATH)
        os.makedirs(SCALE_INGEST_MOUNT_PATH, mode=0755)
    dup_path = os.path.join(SCALE_INGEST_MOUNT_PATH, 'duplicate', ingest.file_name)
    ingest_path = os.path.join(SCALE_INGEST_MOUNT_PATH, ingest.ingest_path)
    nfs_mount(mount, SCALE_INGEST_MOUNT_PATH, read_only=False)

    try:
        # Check condition of the ingest
        ingest = _set_ingesting_status(ingest, ingest_path, dup_path)
        if ingest is None:
            return

        logger.info('Storing %s into %s on %s', ingest_path, ingest.file_path, ingest.workspace.name)
        try:
            # TODO: future refactor: before copying file, grab existing source file (no lock) or create and save model
            # This guarantees that source file exists and can be used to check if file is duplicate
            # After this step, the source file should be marked as is_deleted so that it can't be used yet
            src_file = SourceFile.objects.store_file(ingest_path, ingest.get_data_type_tags(), ingest.workspace,
                                                     ingest.file_path)

            _complete_ingest(ingest, 'INGESTED', src_file)
            _delete_ingest_file(ingest_path)
            logger.info('Ingest successful: %s', ingest_path)
        except DuplicateFile:
            logger.warning('Duplicate file detected: %i', ingest_id, exc_info=True)
            # TODO: future refactor: pass source file model in so source files have duplicate ingests tied to them
            _complete_ingest(ingest, 'DUPLICATE', None)
            _move_ingest_file(ingest_path, dup_path)
        except Exception:
            # TODO: have this delete the stored source file using some SourceFile.objects.delete_file method
            # TODO: future refactor: pass source file model in so source files have errored ingests tied to them
            # TODO: change ERRORED to FAILED
            _complete_ingest(ingest, 'ERRORED', None)
            raise  # File remains where it is so it can be processed again
    finally:
        nfs_umount(SCALE_INGEST_MOUNT_PATH)

    try:
        cleanup_job_exe(job_exe_id)
    except Exception:
        logger.exception('Job Execution %i: Error cleaning up', job_exe_id)


@retry_database_query
def _complete_ingest(ingest, status, source_file):
    """Completes the given ingest by marking its

    :param ingest: The ingest model
    :type ingest: :class:`ingest.models.Ingest`
    :param status: The final status of the ingest
    :type status: string
    :param source_file: The model of the source file that was ingested
    :type source_file: :class:`source.models.SourceFile`
    """

    # TODO: future refactor: this will also be responsible for saving the source file model

    # Atomically mark ingest status and run ingest trigger rules
    with transaction.atomic():
        logger.info('Marking ingest %i as %s', ingest.id, status)
        ingest.source_file = source_file
        ingest.status = status
        if status == 'INGESTED':
            ingest.ingest_ended = timezone.now()
        ingest.save()
        if status == 'INGESTED':
            IngestTriggerHandler().process_ingested_source_file(ingest.source_file, ingest.ingest_ended)


def _delete_ingest_file(ingest_path):
    """Deletes the given ingest file

    :param ingest_path: The absolute path of the file to delete
    :type ingest_path: string
    """
    if os.path.exists(ingest_path):
        logger.info('Deleting %s', ingest_path)
        os.remove(ingest_path)


@retry_database_query
def _get_ingest(ingest_id):
    """Returns the ingest for the given ID

    :param ingest_id: The ingest ID
    :type ingest_id: int
    :returns: The ingest model
    :rtype: :class:`ingest.models.Ingest`
    """

    return Ingest.objects.select_related().get(id=ingest_id)


@retry_database_query
def _get_job_exe_id(ingest):
    """Returns the latest job execution ID for the given ingest

    :param ingest: The ingest model
    :type ingest: :class:`ingest.models.Ingest`
    :returns: The latest job execution ID
    :rtype: int
    """

    return JobExecution.objects.get_latest([ingest.job])[ingest.job.id].id


def _move_ingest_file(ingest_path, dest_path):
    """Moves the given ingest file to a new location

    :param ingest_path: The absolute path of the file to move
    :type ingest_path: string
    :param dest_path: The absolute path of the new location for the file
    :type dest_path: string
    """
    if os.path.exists(ingest_path):
        dest_dir = os.path.dirname(dest_path)
        if not os.path.exists(dest_dir):
            logger.info('Creating %s', dest_dir)
            os.makedirs(dest_dir, mode=0755)
        logger.info('Moving %s to %s', ingest_path, dest_path)
        os.rename(ingest_path, dest_path)


@retry_database_query
def _set_ingesting_status(ingest, ingest_path, dup_path):
    """Checks the condition of the ingest and if good, updates its status in the database to INGESTING and returns the
    model. If None is returned, then the ingest process should stop.

    :param ingest: The ingest model
    :type ingest: :class:`ingest.models.Ingest`
    :param ingest_path: The absolute path of the ingest file
    :type ingest_path: string
    :param dup_path: The absolute path of the duplicate ingest file
    :type dup_path: string
    :returns: The ingest model
    :rtype: :class:`ingest.models.Ingest`
    """
    logger.info('Preparing to ingest %s', ingest_path)

    if ingest.status == 'INGESTED':
        msg = 'Ingest already marked INGESTED but file not deleted, likely due to previous error'
        logger.warning(msg)
        _delete_ingest_file(ingest_path)
        return None
    elif ingest.status == 'DUPLICATE':
        msg = 'Ingest already marked DUPLICATE but file not moved, likely due to previous error'
        logger.warning(msg)
        _move_ingest_file(ingest_path, dup_path)
        return None
    elif not ingest.status in ['QUEUED', 'INGESTING', 'ERRORED']:
        raise Exception('Cannot ingest file with status %s' % ingest.status)

    ingest.status = 'INGESTING'
    ingest.ingest_started = timezone.now()
    ingest.save()
    return ingest
