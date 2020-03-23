"""Defines the class for filtering data"""
from __future__ import absolute_import
from __future__ import unicode_literals

import copy
import logging

from data.filter.exceptions import InvalidDataFilter
from storage.models import ScaleFile
from util.validation import ValidationWarning

logger = logging.getLogger(__name__)

FILE_TYPES = {'filename', 'media-type', 'data-type', 'meta-data'}

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
    :type values: :func:`list`
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
    :type values: :func:`list`
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
    :type values: :func:`list`
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
    :type values: :func:`list`
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
    :type values: :func:`list`
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
    :type values: :func:`list`
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
    :type values: :func:`list`
    :returns: True if the condition check passes, False otherwise
    :rtype: bool
    """

    try:
        return input >= values[0] and input <= values[1]
    except IndexError:
        return False

def _in(input, values):
    """Checks if the given input is in the list of values

    :param input: The input to check
    :type input: int/float
    :param values: The values to check
    :type values: :func:`list`
    :returns: True if the condition check passes, False otherwise
    :rtype: bool
    """

    try:
        if input in values:
            return True
    except TypeError:
        return False
    return False

def _not_in(input, values):
    """Checks if the given input is not in the list of values

    :param input: The input to check
    :type input: int/float/string
    :param values: The values to check
    :type values: :func:`list`
    :returns: True if the condition check passes, False otherwise
    :rtype: bool
    """

    try:
        if input in values:
            return False
    except TypeError:
        return True
    return True

def _contains(input, values):
    """Checks if the given input contains a value from the given list

    :param input: The input to check
    :type input: string/list
    :param values: The values to check
    :type values: :func:`list`
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
    :type values: :func:`list`
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
    :type values: :func:`list`
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

