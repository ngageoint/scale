import glob
from abc import ABCMeta

import os

from job.configuration.results.exceptions import OutputCaptureError
from job.execution.container import SCALE_JOB_EXE_OUTPUT_PATH


class SeedFiles(object):
    __metaclass__ = ABCMeta

    def __init__(self, data):
        """Create a SeedFiles from dict input equivalent

        :param data:
        :type data: dict
        """

        self.dict = data

    @property
    def name(self):
        return self.dict['name']

    @property
    def multiple(self):
        return self.dict['multiple']

    @property
    def required(self):
        return self.dict['required']


class SeedInputFiles(SeedFiles):
    """Concrete class for Seed input files elements"""
    @property
    def media_types(self):
        return self.dict['mediaTypes']

    @property
    def partial(self):
        return self.dict['partial']


class SeedOutputFiles(SeedFiles):
    """Concrete class for Seed output files elements"""

    @property
    def media_type(self):
        return self.dict['mediaType']

    @property
    def pattern(self):
        return self.dict['pattern']

    def get_files(self):
        """Get a list of absolute paths to files following job execution

        :return: files matched by pattern defined for object
        :rtype: [str]
        :raises: OutputCaptureError
        """
        path_pattern = os.path.join(SCALE_JOB_EXE_OUTPUT_PATH, self.pattern)
        results = glob.glob(path_pattern)

        # Handle required validation
        if self.required and len(results) == 0:
            raise OutputCaptureError("No glob match for pattern '%s' defined for required output files"
                                     " key '%s'." % (self.pattern, self.name))

        # Check against multiple to verify we are matching the files as defined.
        if not self.multiple and len(results) > 1:
            raise OutputCaptureError("Pattern matched %i, which is not consistent with a false value for 'multiple'." %
                                     (len(results), ))

        return results


class SeedJson(object):
    __metaclass__ = ABCMeta

    def __init__(self, data):
        """Create a SeedJson from dict input equivalent

        :param data:
        :type data: dict
        """

        self.dict = data

    @property
    def name(self):
        return self.dict['name']

    @property
    def type(self):
        return self.dict['type']

    @property
    def python_type(self):
        """Provides an explicit python type to validate against incoming json types"""

        value_type = self.type.upper()

        if value_type == 'STRING':
            return basestring
        elif value_type == 'NUMBER':
            return float
        elif value_type == 'INTEGER':
            return int
        elif value_type == 'BOOLEAN':
            return bool
        elif value_type == 'OBJECT':
            return dict
        elif value_type == 'ARRAY':
            return list

        raise Exception("Unrecognized type '%s' specified for name %s." % (self.type, self.name))

    @property
    def required(self):
        return self.dict.get('required', True)


class SeedInputJson(SeedJson):
    """Concrete class for Seed input JSON elements"""
    pass


class SeedOutputJson(SeedJson):
    """Concrete class for Seed output JSON elements"""

    @property
    def key(self):
        return self.dict.get('key', None)

    @property
    def json_key(self):
        """Get the preferred key to match in seed.outputs.json for this JSON output

        The `key` member supercedes the `name` member when specified.

        :return: Key used to capture output JSON
        :rtype: str
        """
        value = self.name
        if self.key:
            value = self.key

        return value
