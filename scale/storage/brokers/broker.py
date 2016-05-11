"""Defines the base broker class"""
from abc import ABCMeta, abstractmethod
from collections import namedtuple


FileDownload = namedtuple('FileDownload', 'file local_path')
FileMove = namedtuple('FileMove', 'file new_path')
FileUpload = namedtuple('FileUpload', 'file local_path')


# TODO: delete this
class OldBroker(object):
    """Abstract class for a broker that can download and upload files for a given storage backend

    :keyword broker_type: The type of broker
    :type broker_type: str
    """

    __metaclass__ = ABCMeta

    # This must be unique for each subclass
    broker_type = None

    @abstractmethod
    def cleanup_download_dir(self, download_dir, work_dir):
        """Performs any cleanup necessary for a previous setup_download_dir() call

        :param download_dir: Absolute path to the local directory for the files to download
        :type download_dir: str
        :param work_dir: Absolute path to a local work directory available to the storage backend
        :type work_dir: str
        """

        pass

    @abstractmethod
    def cleanup_upload_dir(self, upload_dir, work_dir):
        """Performs any cleanup necessary for a previous setup_upload_dir() call

        :param upload_dir: Absolute path to the local directory of the files to upload
        :type upload_dir: str
        :param work_dir: Absolute path to a local work directory available to the storage backend
        :type work_dir: str
        """

        pass

    @abstractmethod
    def delete_files(self, work_dir, workspace_paths):
        """Deletes the workspace files with the given workspace paths. The work directory already exists.

        :param work_dir: Absolute path to a local work directory available to the storage backend
        :type work_dir: str
        :param workspace_paths: The relative workspace paths of the files to delete
        :type workspace_paths: list of str
        """

        pass

    @abstractmethod
    def download_files(self, download_dir, work_dir, files_to_download):
        """Downloads the given workspace files into the given download directory. This method assumes that
        setup_download_dir() has already been called with the same download and work directories.

        :param download_dir: Absolute path to the local directory for the files to download
        :type download_dir: str
        :param work_dir: Absolute path to a local work directory available to the storage backend
        :type work_dir: str
        :param files_to_download: List of tuples (workspace path of a file to download, destination path relative to
            download directory)
        :type files_to_download: list of (str, str)
        """

        pass

    @abstractmethod
    def is_config_valid(self, config):
        """Validates the given configuration. There is no return value; an invalid configuration should just raise an
        exception.

        :param config: The configuration as a dictionary
        :type config: dict
        """

        pass

    @abstractmethod
    def load_config(self, config):
        """Loads the given configuration

        :param config: The configuration as a dictionary
        :type config: dict
        """

        pass

    @abstractmethod
    def move_files(self, work_dir, files_to_move):
        """Moves the workspace files to the new workspace paths. The work directory already exists.

        :param work_dir: Absolute path to a local work directory available to the storage backend
        :type work_dir: str
        :param files_to_move: List of tuples (current workspace path of a file to move, new workspace path for the file)
        :type files_to_move: list of (str, str)
        """

        pass

    @abstractmethod
    def setup_download_dir(self, download_dir, work_dir):
        """Sets up the given download directory to download files from the workspace. The download directory and the
        work directory already exist.

        :param download_dir: Absolute path to the local directory for the files to download
        :type download_dir: str
        :param work_dir: Absolute path to a local work directory available to the storage backend
        :type work_dir: str
        """

        pass

    @abstractmethod
    def setup_upload_dir(self, upload_dir, work_dir):
        """Sets up the given upload directory to upload or delete files in the workspace. The upload directory and the
        work directory already exist.

        :param upload_dir: Absolute path to the local directory of the files to upload
        :type upload_dir: str
        :param work_dir: Absolute path to a local work directory available to the storage backend
        :type work_dir: str
        """

        pass

    @abstractmethod
    def upload_files(self, upload_dir, work_dir, files_to_upload):
        """Uploads the given files in the given upload directory into the workspace. This method assumes that
        setup_upload_dir() has already been called with the same upload and work directories.

        :param upload_dir: Absolute path to the local directory of the files to upload
        :type upload_dir: str
        :param work_dir: Absolute path to a local work directory available to the storage backend
        :type work_dir: str
        :param files_to_upload: List of tuples (source path relative to upload directory, workspace path for storing the
            file)
        :type files_to_upload: list of (str, str)
        """

        pass

    def _validate_str_config_field(self, name, config):
        """Validates that the given field name has a non-empty string value in given configuration. There is no return
        value; an invalid configuration should just raise an exception.

        :param name: The name of the field
        :type name: str
        :param config: The configuration as a dictionary
        :type config: dict
        """
        if not name in config:
            msg = u'%s is required for %s broker'
            raise Exception(msg % (name, self.broker_type))

        if not config[name] or not isinstance(config[name], basestring):
            msg = u'%s must have a non-empty string value for %s broker'
            raise Exception(msg % (name, self.broker_type))


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
        self._mount = None

    @property
    def broker_type(self):
        """The type of this broker

        :returns: The broker type
        :rtype: string
        """

        return self._broker_type

    @property
    def mount(self):
        """If this broker uses a mounted file system, this property returns the remote location that should be mounted
        into the task container. If this broker does not use a mounted file system, this property should be None.

        :returns: The remote file system location to mount, possibly None
        :rtype: string
        """

        return self._mount

    def delete_files(self, mount_location, files):
        """Deletes the given files.

        If this broker uses a mounted file system, mount_location will contain the absolute local container location
        where that remote file system is mounted. This means that the remote path to where a ScaleFile currently exists
        is the result of os.path.join(mount_location, files[i].file_path). If this broker does not use a mounted file
        system, None will be given for mount_location.

        The files list contains the ScaleFile models representing the files to be deleted. The broker should only delete
        each file itself and not any parent directories. No changes should be made to the ScaleFile models. Scale will
        mark the models as deleted in the database after the files have been successfully deleted.

        :param mount_location: Absolute path to the local container location onto which the remote file system was
            mounted, None if this broker does not use a mounted file system
        :type mount_location: string
        :param files: List of files to delete
        :type files: [:class:`storage.models.ScaleFile`]
        """

        pass

    def download_files(self, mount_location, file_downloads):
        """Downloads the given files to the given local file system paths.

        If this broker uses a mounted file system, mount_location will contain the absolute local container location
        where that remote file system is mounted. This means that the remote path to a ScaleFile that is accessible to
        the container is the result of os.path.join(mount_location, file_downloads[i].file.file_path). If this broker
        does not use a mounted file system, None will be given for mount_location.

        The file_downloads list contains named tuples that each contain a ScaleFile model to be downloaded and the
        absolute local container path where the file should be downloaded. No changes should be made to the ScaleFile
        models. Any directories in the absolute local container paths should already exist.

        :param mount_location: Absolute path to the local container location onto which the remote file system was
            mounted, None if this broker does not use a mounted file system
        :type mount_location: string
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

    def move_files(self, mount_location, file_moves):
        """Moves the given files to the new file system paths.

        If this broker uses a mounted file system, mount_location will contain the absolute local container location
        where that remote file system is mounted. This means that the remote path to where a ScaleFile currently exists
        is the result of os.path.join(mount_location, files_moves[i].file.file_path) and the new path is given by
        os.path.join(mount_location, files_moves[i].file.new_path). If this broker does not use a mounted file system,
        None will be given for mount_location.

        The file_moves list contains named tuples that each contain a ScaleFile model to be moved and the new relative
        file_path field for the new location of the file. The broker is expected to set the file_path field of each
        ScaleFile model to its new location (which the broker may alter) and is free to alter any additional fields as
        necessary. The broker should NOT perform a model save/update to the database. Scale will save/update the models
        in the database after they have all been successfully moved. The directories in the new file_path may not exist,
        so it is the responsibility of the broker to create them if necessary.

        :param mount_location: Absolute path to the local container location onto which the remote file system was
            mounted, None if this broker does not use a mounted file system
        :type mount_location: string
        :param file_moves: List of files to move
        :type file_moves: [:class:`storage.brokers.broker.FileMove`]
        """

        pass

    def upload_files(self, mount_location, file_uploads):
        """Uploads the given files from the given local file system paths.

        If this broker uses a mounted file system, mount_location will contain the absolute local container location
        where that remote file system is mounted. This means that the remote path to where a ScaleFile should be
        uploaded is the result of os.path.join(mount_location, file_uploads[i].file.file_path). If this broker does not
        use a mounted file system, None will be given for mount_location.

        The file_uploads list contains named tuples that each contain a ScaleFile model to be uploaded and the absolute
        local container path where the file currently exists. The broker is free to alter the ScaleFile fields of the
        uploaded files, including the final file_path (the given file_path is a recommendation by Scale that guarantees
        path uniqueness). The ScaleFile models may not have been saved to the database yet and so may not have their id
        field populated. The broker should NOT perform a model save/update to the database. Scale will save the models
        into the database after they have all been successfully uploaded. The directories in the remote file_path may
        not exist, so it is the responsibility of the broker to create them if necessary.

        :param mount_location: Absolute path to the local container location onto which the remote file system was
            mounted, None if this broker does not use a mounted file system
        :type mount_location: string
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
