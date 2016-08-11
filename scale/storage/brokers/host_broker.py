"""Defines a broker that mounts a local host directory into the task container as its backend storage"""
from __future__ import unicode_literals

import logging
import os
import shutil

from storage.brokers.broker import Broker, BrokerVolume
from storage.brokers.exceptions import InvalidBrokerConfiguration
from util.command import execute_command_line


logger = logging.getLogger(__name__)


class HostBroker(Broker):
    """Broker that utilizes a local host path mounted into the task container
    """

    def __init__(self):
        """Constructor
        """

        super(HostBroker, self).__init__('host')

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

        volume = BrokerVolume(None, config['host_path'])
        volume.host = True
        self._volume = volume

    def move_files(self, volume_path, file_moves):
        """See :meth:`storage.brokers.broker.Broker.move_files`
        """

        for file_move in file_moves:
            full_old_path = os.path.join(volume_path, file_move.file.file_path)
            full_new_path = os.path.join(volume_path, file_move.new_path)
            full_new_path_dir = os.path.dirname(full_new_path)

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
            shutil.copy(file_upload.local_path, path_to_upload)
            logger.info('Setting file permissions for %s', path_to_upload)
            os.chmod(path_to_upload, 0644)

            # Create new model
            file_upload.file.save()

    def validate_configuration(self, config):
        """See :meth:`storage.brokers.broker.Broker.validate_configuration`
        """

        if 'host_path' not in config or not config['host_path']:
            raise InvalidBrokerConfiguration('Host broker requires "host_path" to be populated')

        # TODO: include checks against obvious 'bad' host mounts such as '/'
        return []
