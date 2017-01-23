"""Defines the base broker class"""
from abc import ABCMeta
from collections import namedtuple


"""
FileDownload tuple contains an additional partial flag for defining whether the file
is allowed to be accessed directly or must be copied into running container. This is
currently only applicable to the S3Broker and requires that the host_path also be defined
on the input workspace.
"""
FileDownload = namedtuple('FileDownload', ['file', 'local_path', 'partial'])
FileMove = namedtuple('FileMove', ['file', 'new_path'])
FileUpload = namedtuple('FileUpload', ['file', 'local_path'])


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
        that volume file system is mounted. This means that the path to where a ScaleFile currently exists is the result
        of os.path.join(volume_path, files[i].file_path). If this broker does not use a container volume, None will be
        given for volume_path.

        The files list contains the ScaleFile models representing the files to be deleted. The broker should only delete
        each file itself and not any parent directories. Each file model should be updated and saved when a delete is
        successful, including fields such as is_deleted and deleted.

        :param volume_path: Absolute path to the local container location onto which the volume file system was mounted,
            None if this broker does not use a container volume
        :type volume_path: string
        :param files: List of files to delete
        :type files: [:class:`storage.models.ScaleFile`]
        """

        raise NotImplementedError

    def list_files(self, volume_path, recursive):
        """List the files under the given file system paths.

        If this broker uses a container volume, volume_path will contain the absolute local container location where
        that volume file system is mounted. If this broker does not use a container volume, None will be given for
        volume_path.

        The expression must be a valid regular expression that accommodates matching against the complete file path. If
        the file is not at the root level relative to volume_path, due to recursive processing, the path will
        potentially include a directory and solidus separator.

        :param volume_path: Absolute path to the local container location onto which the volume file system was mounted,
            None if this broker does not use a container volume
        :type volume_path: string
        :param expression: Regular expression for file name and path filtering
        :type expression: string
        :param recursive: Flag to indicate whether file searching should be done recursively
        :type recursive: boolean
        :returns: List of files matching given expression
        :rtype: [:class:`storage.models.ScaleFile`]
        """

        raise NotImplementedError

    def download_files(self, volume_path, file_downloads):
        """Downloads the given files to the given local file system paths.

        If this broker uses a container volume, volume_path will contain the absolute local container location where
        that volume file system is mounted. This means that the path to a ScaleFile that is accessible to the container
        is the result of os.path.join(volume_path, file_downloads[i].file.file_path). If this broker does not use a
        container volume, None will be given for volume_path.

        The file_downloads list contains named tuples that each contain a ScaleFile model to be downloaded and the
        absolute local container path where the file should be downloaded. Typically, no changes are needed to file
        models during a download, but any changes should be saved by the broker. Any directories in the absolute local
        container paths should already exist.

        If a file does not exist in its expected location, raise a MissingFile exception.

        :param volume_path: Absolute path to the local container location onto which the volume file system was mounted,
            None if this broker does not use a container volume
        :type volume_path: string
        :param file_downloads: List of files to download
        :type file_downloads: [:class:`storage.brokers.broker.FileDownload`]

        :raises :class:`storage.exceptions.MissingFile`: If a file to download does not exist at the expected path
        """

        raise NotImplementedError

    def get_file_system_paths(self, volume_path, files):
        """Returns the local file system paths for the given files, if supported by the broker.

        If this broker uses a container volume, volume_path will contain the absolute local container location where
        that volume file system is mounted. This means that the path to a ScaleFile that is accessible to the container
        is the result of os.path.join(volume_path, scale_files[i].file_path). If this broker does not use a container
        volume, None will be given for volume_path. If this method is not supported by the broker, None will be
        returned.

        :param volume_path: Absolute path to the local container location onto which the volume file system was mounted,
            None if this broker does not use a container volume
        :type volume_path: string
        :param files: List of files
        :type files: [:class:`storage.models.ScaleFile`]
        :returns: The list of local file system paths if supported, None otherwise
        :rtype: [string]
        """

        return None

    def load_configuration(self, config):
        """Loads the given configuration

        :param config: The configuration as a dictionary
        :type config: dict
        """

        raise NotImplementedError

    def move_files(self, volume_path, file_moves):
        """Moves the given files to the new file system paths.

        If this broker uses a container volume, volume_path will contain the absolute local container location where
        that volume file system is mounted. This means that the path to where a ScaleFile currently exists is the result
        of os.path.join(volume_path, files_moves[i].file.file_path) and the new path is given by
        os.path.join(volume_path, files_moves[i].file.new_path). If this broker does not use a container volume, None
        will be given for volume_path.

        The file_moves list contains named tuples that each contain a ScaleFile model to be moved and the new relative
        file_path field for the new location of the file. The broker is expected to set the file_path field of each
        ScaleFile model to its new location (which the broker may alter) and is free to alter any additional fields as
        necessary. The broker is responsible for saving any changes to models when a move is successful The directories
        in the new file_path may not exist, so it is the responsibility of the broker to create them if necessary.

        If a file does not exist in its expected location, raise a MissingFile exception.

        :param volume_path: Absolute path to the local container location onto which the volume file system was mounted,
            None if this broker does not use a container volume
        :type volume_path: string
        :param file_moves: List of files to move
        :type file_moves: [:class:`storage.brokers.broker.FileMove`]

        :raises :class:`storage.exceptions.MissingFile`: If a file to move does not exist at the expected path
        """

        raise NotImplementedError

    def upload_files(self, volume_path, file_uploads):
        """Uploads the given files from the given local file system paths.

        If this broker uses a container volume, volume_path will contain the absolute local container location where
        that volume file system is mounted. This means that the path to where a ScaleFile should be uploaded is the
        result of os.path.join(volume_path, file_uploads[i].file.file_path). If this broker does not use a container
        volume, None will be given for volume_path.

        The file_uploads list contains named tuples that each contain a ScaleFile model to be uploaded and the absolute
        local container path where the file currently exists. The broker is free to alter the ScaleFile fields of the
        uploaded files, including the final file_path (the given file_path is a recommendation by Scale that guarantees
        path uniqueness). The ScaleFile models may not have been saved to the database yet and so may not have their id
        field populated. The broker should perform a model save/update to the database for any files that are
        successfully uploaded. The directories in the remote file_path may not exist, so it is the responsibility of the
        broker to create them if necessary.

        :param volume_path: Absolute path to the local container location onto which the volume file system was mounted,
            None if this broker does not use a container volume
        :type volume_path: string
        :param file_uploads: List of files to upload
        :type file_uploads: [:class:`storage.brokers.broker.FileUpload`]
        """

        raise NotImplementedError

    def validate_configuration(self, config):
        """Validates the given configuration

        :param config: The configuration as a dictionary
        :type config: dict
        :returns: A list of warnings discovered during validation.
        :rtype: [:class:`storage.configuration.workspace_configuration.ValidationWarning`]

        :raises :class:`storage.brokers.exceptions.InvalidBrokerConfiguration`: If the given configuration is invalid
        """

        raise NotImplementedError


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
