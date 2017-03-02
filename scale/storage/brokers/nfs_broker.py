"""Defines an NFS broker that utilizes a network file system as its backend storage"""
from __future__ import unicode_literals

import logging
import os
import shutil

from storage.brokers.broker import Broker, BrokerVolume
from storage.brokers.exceptions import InvalidBrokerConfiguration
from storage.exceptions import MissingFile
from util.command import execute_command_line

logger = logging.getLogger(__name__)


class NfsBroker(Broker):
    """Broker that utilizes the docker-volume-netshare plugin (https://github.com/gondor/docker-volume-netshare) to
    mount an NFS volume into the task container
    """

    def __init__(self):
        """Constructor
        """

        super(NfsBroker, self).__init__('nfs')

    def delete_files(self, volume_path, files):
        """See :meth:`storage.brokers.broker.Broker.delete_files`
        """

        for scale_file in files:
            path_to_delete = os.path.join(volume_path, scale_file.file_path)
            if os.path.exists(path_to_delete):
                logger.info('Deleting %s', path_to_delete)
                os.remove(path_to_delete)

                # Update model attributes
                scale_file.set_deleted()
                scale_file.save()

    def download_files(self, volume_path, file_downloads):
        """See :meth:`storage.brokers.broker.Broker.download_files`
        """

        for file_download in file_downloads:
            path_to_download = os.path.join(volume_path, file_download.file.file_path)

            logger.info('Checking path %s', path_to_download)
            if not os.path.exists(path_to_download):
                raise MissingFile(file_download.file.file_name)

            # Create symlink to the file in the host mount
            logger.info('Creating link %s -> %s', file_download.local_path, path_to_download)
            execute_command_line(['ln', '-s', path_to_download, file_download.local_path])

    def get_file_system_paths(self, volume_path, files):
        """See :meth:`storage.brokers.broker.Broker.get_file_system_paths`
        """

        paths = []
        for scale_file in files:
            paths.append(os.path.join(volume_path, scale_file.file_path))
        return paths

    def load_configuration(self, config):
        """See :meth:`storage.brokers.broker.Broker.load_configuration`
        """

        # The docker-volume-netshare plugin requires the : separator between the NFS host and path to be removed
        self._volume = BrokerVolume('nfs', config['nfs_path'].replace(':', ''))

    def move_files(self, volume_path, file_moves):
        """See :meth:`storage.brokers.broker.Broker.move_files`
        """

        for file_move in file_moves:
            full_old_path = os.path.join(volume_path, file_move.file.file_path)
            full_new_path = os.path.join(volume_path, file_move.new_path)
            full_new_path_dir = os.path.dirname(full_new_path)

            logger.info('Checking path %s', full_old_path)
            if not os.path.exists(full_old_path):
                raise MissingFile(file_move.file.file_name)

            if not os.path.exists(full_new_path_dir):
                logger.info('Creating %s', full_new_path_dir)
                os.makedirs(full_new_path_dir, mode=0755)

            logger.info('Moving %s to %s', full_old_path, full_new_path)
            shutil.move(full_old_path, full_new_path)
            logger.info('Setting file permissions for %s', full_new_path)
            os.chmod(full_new_path, 0644)

            # Update model attributes
            file_move.file.file_path = file_move.new_path
            file_move.file.save()

    def upload_files(self, volume_path, file_uploads):
        """See :meth:`storage.brokers.broker.Broker.upload_files`
        """

        for file_upload in file_uploads:
            path_to_upload = os.path.join(volume_path, file_upload.file.file_path)
            path_to_upload_dir = os.path.dirname(path_to_upload)

            if not os.path.exists(path_to_upload_dir):
                logger.info('Creating %s', path_to_upload_dir)
                os.makedirs(path_to_upload_dir, mode=0755)

            logger.info('Copying %s to %s', file_upload.local_path, path_to_upload)
            self._copy_file(file_upload.local_path, path_to_upload)
            logger.info('Setting file permissions for %s', path_to_upload)
            os.chmod(path_to_upload, 0644)

            # Create new model
            file_upload.file.save()

    def validate_configuration(self, config):
        """See :meth:`storage.brokers.broker.Broker.validate_configuration`
        """

        if 'nfs_path' not in config or not config['nfs_path']:
            raise InvalidBrokerConfiguration('NFS broker requires "nfs_path" to be populated')
        return []

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
        # Attempt bbcp copy first. If it fails, we'll fallback to cp
        try:
            # TODO: detect bbcp location instead of assuming /usr/local and don't even try to execute if it isn't
            # installed
            # TODO: configuration options for the bbcp copy options such as window size
            srv_src_path, srv_dest_path = self._get_mount_info(src_path, dest_path)
            cmd_list = ['/usr/local/bin/bbcp',
                        '-s', '8', '-w', '64M', '-E', 'md5', '-o', '-y', 'd',
                        apply(os.path.join, srv_src_path) if srv_src_path[0] is not None else srv_src_path[1],
                        apply(os.path.join, srv_dest_path) if srv_dest_path[0] is not None else srv_dest_path[1]]
            execute_command_line(cmd_list)
            return
        except OSError as e:
            # errno 2 is No such file or directory..bbcp not installed. We'll be quiet about it but fallback
            if e.errno != 2:
                logger.exception("NFS Broker bbcp copy_file")  # Ignore the error and attempt a regular cp
        except:
            logger.exception("NFS Broker bbcp copy_file")  # Ignore the error and attempt a regular cp
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
                # The indices will be present for nfs and nfs4 entries so if we don't have all the items, we can ignore
                pass
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
