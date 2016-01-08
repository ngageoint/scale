'''Defines the functions necessary to perform the ingest of a source file'''
from __future__ import unicode_literals

import logging
import os
import shutil

from django.db import transaction

import django.utils.timezone as timezone
from ingest.file_system import get_ingest_work_dir
from ingest.models import Ingest
from ingest.triggers.ingest_trigger_handler import IngestTriggerHandler
from job.execution.cleanup import cleanup_job_exe
from job.execution.file_system import create_job_exe_dir
from job.models import JobExecution
from source.models import SourceFile
from storage.exceptions import DuplicateFile
from storage.models import ScaleFile
from storage.nfs import nfs_mount


logger = logging.getLogger(__name__)


def perform_ingest(ingest_id, mount):
    '''Performs the ingest for the given ingest ID

    :param ingest_id: The ID of the ingest to perform
    :type ingest_id: long
    :param mount: The file system to mount in the form of host:/dir/path
    :type mount: str
    '''

    job_exe_id = None
    upload_work_dir = None
    try:
        ingest = Ingest.objects.select_related().get(id=ingest_id)
        job_exe_id = JobExecution.objects.get_latest([ingest.job])[ingest.job.id].id
        create_job_exe_dir(job_exe_id)
        ingest_work_dir = get_ingest_work_dir(job_exe_id)
        dup_path = os.path.join(ingest_work_dir, 'duplicate', ingest.file_name)
        ingest_path = os.path.join(ingest_work_dir, ingest.ingest_path)
        upload_work_dir = os.path.join(os.path.dirname(ingest_path), 'upload', str(ingest_id))
        if not os.path.exists(ingest_work_dir):
            logger.info('Creating %s', ingest_work_dir)
            os.makedirs(ingest_work_dir, mode=0755)
        nfs_mount(mount, ingest_work_dir, read_only=False)
        if not os.path.exists(upload_work_dir):
            logger.info('Creating %s', upload_work_dir)
            os.makedirs(upload_work_dir, mode=0755)

        # Check condition of the ingest
        ingest = _set_ingesting_status(ingest, ingest_path, dup_path)
        if ingest is None:
            return

        logger.info('Storing %s into %s on %s', ingest_path, ingest.file_path, ingest.workspace.name)
        try:
            src_file = SourceFile.objects.store_file(upload_work_dir, ingest_path, ingest.get_data_type_tags(),
                                                     ingest.workspace, ingest.file_path)
            # Atomically store file, mark INGESTED, and run ingest trigger rules
            with transaction.atomic():
                # TODO: It's possible that the file will be successfully moved into the workspace but this database
                # transaction might fail. This will result in a file that is in a workspace but doesn't have database
                # entries. Attempts to re-ingest will result in duplicate file errors.
                logger.info('Marking file as INGESTED: %i', ingest_id)
                ingest.source_file = src_file
                ingest.status = 'INGESTED'
                ingest.ingest_ended = timezone.now()
                ingest.save()
                logger.debug('Checking ingest trigger rules')
                IngestTriggerHandler().process_ingested_source_file(ingest.source_file, ingest.ingest_ended)

            # Delete ingest file
            _delete_ingest_file(ingest_path)
            logger.info('Ingest successful: %s', ingest_path)
        except DuplicateFile:
            logger.warning('Duplicate file detected: %i', ingest_id, exc_info=True)
            ingest.status = 'DUPLICATE'
            ingest.save()
            _move_ingest_file(ingest_path, dup_path)
        except Exception:
            # TODO: have this delete the stored source file using some SourceFile.objects.delete_file method
            ingest.status = 'ERRORED'
            ingest.save()
            raise  # File remains where it is so it can be processed again
    finally:
        try:
            # Try to clean up the upload directory
            if upload_work_dir and os.path.exists(upload_work_dir):
                upload_dir = os.path.join(upload_work_dir, 'upload')
                workspace_work_dir = os.path.join(upload_work_dir, 'work')
                if os.path.exists(workspace_work_dir):
                    ScaleFile.objects.cleanup_upload_dir(upload_dir, workspace_work_dir, ingest.workspace)
                    logger.info('Deleting %s', workspace_work_dir)
                    os.rmdir(workspace_work_dir)
                if os.path.exists(upload_dir):
                    logger.info('Deleting %s', upload_dir)
                    # Delete everything in upload dir
                    shutil.rmtree(upload_dir)
                logger.info('Deleting %s', upload_work_dir)
                os.rmdir(upload_work_dir)
        except:
            # Swallow exception so error from main try block isn't covered up
            logger.exception('Failed to delete upload work dir %s', upload_work_dir)

    try:
        if job_exe_id:
            cleanup_job_exe(job_exe_id)
    except Exception:
        logger.exception('Job Execution %i: Error cleaning up', job_exe_id)


def _delete_ingest_file(ingest_path):
    '''Deletes the given ingest file

    :param ingest_path: The absolute path of the file to delete
    :type ingest_path: str
    '''
    if os.path.exists(ingest_path):
        logger.info('Deleting %s', ingest_path)
        os.remove(ingest_path)


def _move_ingest_file(ingest_path, dest_path):
    '''Moves the given ingest file to a new location

    :param ingest_path: The absolute path of the file to move
    :type ingest_path: str
    :param dest_path: The absolute path of the new location for the file
    :type dest_path: str
    '''
    if os.path.exists(ingest_path):
        dest_dir = os.path.dirname(dest_path)
        if not os.path.exists(dest_dir):
            logger.info('Creating %s', dest_dir)
            os.makedirs(dest_dir, mode=0755)
        logger.info('Moving %s to %s', ingest_path, dest_path)
        os.rename(ingest_path, dest_path)


def _set_ingesting_status(ingest, ingest_path, dup_path):
    '''Checks the condition of the ingest and if good, updates its status in the database to INGESTING and returns the
    model. If None is returned, then the ingest process should stop.

    :param ingest: The ingest model
    :type ingest: :class:`ingest.models.Ingest`
    :param ingest_path: The absolute path of the ingest file
    :type ingest_path: str
    :param dup_path: The absolute path of the duplicate ingest file
    :type dup_path: str
    :returns: The ingest model
    :rtype: :class:`ingest.models.Ingest`
    '''
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
