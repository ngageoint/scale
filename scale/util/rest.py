'''Defines utilities for building RESTful APIs.'''
import datetime

import django.utils.timezone as timezone
import rest_framework.serializers as serializers
import rest_framework.status as status
from django.core.paginator import Paginator, EmptyPage
from rest_framework.exceptions import APIException

import util.parse as parse_util
from util.parse import ParseError


class ModelIdSerializer(serializers.Serializer):
    '''Converts a model to a lightweight place holder object with only an identifier to REST output'''
    id = serializers.IntegerField()


class BadParameter(APIException):
    '''Exception indicating a REST API call contains an invalid value or a missing required parameter.'''
    status_code = status.HTTP_400_BAD_REQUEST


class ReadOnly(APIException):
    '''Exception indicating a REST API call is attempting to update a field that does not support it.'''
    status_code = status.HTTP_400_BAD_REQUEST


def check_update(request, fields):
    '''Checks whether the given request includes fields that are not allowed to be updated.

    :param request: The context of an active HTTP request.
    :type request: :class:`rest_framework.request.Request`
    :param fields: A list of field names that are permitted.
    :type fields: list[str]
    :returns: True when the request does not include extra fields.
    :rtype: bool

    :raises :class:`util.rest.ReadOnly`: If the request includes unsupported fields to update.
    :raises :class:`exceptions.AssertionError`: If fields in not a list or None.
    '''
    fields = fields or []
    assert(type(fields) == type([]))
    extra = filter(lambda x, y=fields: x not in y, request.DATA.keys())
    if extra:
        raise ReadOnly(u'Fields do not allow updates: %s' % ', '.join(extra))
    return True


def check_time_range(started, ended, max_duration=None):
    '''Checks whether the given time range is valid.

    :param started: The start of a time range.
    :type started: datetime.datetime
    :param ended: The end of a time range.
    :type ended: datetime.datetime
    :param max_duration: The maximum amount of time between the started and ended range.
    :type max_duration: datetime.timedelta
    :returns: True when the time range is valid.
    :rtype: bool

    :raises :class:`util.rest.BadParameter`: If there is a problem with the time range.
    '''
    if not started or not ended:
        return True
    if started == ended:
        raise BadParameter('Start and end values must be different')
    if started > ended:
        raise BadParameter('Start time must come before end time')

    if max_duration:
        duration = ended - started
        if datetime.timedelta(days=0) > duration or max_duration < duration:
            raise BadParameter(u'Time range must be between 0 and %s' % max_duration)
    return True


def get_relative_days(days):
    '''Calculates a relative datetime in the past without any time offsets.

    This is useful when a service wants to have a default value of, for example 7 days back. If an ISO duration format
    is used, such as P7D then the current time will be factored in which results in the earliest day being incomplete
    when computing an absolute time stamp.

    :param days: The number of days back to calculate from now.
    :type days: int
    :returns: An absolute time stamp that is the complete range of relative days back.
    :rtype: datetime.datetime
    '''
    base_date = (timezone.now() - datetime.timedelta(days=days)).date()
    return datetime.datetime.combine(base_date, datetime.time.min).replace(tzinfo=timezone.utc)


def parse_string(request, name, default_value=None, required=True):
    '''Parses a string parameter from the given request.

    :param request: The context of an active HTTP request.
    :type request: :class:`rest_framework.request.Request`
    :param name: The name of the parameter to parse.
    :type name: str
    :param default_value: The name of the parameter to parse.
    :type default_value: str
    :param required: Indicates whether or not the parameter is required. An exception will be raised if the parameter
        does not exist, there is no default value, and required is True.
    :type required: bool
    :returns: The value of the named parameter or the default value if provided.
    :rtype: str

    :raises :class:`util.rest.BadParameter`: If the value cannot be parsed.
    '''
    return _get_param(request, name, default_value, required)


def parse_string_list(request, name, default_value=None, required=True):
    '''Parses a list of string parameters from the given request.

    :param request: The context of an active HTTP request.
    :type request: :class:`rest_framework.request.Request`
    :param name: The name of the parameter to parse.
    :type name: str
    :param default_value: The name of the parameter to parse.
    :type default_value: list[str]
    :param required: Indicates whether or not the parameter is required. An exception will be raised if the parameter
        does not exist, there is no default value, and required is True.
    :type required: bool
    :returns: The value of the named parameter or the default value if provided.
    :rtype: str

    :raises :class:`util.rest.BadParameter`: If the value cannot be parsed.
    '''
    return _get_param_list(request, name, default_value, required)


