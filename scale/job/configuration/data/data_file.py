"""Defines the data file inputs and data file outputs that are contained within job data"""
from abc import ABCMeta


# The data file parse saver must be registered here
# The data file parse saver can be registered from another app during its ready() method
DATA_FILE_PARSE_SAVER = {u'DATA_FILE_PARSE_SAVER': None}


# The data file store must be registered here
# The data file store can be registered from another app during its ready() method
DATA_FILE_STORE = {u'DATA_FILE_STORE': None}


class AbstractDataFileParseSaver(object):
    """Abstract base class for a data file parse saver. A data file parse saver provides a way to save parse results for
    input data files.
    """

    __metaclass__ = ABCMeta

    def save_parse_results(self, parse_results, input_file_ids):
        """Saves the given parse results

        :param parse_results: Dict with each input file name mapping to a tuple of GeoJSON containing GIS meta-data
            (optionally None), the start time of the data contained in the file (optionally None), the end time of the
            data contained in the file (optionally None), the list of data types, and the new workspace path (optionally
            None)
        :type parse_results: dict of str -> tuple(str, :class:`datetime.datetime`, :class:`datetime.datetime`, list,
            str, str)
        :param input_file_ids: List of IDs for all input files
        :type input_file_ids: list of long
        """

        raise NotImplementedError()


class AbstractDataFileStore(object):
    """Abstract base class for a data file store. A data file store provides a way to validate data file output
    configuration and store output data files.
    """

    __metaclass__ = ABCMeta

    def get_workspaces(self, workspace_ids):
        """Retrieves the workspaces with the given IDs. If no workspace has a given ID, it will not be retrieved.

        :param workspace_ids: The set of workspace IDs
        :type workspace_ids: set of int
        :returns: Dict with each workspace ID mapping to a bool indicating if it is active (True)
        :rtype: dict of int -> bool
        """

        raise NotImplementedError()

    def store_files(self, data_files, input_file_ids, job_exe):
        """Stores the given data files and writes them to the given workspaces.

        :param data_files: Dict with workspace ID mapping to a list of tuples with absolute local file paths and media
            type (media type is optionally None)
        :type data_files: dict of int -> list of tuple(str, str)
        :param input_file_ids: Set of input file IDs
        :type input_file_ids: set of long
        :param job_exe: The job execution model (with related job and job_type fields) that is storing the files
        :type job_exe: :class:`job.models.JobExecution`
        :returns: Dict with each local file path mapping to its new file ID
        :rtype: dict of str -> long
        """

        raise NotImplementedError()
