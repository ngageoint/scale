"""Defines the class for filtering data"""
from __future__ import absolute_import
from __future__ import unicode_literals

import logging

from data.filter.exceptions import InvalidDataFilter
from storage.models import ScaleFile
from util.validation import ValidationWarning

logger = logging.getLogger(__name__)

FILE_TYPES = {'filename', 'media-type', 'data-type'}

STRING_TYPES = {'string', 'filename', 'media-type', 'data-type'}

STRING_CONDITIONS = {'==', '!=', 'in', 'not in', 'contains'}

NUMBER_TYPES = {'integer', 'number'}

NUMBER_CONDITIONS = {'<', '<=', '>','>=', '==', '!=', 'between', 'in', 'not in'}

BOOL_TYPES = {'boolean'}

BOOL_CONDITIONS = {'==', '!='}

OBJECT_TYPES = {'meta-data', 'object'}

OBJECT_CONDITIONS = {'subset of', 'superset of'}


def _less_than(input, values):
    """Checks if the given input is < the first value in the list

    :param input: The input to check
    :type input: int/float
    :param values: The values to check
    :type values: list
    :returns: True if the condition check passes, False otherwise
    :rtype: bool
    """

    try:
        return input < values[0]
    except IndexError:
        return False

def _less_than_equal(input, values):
    """Checks if the given input is <= the first value in the list

    :param input: The input to check
    :type input: int/float
    :param values: The values to check
    :type values: list
    :returns: True if the condition check passes, False otherwise
    :rtype: bool
    """

    try:
        return input <= values[0]
    except IndexError:
        return False

def _greater_than(input, values):
    """Checks if the given input is > the first value in the list

    :param input: The input to check
    :type input: int/float
    :param values: The values to check
    :type values: list
    :returns: True if the condition check passes, False otherwise
    :rtype: bool
    """

    try:
        return input > values[0]
    except IndexError:
        return False

def _greater_than_equal(input, values):
    """Checks if the given input is >= the first value in the list

    :param input: The input to check
    :type input: int/float
    :param values: The values to check
    :type values: list
    :returns: True if the condition check passes, False otherwise
    :rtype: bool
    """

    try:
        return input >= values[0]
    except IndexError:
        return False

def _equal(input, values):
    """Checks if the given input is equal to the first value in the list

    :param input: The input to check
    :type input: int/float
    :param values: The values to check
    :type values: list
    :returns: True if the condition check passes, False otherwise
    :rtype: bool
    """

    try:
        return input == values[0]
    except IndexError:
        return False

def _not_equal(input, values):
    """Checks if the given input is not equal to the first value in the list

    :param input: The input to check
    :type input: int/float
    :param values: The values to check
    :type values: list
    :returns: True if the condition check passes, False otherwise
    :rtype: bool
    """

    try:
        return input != values[0]
    except IndexError:
        return False

def _between(input, values):
    """Checks if the given input is between the first two values in the list

    :param input: The input to check
    :type input: int/float
    :param values: The values to check
    :type values: list
    :returns: True if the condition check passes, False otherwise
    :rtype: bool
    """

    try:
        return input >= values[0] and input <= values[1]
    except IndexError:
        return False

def _in(input, values):
    """Checks if the given input is in the list of values, or is a subset of a value

    :param input: The input to check
    :type input: int/float
    :param values: The values to check
    :type values: list
    :returns: True if the condition check passes, False otherwise
    :rtype: bool
    """

    if input in values:
        return True
    for value in values:
        if input in value:
            return True
    return False
    
def _not_in(input, values):
    """Checks if the given input is not in the list of values and is not a subset of a value

    :param input: The input to check
    :type input: int/float/string
    :param values: The values to check
    :type values: list
    :returns: True if the condition check passes, False otherwise
    :rtype: bool
    """

    if input in values:
        return False
    for value in values:
        if input in value:
            return False
    return True

def _contains(input, values):
    """Checks if the given input contains a value from the given list

    :param input: The input to check
    :type input: string/list
    :param values: The values to check
    :type values: list
    :returns: True if the condition check passes, False otherwise
    :rtype: bool
    """

    try:
        for value in values:
            if value in input:
                return True
    except TypeError:
        return False # catch error if input is not an iterable
    return False
    
def _subset(input, values):
    """Checks if the given input is a subset of the given value

    :param input: The input to check
    :type input: dict
    :param values: The values to check
    :type values: list
    :returns: True if the condition check passes, False otherwise
    :rtype: bool
    """

    try:
        return all(item in values[0].items() for item in input.items())
    except AttributeError:
        return False # catch error if input or values are not a dictionary
    except IndexError:
        return False
    return False

def _superset(input, values):
    """Checks if the given input is a superset of the given value

    :param input: The input to check
    :type input: dict
    :param values: The values to check
    :type values: list
    :returns: True if the condition check passes, False otherwise
    :rtype: bool
    """

    try:
        return all(item in input.items() for item in values[0].items())
    except AttributeError:
        return False # catch error if input or values are not a dictionary
    except IndexError:
        return False
    return False

