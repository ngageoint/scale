"""Defines the functions necessary to delete a file from a workspace"""
from __future__ import unicode_literals

import logging
import os
import sys

from error.exceptions import ScaleError, get_error_by_exception


logger = logging.getLogger(__name__)


GENERAL_FAIL_EXIT_CODE = 1


def delete_files(files, volume_path, broker):
    """Deletes the given files within a workspace.

    :param files: List of named tuples containing path and ID of the file to delete.
    :type files: [collections.namedtuple]
    :param volume_path: Absolute path to the local container location onto which the volume file system was mounted,
            None if this broker does not use a container volume
    :type volume_path: string
    :param broker: The storage broker
    :type broker: `storage.brokers.broker.Broker`
    """

    logger.info('Deleting %i files', len(files))
    try:
        broker.delete_files(volume_path=volume_path, files=files, update_model=False)
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
            logger.exception('Error performing delete_files steps')
        sys.exit(exit_code)

    return