def parse_bool(request, name, default_value=None, required=True):
    '''Parses a bool parameter from the given request.

    :param request: The context of an active HTTP request.
    :type request: :class:`rest_framework.request.Request`
    :param name: The name of the parameter to parse.
    :type name: str
    :param default_value: The name of the parameter to parse.
    :type default_value: bool
    :param required: Indicates whether or not the parameter is required. An exception will be raised if the parameter
        does not exist, there is no default value, and required is True.
    :type required: bool
    :returns: The value of the named parameter or the default value if provided.
    :rtype: bool

    :raises :class:`util.rest.BadParameter`: If the value cannot be parsed.
    '''
    value = _get_param(request, name, default_value, required)
    if not isinstance(value, basestring):
        return value

    value = value.strip().lower()
    if value == 'true' or value == 't' or value == '1':
        return True
    if value == 'false' or value == 'f' or value == '0':
        return False
    raise BadParameter('Parameter must be a valid boolean: "%s"' % name)


def parse_int(request, name, default_value=None, required=True):
    '''Parses an integer parameter from the given request.

    :param request: The context of an active HTTP request.
    :type request: :class:`rest_framework.request.Request`
    :param name: The name of the parameter to parse.
    :type name: str
    :param default_value: The name of the parameter to parse.
    :type default_value: int
    :param required: Indicates whether or not the parameter is required. An exception will be raised if the parameter
        does not exist, there is no default value, and required is True.
    :type required: bool
    :returns: The value of the named parameter or the default value if provided.
    :rtype: int

    :raises :class:`util.rest.BadParameter`: If the value cannot be parsed.
    '''
    value = _get_param(request, name, default_value, required)
    if not isinstance(value, basestring):
        return value

    try:
        return int(value)
    except (TypeError, ValueError):
        raise BadParameter('Parameter must be a valid integer: "%s"' % name)


def parse_int_list(request, name, default_value=None, required=True):
    '''Parses a list of int parameters from the given request.

    :param request: The context of an active HTTP request.
    :type request: :class:`rest_framework.request.Request`
    :param name: The name of the parameter to parse.
    :type name: str
    :param default_value: The name of the parameter to parse.
    :type default_value: list[int]
    :param required: Indicates whether or not the parameter is required. An exception will be raised if the parameter
        does not exist, there is no default value, and required is True.
    :type required: bool
    :returns: The value of the named parameter or the default value if provided.
    :rtype: str

    :raises :class:`util.rest.BadParameter`: If the value cannot be parsed.
    '''
    param_list = _get_param_list(request, name, default_value, required)

    if param_list and len(param_list):
        results = []
        for param in param_list:
            try:
                results.append(int(param))
            except (TypeError, ValueError):
                raise BadParameter('Parameter must be a valid integer: "%s"' % name)
        return results
    return param_list


def parse_float(request, name, default_value=None, required=True):
    '''Parses a floating point parameter from the given request.

    :param request: The context of an active HTTP request.
    :type request: :class:`rest_framework.request.Request`
    :param name: The name of the parameter to parse.
    :type name: str
    :param default_value: The name of the parameter to parse.
    :type default_value: float
    :param required: Indicates whether or not the parameter is required. An exception will be raised if the parameter
        does not exist, there is no default value, and required is True.
    :type required: bool
    :returns: The value of the named parameter or the default value if provided.
    :rtype: float

    :raises :class:`util.rest.BadParameter`: If the value cannot be parsed.
    '''
    value = _get_param(request, name, default_value, required)
    if not isinstance(value, basestring):
        return value

    try:
        return float(value)
    except (TypeError, ValueError):
        raise BadParameter('Parameter must be a valid float: "%s"' % name)


def parse_timestamp(request, name, default_value=None, required=True):
    '''Parses any valid ISO datetime, duration, or timestamp parameter from the given request.

    :param request: The context of an active HTTP request.
    :type request: :class:`rest_framework.request.Request`
    :param name: The name of the parameter to parse.
    :type name: str
    :param default_value: The name of the parameter to parse.
    :type default_value: datetime.timedelta
    :param required: Indicates whether or not the parameter is required. An exception will be raised if the parameter
        does not exist, there is no default value, and required is True.
    :type required: bool
    :returns: The value of the named parameter or the default value if provided.
    :rtype: datetime.datetime

    :raises :class:`util.rest.BadParameter`: If the value cannot be parsed.
    '''
    value = _get_param(request, name, default_value, required)
    if not isinstance(value, basestring):
        return value

    try:
        result = parse_util.parse_timestamp(value)
        if result:
            return result
        raise
    except:
        raise BadParameter('Invalid ISO timestamp format for parameter: %s' % name)


def parse_duration(request, name, default_value=None, required=True):
    '''Parses a time duration parameter from the given request.

    :param request: The context of an active HTTP request.
    :type request: :class:`rest_framework.request.Request`
    :param name: The name of the parameter to parse.
    :type name: str
    :param default_value: The name of the parameter to parse.
    :type default_value: datetime.timedelta
    :param required: Indicates whether or not the parameter is required. An exception will be raised if the parameter
        does not exist, there is no default value, and required is True.
    :type required: bool
    :returns: The value of the named parameter or the default value if provided.
    :rtype: datetime.timedelta

    :raises :class:`util.rest.BadParameter`: If the value cannot be parsed.
    '''
    value = _get_param(request, name, default_value, required)
    if not isinstance(value, basestring):
        return value

    try:
        result = parse_util.parse_duration(value)
        if result:
            return result
        raise
    except:
        raise BadParameter('Invalid duration format for parameter: %s' % name)


