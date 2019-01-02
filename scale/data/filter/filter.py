"""Defines the class for filtering data"""
from __future__ import absolute_import
from __future__ import unicode_literals

from data.filter.exceptions import InvalidDataFilter

CONDITIONS = {'<', '<=', '>','>=', '==', '!=', 'between', 'is in'}

class DataFilter(object):
    """Represents a filter that either accepts or denies a set of data values
    """

    def __init__(self, filters):
        """Constructor

        :param filters: Filters to determine whether to accept or deny data
        :type filters: dict
        """

        # TODO: there are a number of unit tests that will need to have real DataFilters created instead of
        # DataFilter(True) or DataFilter(False)

        # TODO: after implementing this class, implement recipe.definition.node.ConditionNodeDefinition.__init__
        self.filters = []

    def add_filter(self, name, type, condition, values):
        """Adds a condition node to the recipe graph

        :param name: Name of the data value to compare against
        :type name: string
        :param type: The type of the data value being compared
        :type type: string
        :param condition: The condition to test (<, >, ==, between, contains, etc)
        :type condition: string
        :param values: The values to compare for the condition
        :type values: list

        :raises :class:`recipe.definition.exceptions.InvalidDefinition`: If the node is duplicated
        """

        if not name:
            raise InvalidDataFilter('MISSING_NAME', 'Missing name for \'%s\'' % name)

        if not type:
            raise InvalidDataFilter('MISSING_TYPE', 'Missing type for \'%s\'' % name)

        if not condition:
            raise InvalidDataFilter('MISSING_CONDITION', 'Missing condition for \'%s\'' % name)

        if condition not in CONDITIONS:
            raise InvalidDataFilter('INVALID_CONDITION', 'Invalid condition \'%s\' for \'%s\'. Valid conditions are: %s'
                                    % (condition, name, CONDITIONS))

        if not values:
            raise InvalidDataFilter('MISSING_VALUES', 'Missing values for \'%s\'' % name)

        self.filters.append({'name': name, 'type': type, 'condition': condition, 'values': values})

    def is_data_accepted(self, data):
        """Indicates whether the given data passes the filter or not

        :param data: The data to check against the filter
        :type data: :class:`data.data.data.Data`
        :returns: True if the data is accepted, False if the data is denied
        :rtype: bool
        """

        # TODO: provide real implementation
        return self.accept

    def is_filter_equal(self, data_filter):
        """Indicates whether the given data filter is equal to this filter or not

        :param data_filter: The data filter
        :type data_filter: :class:`data.filter.filter.DataFilter`
        :returns: True if the data filter is equal to this one, False otherwise
        :rtype: bool
        """

        # TODO: provide real implementation
        return self.accept == data_filter.accept

    def validate(self, interface):
        """Validates this data filter against the given interface

        :param interface: The interface describing the data that will be passed to the filter
        :type interface: :class:`data.interface.interface.Interface`
        :returns: A list of warnings discovered during validation
        :rtype: list

        :raises :class:`data.filter.exceptions.InvalidDataFilter`: If the data filter is invalid
        """

        warnings = []

        # TODO: implement

        return warnings
