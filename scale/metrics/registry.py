"""Defines general classes used to manage metrics"""
from __future__ import unicode_literals

import abc
import datetime
import logging
import sys

logger = logging.getLogger(__name__)


# Each metrics type model should be registered here to make them available to the REST layer
_PROVIDERS = {}


class MetricsType(object):
    """Represents a type of metrics that can be queried.

    :keyword name: The system name of the metrics type.
    :type name: string
    :keyword title: The human-friendly display name of the metrics type.
    :type title: string
    :keyword description: A longer description of the metrics type.
    :type description: string
    :keyword filters: A list of filter parameter definitions supported by the metrics type.
    :type filters: list[:class:`metrics.registry.MetricsTypeFilter`]
    :keyword columns: A list of available columns supported by the metrics type.
    :type columns: list[:class:`metrics.registry.MetricsTypeColumn`]
    :keyword choices: A list of available models that can be used as filters for the metrics type. Each metrics type
        can use its own choice models, but any fields listed as filters must be included here at a minimum.
    :type choices: object
    """
    def __init__(self, name, title=None, description=None, filters=None, groups=None, columns=None, choices=None):
        self.name = name
        self.title = title
        self.description = description
        self.filters = filters or []
        self.groups = groups or []
        self.columns = columns or []
        self.choices = choices or []

    def get_column_names(self):
        """Gets a list of all column names for this metrics type.

        Column names can be used to select a specific series of plot values.

        :returns: The metrics type column names.
        :rtype: list[string]
        """
        return self._get_column_map().keys()

    def get_column(self, column_name):
        """Gets the column model associated with the given name.

        :param column_name: The name of the column to lookup.
        :type column_name: string
        :returns: The metrics type column.
        :rtype: :class:`metrics.registry.MetricsTypeColumn`
        """
        if column_name in self._get_column_map():
            return self._get_column_map()[column_name]
        raise MetricsTypeError('Metrics type missing column: %s -> %s', self.name, column_name)

    def get_column_set(self, column_names=None, group_names=None):
        """Gets the combined set of column models derived from the given names and groups.

        Column names use a simple lookup to get the corresponding column model and the group name is used to find all
        columns with a matching a value. Duplicates are then removed to produce the final result.

        :param column_names: The names of the columns to lookup.
        :type column_names: list[string]
        :param group_names: The names of the groups to lookup.
        :type group_names: list[string]
        :returns: The metrics type columns.
        :rtype: set[:class:`metrics.registry.MetricsTypeColumn`]
        """
        column_name_set = set(column_names) if column_names else set()
        column_name_set.update(self.get_group_columns(group_names))
        column_name_set = column_name_set or self.get_column_names()
        return [self.get_column(name) for name in column_name_set]

    def get_group_columns(self, group_names):
        """Gets the set of column models associated with the given groups.

        The group name is used to find all columns with a matching a value. Duplicates are then removed to produce the
        final result.

        :param group_names: The names of the groups to lookup.
        :type group_names: list[string]
        :returns: The metrics type columns.
        :rtype: set[:class:`metrics.registry.MetricsTypeColumn`]
        """
        results = set()
        group_ids = set(group_names) if group_names else set()
        for column in self.columns:
            if column.group and column.group in group_ids:
                results.add(column.name)
        return results

    def set_columns(self, model_class, field_types):
        """Sets all the metric type columns by inspecting the given database model.

        :param model_class: The class type of the metrics model to inspect.
        :type model_class: :class:`django.db.models.Model`
        :param field_types: The model field types to include as metrics columns.
        :type field_types: list[:class:`django.db.models.Field`]
        :returns: The metrics type columns.
        :rtype: set[:class:`metrics.registry.MetricsTypeColumn`]
        """
        columns = []
        for field in model_class._meta.fields:
            for field_class in field_types:
                if isinstance(field, field_class):
                    column = MetricsTypeColumn(field.name, field.verbose_name, field.help_text, field.units,
                                               field.group, field.aggregate)
                    columns.append(column)
        self.columns = columns

    def _get_column_map(self):
        """Gets a mapping of column name to column model definition.

        :returns: The metrics type column mapping.
        :rtype: dict[string, :class:`metrics.registry.MetricsTypeColumn`]
        """
        if not hasattr(self, '_column_map'):
            self._column_map = {c.name: c for c in self.columns} if self.columns else dict()
        return self._column_map


class MetricsTypeFilter(object):
    """Represents a parameter that can be used to filter metrics type values.

    :keyword param: The name of the filter parameter.
    :type param: string
    :keyword param_type: The data type of the filter parameter. Examples: bool, date, datetime, float, int, string, time
    :type type: string
    """
    def __init__(self, param, param_type='string'):
        self.param = param
        self.type = param_type


class MetricsTypeGroup(object):
    """Represents a group of attributes for a metrics type that can be selected as a series of plot values.

    :keyword name: The system name of the group.
    :type name: string
    :keyword title: The human-friendly display name of the group.
    :type title: string
    :keyword description: A longer description of the group.
    :type description: string
    """
    def __init__(self, name, title=None, description=None):
        self.name = name
        self.title = title
        self.description = description


