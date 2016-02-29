'''Defines methods and classes for handling network file systems'''
from __future__ import unicode_literals

import logging

from storage.exceptions import NfsError
from util.command import execute_command_line, CommandError


logger = logging.getLogger(__name__)


def nfs_mount(mount, mount_on, read_only=True):
    '''Performs a mount of a network file system

    :param mount: The network file system to mount in the form of host:/dir/path
    :type mount: str
    :param mount_on: The absolute directory path to mount on (must already exist)
    :type mount_on: str
    :param read_only: Whether the mount should be read-only
    :type read_only: bool
    '''

    logger.info('Mounting %s on %s', mount, mount_on)

    options = 'soft,' + ('ro' if read_only else 'rw') + ',lookupcache=positive'
    cmd_list = ['sudo', 'mount', '-o', options, mount, mount_on]
    try:
        execute_command_line(cmd_list)
    except Exception as ex:
        raise NfsError(ex)


def nfs_umount(mounted_on):
    '''Performs a umount of a network file system

    :param mounted_on: The absolute directory path of the mounted file system
    :type mounted_on: str
    '''

    logger.info('Unmounting %s', mounted_on)

    cmd_list = ['sudo', 'umount', '-lf', mounted_on]
    try:
        execute_command_line(cmd_list)
    except CommandError as ex:
        # Ignore location not mounted error
        if ex.returncode == 32 or (ex.returncode == 1 and "not mounted" in str(ex)):
            logger.info('%s was not mounted', mounted_on)
            return
        raise NfsError(ex)
    except Exception as ex:
        raise NfsError(ex)
