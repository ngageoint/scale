"""Defines the functions necessary to delete a file from a workspace"""
from __future__ import unicode_literals

import logging
import os
import sys


logger = logging.getLogger(__name__)


def destroy_files(files, job_id, volume_path, broker):
    """Deletes the given files within a workspace.

    :param files: List of named tuples containing path and ID of the file to delete.
    :type files: [collections.namedtuple]
    :param job_id: The ID of the job associated with the file
    :type job_id: int
    :param volume_path: Absolute path to the local container location onto which the volume file system was mounted,
            None if this broker does not use a container volume
    :type volume_path: string
    :param workspace: The storage broker
    :type workspace: `storage.brokers.broker.Broker`
    """

    logger.info('Deleting %i files', len(files))
    try:
        broker.delete_files(volume_path=volume_path, files=files, update_model=False)
    except:
        logger.exception('There was an error when trying to delete files for job %i', job_id)
        return 10

    logger.info('A file associated with job %i was deleted', job_id)
    return 0