class MetricsTypeColumn(object):
    """Represents an attribute of a metrics type that can be selected as a series of plot values.

    :keyword name: The system name of the column.
    :type name: string
    :keyword title: The human-friendly display name of the column.
    :type title: string
    :keyword description: A longer description of the column.
    :type description: string
    :keyword units: The mathematical units applied to the value. Examples: seconds, minutes, hours
    :type units: string
    :keyword group: The base field name used to group together related values. For example, a field may have several
        aggregate variations that all reference the same base attribute.
    :type group: string
    :keyword aggregate: The math operation used to compute the value. Examples: avg, max, min, sum
    :type aggregate: string
    """
    def __init__(self, name, title=None, description=None, units=None, group=None, aggregate=None):
        self.name = name
        self.title = title
        self.description = description
        self.units = units
        self.group = group
        self.aggregate = aggregate


class MetricsPlotValue(object):
    """Represents a single value within a series of values for a metrics type column.

    :keyword choice_id: The unique identifier of the choice model associated with the value.
    :type choice_id: string
    :keyword date: The date when the plot value occurred.
    :type date: datetime.date
    :keyword value: The actual plot value that was recorded.
    :type value: int
    """
    def __init__(self, choice_id, date, value):
        self.id = choice_id
        self.date = date
        self.value = value


class MetricsPlotData(object):
    """Represents a series of plot values for a single metrics type column.

    :keyword column: The metrics type column definition.
    :type column: :class:`metrics.registry.MetricsTypeColumn`
    :keyword min_x: The minimum x-axis value, which is always a date.
    :type min_x: datetime.date
    :keyword max_x: The maximum x-axis value, which is always a date.
    :type max_x: datetime.date
    :keyword min_y: The minimum y-axis value, which is always a number.
    :type min_y: int
    :keyword max_y: The maximum y-axis value, which is always a number.
    :type max_y: int
    :keyword values: A list of the actual plot values in the series.
    :type values: list[:class:`metrics.registry.MetricsPlotValue`]
    """
    def __init__(self, column, min_x=None, max_x=None, min_y=None, max_y=None, values=None):
        self.column = column
        self.min_x = min_x
        self.max_x = max_x
        self.min_y = min_y
        self.max_y = max_y
        self.values = values

    @classmethod
    def create(cls, query_set, date_field, choice_field, choice_ids, columns):
        """Creates new metrics plot data records from a query set of database models.

        :param query_set: A set of database models that are being counted towards metrics.
        :type query_set: :class:`django.models.QuerySet`
        :param date_field: The name of the field within each model that contains the recorded date.
        :type date_field: string
        :param choice_field: The name of the field within each model that contains the choice model relation.
        :type choice_field: string
        :param choice_ids: A list of related model identifiers to query.
        :type choice_ids: list[string]
        :param columns: A list of metrics type column definitions that should be included.
        :type columns: list[:class:`metrics.registry.MetricsTypeColumn`]
        :returns: The plot data models that were created.
        :rtype: list[:class:`metrics.registry.MetricsPlotData`]
        """
        results = {column.name: MetricsPlotData(column=column, values=[]) for column in columns}
        for entry in query_set.iterator():
            for column in columns:
                if not column.name in results:
                    results[column.name] = MetricsPlotData(column=column, values=[])
                MetricsPlotData._add_plot_value(results[column.name], entry, date_field, choice_field, choice_ids)
        return results.values()

    @classmethod
    def _add_plot_value(cls, plot_data, entry, date_field, choice_field, choice_ids=None):
        """Adds metrics to an existing plot data model.

        :param plot_data: The plot model to update with a new value.
        :type plot_data: :class:`metrics.registry.MetricsPlotData`
        :param entry: A dictionary representation of the metrics model to use as a source for adding a plot value.
        :type entry: dict[string, object]
        :param date_field: The name of the field within the entry dict that contains the recorded date.
        :type date_field: string
        :param choice_field: The name of the field within the entry dict that contains the choice model relation.
        :type choice_field: string
        :param choice_ids: A list of related model identifiers to query.
        :type choice_ids: list[string]
        :returns: The plot model that was added.
        :rtype: :class:`metrics.registry.MetricsPlotValue`
        """
        entry_val = entry[plot_data.column.name]
        if entry_val is None:
            return

        # Update the bounds for the y-axis
        plot_data.min_y = min(plot_data.min_y or sys.maxint, entry_val)
        plot_data.max_y = max(plot_data.max_y or 0, entry_val)

        # Update the bounds for the x-axis
        entry_date = entry[date_field]
        plot_data.min_x = min(plot_data.min_x or datetime.date.max, entry_date)
        plot_data.max_x = max(plot_data.max_x or datetime.date.min, entry_date)

        # Append a new value for the given entry
        if choice_ids:
            plot_value = MetricsPlotValue(choice_id=entry[choice_field], date=entry_date, value=entry_val)
            plot_data.values.append(plot_value)
            return plot_value

        # Aggregate values across entries when no choice filters are used
        if not plot_data.values or plot_data.values[-1].date != entry_date:
            plot_data.values.append(MetricsPlotValue(choice_id=None, date=entry_date, value=0))
        plot_value = plot_data.values[-1]
        plot_value.value += entry_val
        return plot_value