ALL_CONDITIONS = {'<': _less_than, '<=': _less_than_equal, '>': _greater_than,'>=': _greater_than_equal,
                  '==': _equal, '!=': _not_equal, 'between': _between, 'in': _in, 'not in': _not_in, 
                  'contains': _contains, 'subset of': _subset, 'superset of': _superset}

class DataFilter(object):
    """Represents a filter that either accepts or denies a set of data values
    """

    def __init__(self, filter_list=None, all=True):
        """Constructor

        :param filters: Filters to determine whether to accept or deny data
        :type filters: dict
        :param all: Whether all filters need to pass to accept data
        :type filters: boolean
        """

        # TODO: after implementing this class, implement recipe.definition.node.ConditionNodeDefinition.__init__
        if not filter_list:
            filter_list = []
        self.filter_list = filter_list
        self.all = all

    def add_filter(self, filter_dict):
        """Adds a filter definition

        :param filter_dict: data filter to add
        :type filter_dict: dict

        :raises :class:`recipe.definition.exceptions.InvalidDataFilter`: If the filter is invalid
        """

        filter_dict = DataFilter.validate_filter(filter_dict)

        self.filter_list.append(filter_dict)

    def is_data_accepted(self, data):
        """Indicates whether the given data passes the filter or not

        :param data: The data to check against the filter
        :type data: :class:`data.data.data.Data`
        :returns: True if the data is accepted, False if the data is denied
        :rtype: bool
        """

        success = True
        for f in self.filter_list:
            name = f['name']
            type = f['type']
            cond = f['condition']
            values = f['values']
            filter_success = False
            if name in data.values:
                param = data.values[name]
                try:
                    if type == 'filename':
                        filenames = [scale_file.file_name for scale_file in ScaleFile.objects.filter(id__in=param.file_ids)]
                        # attempt to run condition on list first, i.e. in case we're checking 'contains'
                        filter_success |= ALL_CONDITIONS[cond](filenames, values)
                        for filename in filenames:
                            # attempt to run condition on inidividual items, if any succeed we pass the filter
                            filter_success |= ALL_CONDITIONS[cond](filename, values)
                    elif type == 'media-type':
                        media_types = [scale_file.media_type for scale_file in ScaleFile.objects.filter(id__in=param.file_ids)]
                        filter_success |= ALL_CONDITIONS[cond](media_types, values)
                        for media_type in media_types:
                            filter_success |= ALL_CONDITIONS[cond](media_type, values)
                    elif type == 'data-type':
                        data_types = [scale_file.data_type for scale_file in ScaleFile.objects.filter(id__in=param.file_ids)]
                        filter_success |= ALL_CONDITIONS[cond](data_types, values)
                        for data_type in data_types:
                            filter_success |= ALL_CONDITIONS[cond](data_type, values)
                    elif type == 'meta-data':
                        meta_data_list = [scale_file.meta_data for scale_file in ScaleFile.objects.filter(id__in=param.file_ids)]
                        if 'fields' in f:
                            if len(f['fields']) != len(values):
                                logger.exception('Length of fields (%s) and values (%s) are not equal' % (f['fields'], values))
                                return False
                            for field, value in zip(f['fields'], values):
                                filter_success &= ALL_CONDITIONS[cond](meta_data[field], value)
                        else:
                            filter_success |= ALL_CONDITIONS[cond](meta_data_list, values)
                            for item in meta_data_list:
                                filter_success |= ALL_CONDITIONS[cond](item, values)
                    else:
                        filter_success |= ALL_CONDITIONS[cond](param.value, values)
                except AttributeError:
                    logger.error('Attempting to run file filter on json parameter or vice versa')
                    success = False
                except KeyError:
                    logger.error('Condition %s does not exist' % cond)
                    success = False
                except ScaleFile.DoesNotExist:
                    logger.error('Attempting to run file filter on non-existant file(s): %d' % param.file_ids)
                    success = False
            if filter_success and not self.all:
                return True # One filter passed, so return True
            if not filter_success and self.all:
                return False # One filter failed, so return False
            success &= filter_success
        return success

    def is_filter_equal(self, data_filter):
        """Indicates whether the given data filter is equal to this filter or not

        :param data_filter: The data filter
        :type data_filter: :class:`data.filter.filter.DataFilter`
        :returns: True if the data filter is equal to this one, False otherwise
        :rtype: bool
        """

        equal = self.all == data_filter.all
        equal &= self.filter_list == data_filter.filter_list
        
        return equal

    def validate(self, interface):
        """Validates this data filter against the given interface

        :param interface: The interface describing the data that will be passed to the filter
        :type interface: :class:`data.interface.interface.Interface`
        :returns: A list of warnings discovered during validation
        :rtype: list

        :raises :class:`data.filter.exceptions.InvalidDataFilter`: If the data filter is invalid
        """

        warnings = []
        unmatched = interface.parameters.keys()

        for f in self.filter_list:
            name = f['name']
            type = f['type']
            if name in interface.parameters:
                if name in unmatched:
                    unmatched.remove(name)
                if interface.parameters[name].param_type == 'file' and type not in FILE_TYPES:
                    raise InvalidDataFilter('MISMATCHED_TYPE', 'Interface parameter is a file type and requires a file type filter.')
                if interface.parameters[name].param_type == 'json' and type in FILE_TYPES:
                    raise InvalidDataFilter('MISMATCHED_TYPE', 'Interface parameter is a json type and will not work with a file type filter.')
                if interface.parameters[name].param_type == 'json':
                    if interface.parameters[name].json_type in STRING_TYPES and type not in STRING_TYPES:
                        raise InvalidDataFilter('MISMATCHED_TYPE', 'Interface parameter is a string and filter is not a string type filter')
                    if interface.parameters[name].json_type in NUMBER_TYPES and type not in NUMBER_TYPES:
                        raise InvalidDataFilter('MISMATCHED_TYPE', 'Interface parameter is a number and filter is not a number type filter')
                    if interface.parameters[name].json_type in BOOL_TYPES and type not in BOOL_TYPES:
                        raise InvalidDataFilter('MISMATCHED_TYPE', 'Interface parameter is a number and filter is not a number type filter')
                    json_type = interface.parameters[name].json_type
                    if json_type not in BOOL_TYPES and json_type not in STRING_TYPES and json_type not in NUMBER_TYPES:
                        raise InvalidDataFilter('MISMATCHED_TYPE', 'Interface parameter type is not supported by data filters')
            else:
                warnings.append(ValidationWarning('UNMATCHED_FILTER',
                                                  'Filter with name \'%s\' does not have a matching parameter'))
        
        if unmatched:
            warnings.append(ValidationWarning('UNMATCHED_PARAMETERS', 'No matching filters for these parameters: \'%s\' ' % unmatched))

        return warnings

    @staticmethod
    def validate_filter(filter_dict):
        """Validates a data filter dictionary

        :param filter_dict: data filter to validate
        :type filter_dict: dict

        :raises :class:`recipe.definition.exceptions.InvalidDataFilter`: If the filter is invalid

        :returns: Validated filter if the tests pass
        :rtype: dict
        """

        if 'name' not in filter_dict:
            raise InvalidDataFilter('MISSING_NAME', 'Missing name for filter')

        name = filter_dict['name']
        if 'type' not in filter_dict:
            raise InvalidDataFilter('MISSING_TYPE', 'Missing type for \'%s\'' % name)

        if 'condition' not in filter_dict:
            raise InvalidDataFilter('MISSING_CONDITION', 'Missing condition for \'%s\'' % name)

        if 'values' not in filter_dict:
            raise InvalidDataFilter('MISSING_VALUES', 'Missing values for \'%s\'' % name)
            
        type = filter_dict['type']
        condition = filter_dict['condition']
        values = filter_dict['values']
        
        if condition not in ALL_CONDITIONS:
            raise InvalidDataFilter('INVALID_CONDITION', 'Invalid condition \'%s\' for \'%s\'. Valid conditions are: %s'
                                    % (condition, name, ALL_CONDITIONS))

        if type in STRING_TYPES and condition not in STRING_CONDITIONS:
            raise InvalidDataFilter('INVALID_CONDITION', 'Invalid condition \'%s\' for \'%s\'. Valid conditions are: %s'
                                    % (condition, name, STRING_CONDITIONS))

        if type in NUMBER_TYPES and condition not in NUMBER_CONDITIONS:
            raise InvalidDataFilter('INVALID_CONDITION', 'Invalid condition \'%s\' for \'%s\'. Valid conditions are: %s'
                                    % (condition, name, NUMBER_CONDITIONS))

        if type in BOOL_TYPES and condition not in BOOL_CONDITIONS:
            raise InvalidDataFilter('INVALID_CONDITION', 'Invalid condition \'%s\' for \'%s\'. Valid conditions are: %s'
                                    % (condition, name, BOOL_CONDITIONS))

        if type not in STRING_TYPES and type not in NUMBER_TYPES and type not in BOOL_TYPES:
            raise InvalidDataFilter('INVALID_TYPE', 'No valid conditions for this type')

        filter_values = []
        if type == 'number':
            for value in values:
                try:
                    filter_values.append(float(value))
                except ValueError:
                    raise InvalidDataFilter('VALUE_ERROR', 'Expected float for \'%s\', found %s' % (name, value))
        elif type == 'integer':
            for value in values:
                try:
                    filter_values.append(int(value))
                except ValueError:
                    raise InvalidDataFilter('VALUE_ERROR', 'Expected int for \'%s\', found %s' % (name, value))
        else:
            filter_values.extend(values)

        return {'name': name, 'type': type, 'condition': condition, 'values': filter_values}