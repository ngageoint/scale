"""Defines the functions necessary to delete a file from a workspace"""
from __future__ import unicode_literals

import logging
import os
import sys


logger = logging.getLogger(__name__)


def destroy_file(file_path, job_id):
    """Deletes the given file within a workspace.

    :param file_path: The absolute path of the file to delete
    :type file_path: string
    :param job_id: The ID of the job associated with the file
    :type job_id: int
    """

    if os.path.exists(file_path):
        logger.info('Deleting %s', file_path)
        try:
            os.remove(file_path)
        except:
            logger.exception('There was an error when trying to delete %s', file_path)
            sys.exit(10)
    else:
        logger.error('No file exists at %s', file_path)
        sys.exit(20)

    logger.info('The file located at %s was deleted for job %i', file_path, job_id)
    sys.exit(0)