class MetricsTypeError(Exception):
    """Error class used when there is a problem generating metrics."""
    pass


class MetricsTypeProvider(object):
    """Base class used to handle requests for specific types of metrics."""
    __metaclass__ = abc.ABCMeta

    def calculate(self, date):
        """Calculates and saves new metrics models grouped by the given date.

        :param date: The target date metrics should be based on.
        :type date: datetime.date
        """
        raise NotImplemented()

    def get_metrics_type(self, include_choices=False):
        """Gets the metrics type model handled by this provider.

        :param include_choices: Whether or not to include all the possible model choices that can be used to filter
            metrics generated by this provider. Since the list of choices can be large and require additional database
            queries they are not included by default.
        :type include_choices: bool
        :returns: The metrics type for this provider.
        :rtype: :class:`metrics.registry.MetricsType`
        """
        raise NotImplemented()

    def get_plot_data(self, started=None, ended=None, choice_ids=None, columns=None):
        """Gets a list of plot values based on the given query parameters.

        :param started: The start of the time range to query.
        :type started: datetime.date
        :param ended: The end of the time range to query.
        :type ended: datetime.date
        :param choice_ids: A list of related model identifiers to query.
        :type choice_ids: list[string]
        :param columns: A list of metric columns to include from the metric type.
        :type columns: list[string]
        :returns: A series of plot values that match the query.
        :rtype: list[:class:`metrics.registry.MetricsPlotData`]
        """
        raise NotImplemented()


def register_provider(provider, serializer_class=None):
    """Registers the given metrics type definition to be called by the metrics management system.

    :param provider: The provider instance that is used to access the metrics.
    :type provider: :class:`metrics.registry.MetricsTypeProvider`
    :param serializer_class: The class used to serialize metrics generated by the provider.
    :type serializer_class: :class:`metrics.serializers.MetricsTypeDetailsSerializer`
    """
    metrics_type = provider.get_metrics_type()
    if metrics_type.name in _PROVIDERS:
        logger.warn('Duplicate metrics type definition registered for name: %s', metrics_type.name)
    logger.debug('Registering metrics type: %s -> %s', metrics_type.name, metrics_type)
    _PROVIDERS[metrics_type.name] = (provider, serializer_class)


def get_providers():
    """Gets a list of all registered metrics providers.

    :returns: The current metrics provider list.
    :rtype: list[:class:`metrics.registry.MetricsTypeProvider`]
    """
    return [provider for provider, _serializer in _PROVIDERS.values()]


def get_provider(name):
    """Gets the metrics provider registered with the given name.

    :param name: The name of the metrics provider to retrieve.
    :type name: string
    :returns: The metrics provider associated with the name.
    :rtype: :class:`metrics.registry.MetricsTypeProvider`

    :raises :class:`metrics.registry.MetricsTypeError`: If the registration is missing.
    """
    if name not in _PROVIDERS:
        raise MetricsTypeError('Unknown metrics type requested: %s', name)
    provider, _serializer = _PROVIDERS[name]
    return provider


def get_metrics_types():
    """Gets a list of all registered metrics types.

    :returns: The metrics type list.
    :rtype: list[:class:`metrics.registry.MetricsType`]
    """
    return [provider.get_metrics_type() for provider, _serializer in _PROVIDERS.values()]


def get_metrics_type(name, include_choices=False):
    """Gets the metrics type registered with the given name.

    :param name: The name of the metrics type to retrieve.
    :type name: string
    :param include_choices: Whether or not to include all the possible model choices that can be used to filter metrics
        generated by this provider. Since the list of choices can be large and require additional database queries they
        are not included by default.
    :type include_choices: bool
    :returns: The metrics type list.
    :rtype: list[:class:`metrics.registry.MetricsType`]
    """
    if name not in _PROVIDERS:
        raise MetricsTypeError('Unknown metrics type requested: %s', name)
    provider, _serializer = _PROVIDERS[name]
    return provider.get_metrics_type(include_choices=include_choices)


def get_serializer(name):
    """Gets the model serializer class for the given metrics type name.

    :param name: The name of the metrics type serializer to retrieve.
    :type name: string
    :returns: The class used to serialize the metrics type.
    :rtype: :class:`metrics.serializers.MetricsTypeDetailsSerializer`
    """
    if name not in _PROVIDERS:
        raise MetricsTypeError('Unknown metrics type requested: %s', name)
    _provider, serializer_class = _PROVIDERS[name]
    return serializer_class
