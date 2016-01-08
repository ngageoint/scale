'''Defines the base broker class'''
from abc import ABCMeta, abstractmethod


class Broker(object):
    '''Abstract class for a broker that can download and upload files for a given storage backend

    :keyword broker_type: The type of broker
    :type broker_type: str
    '''

    __metaclass__ = ABCMeta

    # This must be unique for each subclass
    broker_type = None

    @abstractmethod
    def cleanup_download_dir(self, download_dir, work_dir):
        '''Performs any cleanup necessary for a previous setup_download_dir() call

        :param download_dir: Absolute path to the local directory for the files to download
        :type download_dir: str
        :param work_dir: Absolute path to a local work directory available to the storage backend
        :type work_dir: str
        '''

        pass

    @abstractmethod
    def cleanup_upload_dir(self, upload_dir, work_dir):
        '''Performs any cleanup necessary for a previous setup_upload_dir() call

        :param upload_dir: Absolute path to the local directory of the files to upload
        :type upload_dir: str
        :param work_dir: Absolute path to a local work directory available to the storage backend
        :type work_dir: str
        '''

        pass

    @abstractmethod
    def delete_files(self, work_dir, workspace_paths):
        '''Deletes the workspace files with the given workspace paths. The work directory already exists.

        :param work_dir: Absolute path to a local work directory available to the storage backend
        :type work_dir: str
        :param workspace_paths: The relative workspace paths of the files to delete
        :type workspace_paths: list of str
        '''

        pass

    @abstractmethod
    def download_files(self, download_dir, work_dir, files_to_download):
        '''Downloads the given workspace files into the given download directory. This method assumes that
        setup_download_dir() has already been called with the same download and work directories.

        :param download_dir: Absolute path to the local directory for the files to download
        :type download_dir: str
        :param work_dir: Absolute path to a local work directory available to the storage backend
        :type work_dir: str
        :param files_to_download: List of tuples (workspace path of a file to download, destination path relative to
            download directory)
        :type files_to_download: list of (str, str)
        '''

        pass

    @abstractmethod
    def is_config_valid(self, config):
        '''Validates the given configuration. There is no return value; an invalid configuration should just raise an
        exception.

        :param config: The configuration as a dictionary
        :type config: dict
        '''

        pass

    @abstractmethod
    def load_config(self, config):
        '''Loads the given configuration

        :param config: The configuration as a dictionary
        :type config: dict
        '''

        pass

    @abstractmethod
    def move_files(self, work_dir, files_to_move):
        '''Moves the workspace files to the new workspace paths. The work directory already exists.

        :param work_dir: Absolute path to a local work directory available to the storage backend
        :type work_dir: str
        :param files_to_move: List of tuples (current workspace path of a file to move, new workspace path for the file)
        :type files_to_move: list of (str, str)
        '''

        pass

    @abstractmethod
    def setup_download_dir(self, download_dir, work_dir):
        '''Sets up the given download directory to download files from the workspace. The download directory and the
        work directory already exist.

        :param download_dir: Absolute path to the local directory for the files to download
        :type download_dir: str
        :param work_dir: Absolute path to a local work directory available to the storage backend
        :type work_dir: str
        '''

        pass

    @abstractmethod
    def setup_upload_dir(self, upload_dir, work_dir):
        '''Sets up the given upload directory to upload or delete files in the workspace. The upload directory and the
        work directory already exist.

        :param upload_dir: Absolute path to the local directory of the files to upload
        :type upload_dir: str
        :param work_dir: Absolute path to a local work directory available to the storage backend
        :type work_dir: str
        '''

        pass

    @abstractmethod
    def upload_files(self, upload_dir, work_dir, files_to_upload):
        '''Uploads the given files in the given upload directory into the workspace. This method assumes that
        setup_upload_dir() has already been called with the same upload and work directories.

        :param upload_dir: Absolute path to the local directory of the files to upload
        :type upload_dir: str
        :param work_dir: Absolute path to a local work directory available to the storage backend
        :type work_dir: str
        :param files_to_upload: List of tuples (source path relative to upload directory, workspace path for storing the
            file)
        :type files_to_upload: list of (str, str)
        '''

        pass

    def _validate_str_config_field(self, name, config):
        '''Validates that the given field name has a non-empty string value in given configuration. There is no return
        value; an invalid configuration should just raise an exception.

        :param name: The name of the field
        :type name: str
        :param config: The configuration as a dictionary
        :type config: dict
        '''
        if not name in config:
            msg = u'%s is required for %s broker'
            raise Exception(msg % (name, self.broker_type))

        if not config[name] or not isinstance(config[name], basestring):
            msg = u'%s must have a non-empty string value for %s broker'
            raise Exception(msg % (name, self.broker_type))