def parse_datetime(request, name, default_value=None, required=True):
    '''Parses a datetime parameter from the given request.

    :param request: The context of an active HTTP request.
    :type request: :class:`rest_framework.request.Request`
    :param name: The name of the parameter to parse.
    :type name: str
    :param default_value: The name of the parameter to parse.
    :type default_value: datetime.datetime
    :param required: Indicates whether or not the parameter is required. An exception will be raised if the parameter
        does not exist, there is no default value, and required is True.
    :type required: bool
    :returns: The value of the named parameter or the default value if provided.
    :rtype: datetime.datetime

    :raises :class:`util.rest.BadParameter`: If the value cannot be parsed.
    '''
    value = _get_param(request, name, default_value, required)
    if not isinstance(value, basestring):
        return value

    try:
        result = parse_util.parse_datetime(value)
        if result:
            return result
        raise
    except ParseError:
        raise BadParameter('Datetime value must include a timezone: %s' % name)
    except:
        raise BadParameter('Invalid datetime format for parameter: %s' % name)


def parse_dict(request, name, default_value=None, required=True):
    '''Parses a dictionary parameter from the given request.

    :param request: The context of an active HTTP request.
    :type request: :class:`rest_framework.request.Request`
    :param name: The name of the parameter to parse.
    :type name: str
    :param default_value: The name of the parameter to parse.
    :type default_value: dict
    :param required: Indicates whether or not the parameter is required. An exception will be raised if the parameter
        does not exist, there is no default value, and required is True.
    :type required: bool
    :returns: The value of the named parameter or the default value if provided.
    :rtype: dict

    :raises :class:`util.rest.BadParameter`: If the value cannot be parsed.
    '''
    value = _get_param(request, name, default_value, required)
    if required and not isinstance(value, dict):
        raise BadParameter(u'Parameter must be a valid JSON object: "%s"' % name)
    return value


def perform_paging(request, objects):
    '''Performs paging on the given objects using the given request parameters

    :param request: The context of an active HTTP request.
    :type request: :class:`rest_framework.request.Request`
    :param objects: List of objects, typically a queryset
    :type objects: list
    :returns: the created page
    :rtype: :class:`django.core.paginator.Page`
    '''
    # TODO: Replace this function with the paging features added to DRF 3.x

    try:
        page = int(request.QUERY_PARAMS.get(u'page', 1))
    except (TypeError, ValueError):
        raise BadParameter(u'"page" must be an integer')
    try:
        page_size = int(request.QUERY_PARAMS.get(u'page_size', 100))
    except (TypeError, ValueError):
        raise BadParameter(u'"page_size" must be an integer')

    if page_size < 1 or page_size > 1000:
        raise BadParameter(u'"page_size" must be between 1 and 1000 inclusive')

    paginator = Paginator(objects, page_size)
    try:
        return paginator.page(page)
    except EmptyPage:
        raise BadParameter(u'Bad "page" number')


def _get_param(request, name, default_value=None, required=True):
    '''Gets a parameter from the given request that works for either read or write operations.

    :param request: The context of an active HTTP request.
    :type request: :class:`rest_framework.request.Request`
    :param name: The name of the parameter to parse.
    :type name: str
    :param default_value: The name of the parameter to parse.
    :type default_value: object
    :param required: Indicates whether or not the parameter is required. An exception will be raised if the parameter
        does not exist, there is no default value, and required is True.
    :type required: bool
    :returns: The value of the named parameter or the default value if provided.
    :rtype: object
    '''
    if name in request.QUERY_PARAMS:
        return request.QUERY_PARAMS.get(name)
    if name in request.DATA:
        return request.DATA.get(name)

    if default_value is not None:
        return default_value

    if required:
        raise BadParameter('Missing required parameter: "%s"' % name)


def _get_param_list(request, name, default_value=None, required=True):
    '''Gets a list of parameters from the given request that works for either read or write operations.

    :param request: The context of an active HTTP request.
    :type request: :class:`rest_framework.request.Request`
    :param name: The name of the parameter to parse.
    :type name: str
    :param default_value: The name of the parameter to parse.
    :type default_value: object
    :returns: A list of the values of the named parameter or the default value if provided.
    :rtype: list[object]
    '''
    if name in request.QUERY_PARAMS:
        return request.QUERY_PARAMS.getlist(name)
    if name in request.DATA:
        return request.DATA.getlist(name)

    if default_value is not None:
        return default_value

    if required:
        raise BadParameter('Missing required parameter: "%s"' % name)
    return []
