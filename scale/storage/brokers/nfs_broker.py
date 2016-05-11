"""Defines an NFS broker that utilizes a network file system as its backend storage"""
from __future__ import unicode_literals

import logging
import os
import shutil

from storage.brokers.broker import OldBroker
from storage.nfs import nfs_umount, nfs_mount
from util.command import execute_command_line


logger = logging.getLogger(__name__)


class NfsBroker(OldBroker):
    """Broker that utilizes the NFS (Network File System) protocol
    """

    broker_type = 'nfs'

    def __init__(self):
        """Constructor
        """

        self.mount = None

    def cleanup_download_dir(self, download_dir, work_dir):
        """See :meth:`storage.brokers.broker.Broker.cleanup_download_dir`
        """

        nfs_umount(work_dir)

    def cleanup_upload_dir(self, upload_dir, work_dir):
        """See :meth:`storage.brokers.broker.Broker.cleanup_upload_dir`
        """

        nfs_umount(work_dir)

    def delete_files(self, work_dir, workspace_paths):
        """See :meth:`storage.brokers.broker.Broker.delete_files`
        """

        nfs_mount(self.mount, work_dir, False)
        try:
            for workspace_path in workspace_paths:
                path_to_delete = os.path.join(work_dir, workspace_path)
                if os.path.exists(path_to_delete):
                    logger.info('Deleting %s', path_to_delete)
                    os.remove(path_to_delete)
        finally:
            nfs_umount(work_dir)

    def download_files(self, download_dir, work_dir, files_to_download):
        """See :meth:`storage.brokers.broker.Broker.download_files`
        """

        for file_to_download in files_to_download:
            workspace_path = file_to_download[0]
            dest_path = file_to_download[1]

            full_workspace_path = os.path.join(work_dir, workspace_path)
            full_dest_path = os.path.join(download_dir, dest_path)
            full_dest_dir = os.path.dirname(full_dest_path)

            if not os.path.exists(full_dest_dir):
                logger.info('Creating %s', full_dest_dir)
                os.makedirs(full_dest_dir, mode=0755)
            execute_command_line(['ln', '-s', full_workspace_path, full_dest_path])

    def is_config_valid(self, config):
        """Validates the given configuration. There is no return value; an invalid configuration should just raise an
        exception.

        :param config: The configuration as a dictionary
        :type config: dict
        """

        if not config['type'] == self.broker_type:
            raise Exception('Invalid broker type: %s' % config['type'])

        self._validate_str_config_field('mount', config)

    def load_config(self, config):
        """Loads the given configuration

        :param config: The configuration as a dictionary
        :type config: dict
        """

        self.mount = config['mount']

    def move_files(self, work_dir, files_to_move):
        """See :meth:`storage.brokers.broker.Broker.move_files`
        """

        nfs_mount(self.mount, work_dir, False)
        try:
            for file_to_move in files_to_move:
                old_workspace_path = file_to_move[0]
                new_workspace_path = file_to_move[1]

                full_old_workspace_path = os.path.join(work_dir, old_workspace_path)
                full_new_workspace_path = os.path.join(work_dir, new_workspace_path)
                full_new_workspace_dir = os.path.dirname(full_new_workspace_path)

                if not os.path.exists(full_new_workspace_dir):
                    logger.info('Creating %s', full_new_workspace_dir)
                    os.makedirs(full_new_workspace_dir, mode=0755)

                logger.info('Moving %s to %s', full_old_workspace_path, full_new_workspace_path)
                shutil.move(full_old_workspace_path, full_new_workspace_path)
                os.chmod(full_new_workspace_path, 0644)
        finally:
            nfs_umount(work_dir)

    def setup_download_dir(self, download_dir, work_dir):
        """See :meth:`storage.brokers.broker.Broker.setup_download_dir`
        """

        nfs_mount(self.mount, work_dir, True)

    def setup_upload_dir(self, upload_dir, work_dir):
        """See :meth:`storage.brokers.broker.Broker.setup_upload_dir`
        """

        pass

    def upload_files(self, upload_dir, work_dir, files_to_upload):
        """See :meth:`storage.brokers.broker.Broker.setup_upload_dir`
        """

        nfs_mount(self.mount, work_dir, False)
        try:
            for file_to_upload in files_to_upload:
                src_path = file_to_upload[0]
                workspace_path = file_to_upload[1]

                full_src_path = os.path.join(upload_dir, src_path)
                full_workspace_path = os.path.join(work_dir, workspace_path)
                full_workspace_dir = os.path.dirname(full_workspace_path)

                if not os.path.exists(full_workspace_dir):
                    logger.info('Creating %s', full_workspace_dir)
                    os.makedirs(full_workspace_dir, mode=0755)
                self._copy_file(full_src_path, full_workspace_path)
                os.chmod(full_workspace_path, 0644)
        finally:
            nfs_umount(work_dir)

    def _copy_file(self, src_path, dest_path):
        """Performs a copy from the src_path to the dest_path

        :param src_path: The absolute path to the source file
        :type src_path: str
        :param dest_path: The absolute path to the destination
        :type dest_path: str
        """

        if os.path.islink(src_path):
            real_path = os.path.realpath(src_path)
            logger.info('%s is a link to %s', src_path, real_path)
            src_path = real_path
        logger.info('Copying %s to %s', src_path, dest_path)
        # attempt bbcp copy first. If it fails, we'll fallback to cp
        try:
            # TODO: detect bbcp location instead of assuming /usr/local and don't even try to execute if it isn't installed
            # TODO: configuration options for the bbcp copy options such as window size
            srv_src_path, srv_dest_path = self._get_mount_info(src_path, dest_path)
            cmd_list = ['/usr/local/bin/bbcp',
                        '-s', '8', '-w', '64M', '-E', 'md5', '-o', '-y', 'd',
                        apply(os.path.join, srv_src_path) if srv_src_path[0] is not None else srv_src_path[1],
                        apply(os.path.join, srv_dest_path) if srv_dest_path[0] is not None else srv_dest_path[1]]
            execute_command_line(cmd_list)
            return
        except OSError, e:
            if e.errno != 2: # errno 2 is No such file or directory..bbcp not installed. We'll be quiet about it but fallback
                logger.exception("NFS Broker bbcp copy_file") # ignore the error and attempt a regular cp
        except:
            logger.exception("NFS Broker bbcp copy_file") # ignore the error and attempt a regular cp
        logger.info('Fall back to cp for %s', src_path)
        shutil.copy(src_path, dest_path)

    def _get_mount_info(self, *args):
        """Determine what filesystem contains a path and if it's an nfs filesystem return the mount spec and server.

        :param args: The path(s) to query.
        :type args: str
        :return: A tuple with ('server:/path/on/server', 'residual path') or (None, 'full path') per argument.
                 The resulting tuple can be passed to os.path.join (i.e. apply(os.path.join, rval))
        :rtype: list of tuple
        """

        # create a list of nfs mounts from proc/mountinfo
        mnt_table = []
        for l in open('/proc/%d/mountinfo' % os.getpid(), 'rt').readlines():
            try:
                l = l.strip().split()
                mntpnt = l[4]
                while l[0] != '-':
                    l.pop(0)
                    l.pop(0)
                    typ = l.pop(0)
                    if typ.startswith('nfs'):
                        srv = l[0]
                        mnt_table.append((mntpnt, srv))
            except IndexError:
                pass # the indices will be present for nfs and nfs4 entries so if we don't have all the items, we can ignore
        # sort by length of mount point. Longest mount points (number of nested directories) are first in case we have
        # items mounted within an nfs mount tree
        mnt_table.sort(cmp=lambda a, b: cmp(len(a[0].split(os.sep)), len(b[0].split(os.sep))), reverse=True)

        rval = []
        for pth in args:
            # make sure we have an absolute path when checking mount points
            pth = os.path.abspath(pth)

            # find the first matching mount point and return its info
            found = False
            for mntpnt, srv in mnt_table:
                if os.path.commonprefix([mntpnt, pth]) == mntpnt:
                    pth = os.path.relpath(pth, mntpnt)
                    rval.append((srv, pth))
                    found = True
                    break
            if not found:
                rval.append((None, pth))
        return rval
