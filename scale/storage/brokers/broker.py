"""Defines the base broker class"""
from abc import ABCMeta
from collections import namedtuple


FileDownload = namedtuple('FileDownload', 'file local_path')
FileMove = namedtuple('FileMove', 'file new_path')
FileUpload = namedtuple('FileUpload', 'file local_path')


class Broker(object):
    """Abstract class for a broker that can download and upload files for a given storage backend
    """

    __metaclass__ = ABCMeta

    def __init__(self, broker_type):
        """Constructor

        :param broker_type: The type of this broker
        :type broker_type: string
        """

        self._broker_type = broker_type
        self._volume = None

    @property
    def broker_type(self):
        """The type of this broker

        :returns: The broker type
        :rtype: string
        """

        return self._broker_type

    @property
    def volume(self):
        """If this broker uses a container volume, this property returns the information needed to set up a volume that
        can be mounted into the task container. If this broker does not use a container volume, this property should be
        None.

        :returns: The container volume information needed for this broker, possibly None
        :rtype: :class:`storage.brokers.broker.BrokerVolume`
        """

        return self._volume

    def delete_files(self, volume_path, files):
        """Deletes the given files.

        If this broker uses a container volume, volume_path will contain the absolute local container location where
        that volume file system is mounted. This means that the remote path to where a ScaleFile currently exists is the
        result of os.path.join(volume_path, files[i].file_path). If this broker does not use a container volume, None
        will be given for volume_path.

        The files list contains the ScaleFile models representing the files to be deleted. The broker should only delete
        each file itself and not any parent directories. No changes should be made to the ScaleFile models. Scale will
        mark the models as deleted in the database after the files have been successfully deleted.

        :param volume_path: Absolute path to the local container location onto which the volume file system was mounted,
            None if this broker does not use a container volume
        :type volume_path: string
        :param files: List of files to delete
        :type files: [:class:`storage.models.ScaleFile`]
        """

        pass

    def download_files(self, volume_path, file_downloads):
        """Downloads the given files to the given local file system paths.

        If this broker uses a container volume, volume_path will contain the absolute local container location where
        that volume file system is mounted. This means that the remote path to a ScaleFile that is accessible to the
        container is the result of os.path.join(volume_path, file_downloads[i].file.file_path). If this broker does not
        use a container volume, None will be given for volume_path.

        The file_downloads list contains named tuples that each contain a ScaleFile model to be downloaded and the
        absolute local container path where the file should be downloaded. No changes should be made to the ScaleFile
        models. Any directories in the absolute local container paths should already exist.

        :param volume_path: Absolute path to the local container location onto which the volume file system was mounted,
            None if this broker does not use a container volume
        :type volume_path: string
        :param file_downloads: List of files to download
        :type file_downloads: [:class:`storage.brokers.broker.FileDownload`]
        """

        pass

    def load_configuration(self, config):
        """Loads the given configuration

        :param config: The configuration as a dictionary
        :type config: dict
        """

        pass

    def move_files(self, volume_path, file_moves):
        """Moves the given files to the new file system paths.

        If this broker uses a container volume, volume_path will contain the absolute local container location where
        that volume file system is mounted. This means that the remote path to where a ScaleFile currently exists is the
        result of os.path.join(volume_path, files_moves[i].file.file_path) and the new path is given by
        os.path.join(volume_path, files_moves[i].file.new_path). If this broker does not use a container volume, None
        will be given for volume_path.

        The file_moves list contains named tuples that each contain a ScaleFile model to be moved and the new relative
        file_path field for the new location of the file. The broker is expected to set the file_path field of each
        ScaleFile model to its new location (which the broker may alter) and is free to alter any additional fields as
        necessary. The broker should NOT perform a model save/update to the database. Scale will save/update the models
        in the database after they have all been successfully moved. The directories in the new file_path may not exist,
        so it is the responsibility of the broker to create them if necessary.

        :param volume_path: Absolute path to the local container location onto which the volume file system was mounted,
            None if this broker does not use a container volume
        :type volume_path: string
        :param file_moves: List of files to move
        :type file_moves: [:class:`storage.brokers.broker.FileMove`]
        """

        pass

    def upload_files(self, volume_path, file_uploads):
        """Uploads the given files from the given local file system paths.

        If this broker uses a container volume, volume_path will contain the absolute local container location where
        that volume file system is mounted. This means that the remote path to where a ScaleFile should be uploaded is
        the result of os.path.join(volume_path, file_uploads[i].file.file_path). If this broker does not use a container
        volume, None will be given for volume_path.

        The file_uploads list contains named tuples that each contain a ScaleFile model to be uploaded and the absolute
        local container path where the file currently exists. The broker is free to alter the ScaleFile fields of the
        uploaded files, including the final file_path (the given file_path is a recommendation by Scale that guarantees
        path uniqueness). The ScaleFile models may not have been saved to the database yet and so may not have their id
        field populated. The broker should NOT perform a model save/update to the database. Scale will save the models
        into the database after they have all been successfully uploaded. The directories in the remote file_path may
        not exist, so it is the responsibility of the broker to create them if necessary.

        :param volume_path: Absolute path to the local container location onto which the volume file system was mounted,
            None if this broker does not use a container volume
        :type volume_path: string
        :param file_uploads: List of files to upload
        :type file_uploads: [:class:`storage.brokers.broker.FileUpload`]
        """

        pass

    def validate_configuration(self, config):
        """Validates the given configuration

        :param config: The configuration as a dictionary
        :type config: dict
        :raises :class:`storage.brokers.exceptions.InvalidBrokerConfiguration`: If the given configuration is invalid
        """

        pass


class BrokerVolume(object):
    """Represents the properties of a container volume that must be mounted into the container for a broker to work
    """

    def __init__(self, driver, remote_path):
        """Constructor

        :param driver: The driver used by the volume, None indicates that the default volume driver should be used
        :type driver: string
        :param remote_path: The remote path for the storage backend to which the container volume is connecting
        :type remote_path: string
        """

        self.driver = driver
        self.remote_path = remote_path

        # Special flag to indicate a host mount, which has different behavior
        self.host = False