def _getNestedDictField(data_dict, map_list):
    try:
        for k in map_list: data_dict = data_dict[k]
        return data_dict
    except KeyError:
        return None

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
            filter_type = f['type']
            cond = f['condition']
            values = f['values']
            filter_success = False
            all_fields = False
            if 'all_fields' in f and f['all_files']:
                all_fields = True
            all_files = False
            if 'all_files' in f and f['all_files']:
                all_files = True
            if name in data.values:
                param = data.values[name]
                try:
                    if filter_type in {'filename', 'media-type', 'data-type'}:
                        if filter_type == 'filename':
                            file_values = [scale_file.file_name for scale_file in ScaleFile.objects.filter(id__in=param.file_ids)]
                        elif filter_type == 'media-type':
                            file_values = [scale_file.media_type for scale_file in ScaleFile.objects.filter(id__in=param.file_ids)]
                        elif filter_type == 'data-type':
                            list_of_lists = [scale_file.data_type_tags for scale_file in ScaleFile.objects.filter(id__in=param.file_ids)]
                            file_values = [item for sublist in list_of_lists for item in sublist]
                        # attempt to run condition on list, i.e. in case we're checking 'contains'
                        filter_success |= ALL_CONDITIONS[cond](file_values, values)
                        file_success = all_files
                        for value in file_values:
                            if all_files:
                                # attempt to run condition on individual items, if any fail we fail the filter
                                file_success &= ALL_CONDITIONS[cond](value, values)
                            else:
                                # attempt to run condition on individual items, if any succeed we pass the filter
                                file_success |= ALL_CONDITIONS[cond](value, values)
                        filter_success |= file_success
                    elif filter_type == 'meta-data':
                        meta_data_list = [scale_file.meta_data for scale_file in ScaleFile.objects.filter(id__in=param.file_ids)]
                        if 'fields' in f:
                            if len(f['fields']) != len(values):
                                logger.exception('Length of fields (%s) and values (%s) are not equal' % (f['fields'], values))
                                return False
                            file_success = all_files
                            for meta_data in meta_data_list:
                                field_success = all_fields
                                for field_path, value in zip(f['fields'], values):
                                    item = _getNestedDictField(meta_data, field_path)
                                    if all_fields:
                                        # attempt to run condition on individual items, if any fail we fail the filter
                                        field_success &= ALL_CONDITIONS[cond](item, value)
                                    else:
                                        # attempt to run condition on individual items, if any succeed we pass the filter
                                        field_success |= ALL_CONDITIONS[cond](item, value)
                                if all_files:
                                    file_success &= field_success
                                else:
                                    file_success |= field_success
                            filter_success |= file_success
                        else:
                            filter_success |= ALL_CONDITIONS[cond](meta_data_list, values)
                            file_success = all_files
                            for item in meta_data_list:
                                if all_files:
                                    # attempt to run condition on individual items, if any fail we fail the filter
                                    file_success &= ALL_CONDITIONS[cond](item, values)
                                else:
                                    # attempt to run condition on individual items, if any succeed we pass the filter
                                    file_success |= ALL_CONDITIONS[cond](item, values)
                            filter_success |= file_success
                    elif filter_type == 'object':
                        if 'fields' in f:
                            if len(f['fields']) != len(values):
                                logger.exception('Length of fields (%s) and values (%s) are not equal' % (f['fields'], values))
                                return False
                            field_success = all_fields
                            for field_path, value in zip(f['fields'], values):
                                item = _getNestedDictField(param.value, field_path)
                                if all_fields:
                                    field_success &= ALL_CONDITIONS[cond](item, values)
                                else:
                                    field_success |= ALL_CONDITIONS[cond](item, values)
                            filter_success |= field_success
                        else:
                            filter_success |= ALL_CONDITIONS[cond](param.value, values)
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
        :rtype: :func:`list`

        :raises :class:`data.filter.exceptions.InvalidDataFilter`: If the data filter is invalid
        """

        warnings = []
        unmatched = interface.parameters.keys()

        for f in self.filter_list:
            name = f['name']
            filter_type = f['type']
            if name in interface.parameters:
                if name in unmatched:
                    unmatched.remove(name)
                if interface.parameters[name].param_type == 'file' and filter_type not in FILE_TYPES:
                    raise InvalidDataFilter('MISMATCHED_TYPE', 'Interface parameter is a file type and requires a file type filter.')
                if interface.parameters[name].param_type == 'json' and filter_type in FILE_TYPES:
                    raise InvalidDataFilter('MISMATCHED_TYPE', 'Interface parameter is a json type and will not work with a file type filter.')
                if interface.parameters[name].param_type == 'json':
                    if interface.parameters[name].json_type in STRING_TYPES and filter_type not in STRING_TYPES:
                        raise InvalidDataFilter('MISMATCHED_TYPE', 'Interface parameter is a string and filter is not a string type filter')
                    if interface.parameters[name].json_type in NUMBER_TYPES and filter_type not in NUMBER_TYPES:
                        raise InvalidDataFilter('MISMATCHED_TYPE', 'Interface parameter is a number and filter is not a number type filter')
                    if interface.parameters[name].json_type in BOOL_TYPES and filter_type not in BOOL_TYPES:
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

        filter_type = filter_dict['type']
        condition = filter_dict['condition']
        values = filter_dict['values']

        if condition not in ALL_CONDITIONS:
            raise InvalidDataFilter('INVALID_CONDITION', 'Invalid condition \'%s\' for \'%s\'. Valid conditions are: %s'
                                    % (condition, name, ALL_CONDITIONS))

        if filter_type in STRING_TYPES and condition not in STRING_CONDITIONS:
            raise InvalidDataFilter('INVALID_CONDITION', 'Invalid condition \'%s\' for \'%s\'. Valid conditions are: %s'
                                    % (condition, name, STRING_CONDITIONS))

        if filter_type in NUMBER_TYPES and condition not in NUMBER_CONDITIONS:
            raise InvalidDataFilter('INVALID_CONDITION', 'Invalid condition \'%s\' for \'%s\'. Valid conditions are: %s'
                                    % (condition, name, NUMBER_CONDITIONS))

        if filter_type in BOOL_TYPES and condition not in BOOL_CONDITIONS:
            raise InvalidDataFilter('INVALID_CONDITION', 'Invalid condition \'%s\' for \'%s\'. Valid conditions are: %s'
                                    % (condition, name, BOOL_CONDITIONS))

        if filter_type in OBJECT_TYPES and condition not in OBJECT_CONDITIONS:
            if 'fields' not in filter_dict or not filter_dict['fields']:
                msg = 'Object %s does not have object condition (%s) and fields property is not set'
                raise InvalidDataFilter('INVALID_CONDITION', msg % (name, OBJECT_CONDITIONS))

        if 'fields' in filter_dict:
            if len(filter_dict['fields']) != len(values):
                raise InvalidDataFilter('INVALID_FIELDS', 'Fields property must be same length as values')

        if filter_type not in STRING_TYPES and filter_type not in NUMBER_TYPES and filter_type not in BOOL_TYPES and filter_type not in OBJECT_TYPES:
            raise InvalidDataFilter('INVALID_TYPE', 'No valid conditions for this type')

        filter_values = []
        if filter_type == 'number':
            for value in values:
                try:
                    filter_values.append(float(value))
                except ValueError:
                    raise InvalidDataFilter('VALUE_ERROR', 'Expected float for \'%s\', found %s' % (name, value))
        elif filter_type == 'integer':
            for value in values:
                try:
                    filter_values.append(int(value))
                except ValueError:
                    raise InvalidDataFilter('VALUE_ERROR', 'Expected int for \'%s\', found %s' % (name, value))
        else:
            filter_values.extend(values)

        ret_val = copy.deepcopy(filter_dict)
        ret_val['values'] = filter_values
        return ret_val