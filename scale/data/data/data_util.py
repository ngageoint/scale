from __future__ import absolute_import
from __future__ import unicode_literals

from data.data.value import FileValue, JsonValue

def get_file_ids(data):
    """Returns the file ids from a data object

    :param data: The Data object to inspect
    :type data: :class:`data.data.data.Data`
    :returns: A list of file ids
    :rtype: [int]
    """

    file_ids = set()
    for input_value in data.values.values():
        if isinstance(input_value, FileValue):
            for file_id in input_value.file_ids:
                file_ids.add(file_id)
    return file_ids

def get_parameter_names(data):
    """Returns the paramater names from a data object

    :param data: The Data object to inspect
    :type data: :class:`data.data.data.Data`
    :returns: A list of paramater names
    :rtype: [string]
    """
    names = set()
    for input_value in data.values.values():
        if isinstance(input_value, JsonValue):
            names.add(input_value.name)
    return names
