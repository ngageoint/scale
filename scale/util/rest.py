"""Defines utilities for building RESTful APIs."""
from __future__ import unicode_literals

import datetime
import uuid

from django.contrib.auth.models import AnonymousUser, User
from django.template.defaultfilters import slugify
import django.utils.timezone as timezone
import rest_framework.pagination as pagination
import rest_framework.renderers as renderers
import rest_framework.serializers as serializers
import rest_framework.status as status
from django.conf import settings
from django.conf.urls import include, url
from rest_framework import permissions
from rest_framework.exceptions import APIException
from rest_framework.settings import api_settings

import util.parse as parse_util


class ScaleAPIPermissions(permissions.BasePermission):
    """
    Verifies that method is permitted to be called.
    Evaluation logic is all methods must be authenticated if PUBLIC_API_READ is False
    SAFE_METHODS will be allowed publicly if PUBLIC_API_READ is True
    POST against validation methods do not require staff user.
    Unsafe methods always require staff user.
    """

    def has_permission(self, request, view):
        if request.user.is_staff:
            return True

        if request.method in permissions.SAFE_METHODS or '/validation' in request.path:
            if settings.PUBLIC_READ_API:
                return True
            elif request.user.is_authenticated:
                return True

        return False

class DefaultPagination(pagination.PageNumberPagination):
    """Default configuration class for the paging system."""
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 1000


class ModelIdSerializer(serializers.Serializer):
    """Converts a model to a lightweight place holder object with only an identifier to REST output"""
    id = serializers.IntegerField()


class PlainTextRenderer(renderers.BaseRenderer):
    """Encodes a string using the requested character set and renders it as text/plain."""
    media_type = 'text/plain'
    format = 'txt'

    def render(self, data, media_type=None, renderer_context=None):
        return data.encode(self.charset)


class BadParameter(APIException):
    """Exception indicating a REST API call contains an invalid value or a missing required parameter."""
    status_code = status.HTTP_400_BAD_REQUEST


class ReadOnly(APIException):
    """Exception indicating a REST API call is attempting to update a field that does not support it."""
    status_code = status.HTTP_400_BAD_REQUEST


def check_update(request, fields):
    """Checks whether the given request includes fields that are not allowed to be updated.

    :param request: The context of an active HTTP request.
    :type request: :class:`rest_framework.request.Request`
    :param fields: A list of field names that are permitted.
    :type fields: [string]
    :returns: True when the request does not include extra fields.
    :rtype: bool

    :raises :class:`util.rest.ReadOnly`: If the request includes unsupported fields to update.
    :raises :class:`exceptions.AssertionError`: If fields in not a list or None.
    """
    fields = fields or []
    assert (isinstance(fields, list))
    extra = filter(lambda x, y=fields: x not in y, request.data.keys())
    if extra:
        raise ReadOnly('Fields do not allow updates: %s' % ', '.join(extra))
    return True


def check_time_range(started, ended, max_duration=None):
    """Checks whether the given time range is valid.

    :param started: The start of a time range.
    :type started: datetime.datetime or None
    :param ended: The end of a time range.
    :type ended: datetime.datetime or None
    :param max_duration: The maximum amount of time between the started and ended range.
    :type max_duration: datetime.timedelta
    :returns: True when the time range is valid.
    :rtype: bool

    :raises :class:`util.rest.BadParameter`: If there is a problem with the time range.
    """
    if not started or not ended:
        return True
    if started == ended:
        raise BadParameter('Start and end values must be different')
    if started > ended:
        raise BadParameter('Start time must come before end time')

    if max_duration:
        duration = ended - started
        if datetime.timedelta(days=0) > duration or max_duration < duration:
            raise BadParameter('Time range must be between 0 and %s' % max_duration)
    return True


def check_together(names, values):
    """Checks whether a list of fields as a group. Either all or none of the fields should be provided.

    :param names: The list of field names to check.
    :type names: [string]
    :param values: The list of field values to check.
    :type values: [object]
    :returns: True when all parameters are provided and false if none of the parameters are provided.
    :rtype: bool

    :raises :class:`util.rest.BadParameter`: If the list of fields is mismatched.
    """
    if not names and not values:
        return False
    if len(names) != len(values):
        raise BadParameter('Field names and values must be the same length')

    provided = 0
    for value in values:
        if value is not None:
            provided += 1
    if provided != 0 and provided != len(values):
        raise BadParameter('Required together: [%s]' % ','.join(names))
    return provided > 0


def has_params(request, *names):
    """Checks whether one or more parameters are included in the request.

    :param request: The context of an active HTTP request.
    :type request: :class:`rest_framework.request.Request`
    :param names: One or more parameter names to check.
    :type names: string
    :returns: True when all the parameters are provided or false if at least one is not provided.
    :rtype: bool
    """
    if not names:
        return False
    for name in names:
        if name not in request.query_params and name not in request.data:
            return False
    return True


def get_relative_days(days):
    """Calculates a relative date/time in the past without any time offsets.

    This is useful when a service wants to have a default value of, for example 7 days back. If an ISO duration format
    is used, such as P7D then the current time will be factored in which results in the earliest day being incomplete
    when computing an absolute time stamp.

    :param days: The number of days back to calculate from now.
    :type days: int
    :returns: An absolute time stamp that is the complete range of relative days back.
    :rtype: datetime.datetime
    """
    base_date = (timezone.now() - datetime.timedelta(days=days)).date()
    return datetime.datetime.combine(base_date, datetime.time.min).replace(tzinfo=timezone.utc)


def get_url(path):
    """Builds an absolute URL from the given path with any required prefixes, such as the default REST API version.

    :param path: A URL path to combine with the default prefix.
    :type path: string
    :returns: The absolute path to use when calling the target URL path.
    :rtype: string
    """
    return '/%s%s' % (api_settings.DEFAULT_VERSION, path)


def get_versioned_urls(apps):
    """Generates a list of URLs for applications with REST APIs

    :param apps: A list of application names to register.
    :type apps: [string]
    :returns: A list of URLs for REST APIs with version prefixes.
    :rtype: [:class:`django.core.urlresolvers.RegexURLPattern`]
    """
    urls = []

    # Check whether the application is configured to use versions
    rest_settings = getattr(settings, 'REST_FRAMEWORK', None)
    if not rest_settings:
        return urls
    allowed_versions = rest_settings.get('ALLOWED_VERSIONS', None)
    if not allowed_versions:
        return urls

    # Generate a URL for each endpoint with a version prefix
    for version in allowed_versions:
        app_urls = []
        for app in apps:
            app_urls.append(url('', include(app + '.urls')))

        urls.append(url(r'^' + version + '/', include(app_urls, namespace=version)))
    return urls


def login_client(client, is_staff=False):
    """Takes a client object and creates a login session, optionally creating a staff user for unsafe methods"""
    User.objects.create_user(username='test', password='user', email='test@empty.com', is_staff=is_staff)
    client.login(username='test', password='user')


def parse_string(request, name, default_value=None, required=True, accepted_values=None):
    """Parses a string parameter from the given request.

    :param request: The context of an active HTTP request.
    :type request: :class:`rest_framework.request.Request`
    :param name: The name of the parameter to parse.
    :type name: string
    :param default_value: The name of the parameter to parse.
    :type default_value: string
    :param required: Indicates whether or not the parameter is required. An exception will be raised if the parameter
        does not exist, there is no default value, and required is True.
    :type required: bool
    :param accepted_values: A list of values that are acceptable for the parameter.
    :type accepted_values: [string]
    :returns: The value of the named parameter or the default value if provided.
    :rtype: string

    :raises :class:`util.rest.BadParameter`: If the value cannot be parsed.
    """
    value = _get_param(request, name, default_value, required)
    _check_accepted_value(name, value, accepted_values)
    return value


def parse_string_list(request, name, default_value=None, required=True, accepted_values=None):
    """Parses a list of string parameters from the given request.

    :param request: The context of an active HTTP request.
    :type request: :class:`rest_framework.request.Request`
    :param name: The name of the parameter to parse.
    :type name: string
    :param default_value: The name of the parameter to parse.
    :type default_value: [string]
    :param required: Indicates whether or not the parameter is required. An exception will be raised if the parameter
        does not exist, there is no default value, and required is True.
    :type required: bool
    :param accepted_values: A list of values that are acceptable for the parameter.
    :type accepted_values: [string]
    :returns: The values of the named parameter or the default values if provided.
    :rtype: [string]

    :raises :class:`util.rest.BadParameter`: If the value cannot be parsed or does not match the validation list.
    """
    values = _get_param_list(request, name, default_value, required)
    _check_accepted_values(name, values, accepted_values)
    return values


def parse_bool(request, name, default_value=None, required=True):
    """Parses a bool parameter from the given request.

    :param request: The context of an active HTTP request.
    :type request: :class:`rest_framework.request.Request`
    :param name: The name of the parameter to parse.
    :type name: string
    :param default_value: The name of the parameter to parse.
    :type default_value: bool
    :param required: Indicates whether or not the parameter is required. An exception will be raised if the parameter
        does not exist, there is no default value, and required is True.
    :type required: bool
    :returns: The value of the named parameter or the default value if provided.
    :rtype: bool

    :raises :class:`util.rest.BadParameter`: If the value cannot be parsed.
    """
    value = _get_param(request, name, default_value, required)
    if not isinstance(value, basestring):
        return value

    value = value.strip().lower()
    if value == 'true' or value == 't' or value == '1':
        return True
    if value == 'false' or value == 'f' or value == '0':
        return False
    raise BadParameter('Parameter must be a valid boolean: "%s"' % name)


def parse_int(request, name, default_value=None, required=True, accepted_values=None):
    """Parses an integer parameter from the given request.

    :param request: The context of an active HTTP request.
    :type request: :class:`rest_framework.request.Request`
    :param name: The name of the parameter to parse.
    :type name: string
    :param default_value: The name of the parameter to parse.
    :type default_value: int
    :param required: Indicates whether or not the parameter is required. An exception will be raised if the parameter
        does not exist, there is no default value, and required is True.
    :type required: bool
    :param accepted_values: A list of values that are acceptable for the parameter.
    :type accepted_values: [int]
    :returns: The value of the named parameter or the default value if provided.
    :rtype: int

    :raises :class:`util.rest.BadParameter`: If the value cannot be parsed.
    """
    value = _get_param(request, name, default_value, required)
    if not isinstance(value, basestring):
        return value

    try:
        result = int(value)
        _check_accepted_value(name, result, accepted_values)
        return result
    except (TypeError, ValueError):
        raise BadParameter('Parameter must be a valid integer: "%s"' % name)


def parse_int_list(request, name, default_value=None, required=True, accepted_values=None):
    """Parses a list of int parameters from the given request.

    :param request: The context of an active HTTP request.
    :type request: :class:`rest_framework.request.Request`
    :param name: The name of the parameter to parse.
    :type name: string
    :param default_value: The name of the parameter to parse.
    :type default_value: [int]
    :param required: Indicates whether or not the parameter is required. An exception will be raised if the parameter
        does not exist, there is no default value, and required is True.
    :type required: bool
    :param accepted_values: A list of values that are acceptable for the parameter.
    :type accepted_values: [int]
    :returns: The values of the named parameter or the default values if provided.
    :rtype: [int]

    :raises :class:`util.rest.BadParameter`: If the value cannot be parsed or does not match the validation list.
    """
    param_list = _get_param_list(request, name, default_value, required)

    if param_list and len(param_list):
        values = []
        for param in param_list:
            try:
                values.append(int(param))
            except (TypeError, ValueError):
                raise BadParameter('Parameter must be a valid integer: "%s"' % name)
        _check_accepted_values(name, values, accepted_values)
        return values
    return param_list


def parse_float(request, name, default_value=None, required=True, accepted_values=None):
    """Parses a floating point parameter from the given request.

    :param request: The context of an active HTTP request.
    :type request: :class:`rest_framework.request.Request`
    :param name: The name of the parameter to parse.
    :type name: string
    :param default_value: The name of the parameter to parse.
    :type default_value: float
    :param required: Indicates whether or not the parameter is required. An exception will be raised if the parameter
        does not exist, there is no default value, and required is True.
    :type required: bool
    :param accepted_values: A list of values that are acceptable for the parameter.
    :type accepted_values: [float]
    :returns: The value of the named parameter or the default value if provided.
    :rtype: float

    :raises :class:`util.rest.BadParameter`: If the value cannot be parsed.
    """
    value = _get_param(request, name, default_value, required)
    if not isinstance(value, basestring):
        return value

    try:
        result = float(value)
        _check_accepted_value(name, result, accepted_values)
        return result
    except (TypeError, ValueError):
        raise BadParameter('Parameter must be a valid float: "%s"' % name)


def parse_timestamp(request, name, default_value=None, required=True):
    """Parses any valid ISO datetime, duration, or timestamp parameter from the given request.

    :param request: The context of an active HTTP request.
    :type request: :class:`rest_framework.request.Request`
    :param name: The name of the parameter to parse.
    :type name: string
    :param default_value: The name of the parameter to parse.
    :type default_value: datetime.datetime or datetime.timedelta or string
    :param required: Indicates whether or not the parameter is required. An exception will be raised if the parameter
        does not exist, there is no default value, and required is True.
    :type required: bool
    :returns: The value of the named parameter or the default value if provided.
    :rtype: datetime.datetime

    :raises :class:`util.rest.BadParameter`: If the value cannot be parsed.
    """
    value = _get_param(request, name, default_value, required)
    if not isinstance(value, basestring):
        return value

    try:
        result = parse_util.parse_timestamp(value)
        if result:
            return result
        raise BadParameter('Did not parse a result for parameter: %s' % name)
    except:
        raise BadParameter('Invalid ISO timestamp format for parameter: %s' % name)


def parse_duration(request, name, default_value=None, required=True):
    """Parses a time duration parameter from the given request.

    :param request: The context of an active HTTP request.
    :type request: :class:`rest_framework.request.Request`
    :param name: The name of the parameter to parse.
    :type name: string
    :param default_value: The name of the parameter to parse.
    :type default_value: datetime.timedelta or string
    :param required: Indicates whether or not the parameter is required. An exception will be raised if the parameter
        does not exist, there is no default value, and required is True.
    :type required: bool
    :returns: The value of the named parameter or the default value if provided.
    :rtype: datetime.timedelta

    :raises :class:`util.rest.BadParameter`: If the value cannot be parsed.
    """
    value = _get_param(request, name, default_value, required)
    if not isinstance(value, basestring):
        return value

    try:
        result = parse_util.parse_duration(value)
        if result:
            return result
        raise BadParameter('Did not parse a result for parameter: %s' % name)
    except:
        raise BadParameter('Invalid duration format for parameter: %s' % name)


def parse_datetime(request, name, default_value=None, required=True):
    """Parses a datetime parameter from the given request.

    :param request: The context of an active HTTP request.
    :type request: :class:`rest_framework.request.Request`
    :param name: The name of the parameter to parse.
    :type name: string
    :param default_value: The name of the parameter to parse.
    :type default_value: datetime.datetime
    :param required: Indicates whether or not the parameter is required. An exception will be raised if the parameter
        does not exist, there is no default value, and required is True.
    :type required: bool
    :returns: The value of the named parameter or the default value if provided.
    :rtype: datetime.datetime

    :raises :class:`util.rest.BadParameter`: If the value cannot be parsed.
    """
    value = _get_param(request, name, default_value, required)
    if not isinstance(value, basestring):
        return value

    try:
        result = parse_util.parse_datetime(value)
        if result:
            return result
        raise BadParameter('Did not parse a result for parameter: %s' % name)
    except:
        raise BadParameter('Datetime values must follow ISO-8601 and include a timezone: %s' % name)


def parse_dict(request, name, default_value=None, required=True):
    """Parses a dictionary parameter from the given request.

    :param request: The context of an active HTTP request.
    :type request: :class:`rest_framework.request.Request`
    :param name: The name of the parameter to parse.
    :type name: string
    :param default_value: The name of the parameter to parse.
    :type default_value: dict
    :param required: Indicates whether or not the parameter is required. An exception will be raised if the parameter
        does not exist, there is no default value, and required is True.
    :type required: bool
    :returns: The value of the named parameter or the default value if provided.
    :rtype: dict

    :raises :class:`util.rest.BadParameter`: If the value cannot be parsed.
    """
    value = _get_param(request, name, default_value, required)
    if required and not isinstance(value, dict):
        raise BadParameter('Parameter must be a valid JSON object: "%s"' % name)
    return value or {}

def parse_dict_list(request, name, default_value=None, required=True):
    """Parses a list of dictionary parameters from the given request.

    :param request: The context of an active HTTP request.
    :type request: :class:`rest_framework.request.Request`
    :param name: The name of the parameter to parse.
    :type name: string
    :param default_value: The name of the parameter to parse.
    :type default_value: dict
    :param required: Indicates whether or not the parameter is required. An exception will be raised if the parameter
        does not exist, there is no default value, and required is True.
    :type required: bool
    :returns: The value of the named parameter or the default value if provided.
    :rtype: [dict]

    :raises :class:`util.rest.BadParameter`: If the value cannot be parsed.
    """

    param_list = _get_param_list(request, name, default_value, required)

    if param_list and len(param_list):
        for param in param_list:
            if not isinstance(param, dict):
                raise BadParameter('Parameter must be a valid JSON object: "%s"' % name)
    return param_list or []

def title_to_name(queryset, title):
    """Generates an identifying name for a model from a human readable title

    :param request: The context of an active HTTP request.
    :type request: :class:`rest_framework.request.Request`
    :param title: The title to convert
    :type title: string
    :returns: The generated identifying name.
    :rtype: string
    
    :raises :class:`Exception`: If unable to generate a unique name.
    """

    name = title_to_basename(title)
    basename = name
    
    index = 0
    while queryset != None and queryset.filter(name=name).count() > 0:
        name = basename + '-' + uuid.uuid4().hex[:19]
        if index > 999:
            raise Exception('Unable to find a unique name. Exiting to prevent infinite loop.')
        
    return name
    
def title_to_basename(title):
    """Generates an identifying basename for a model from a human readable title

    :param title: The title to convert
    :type title: string
    :returns: The generated identifying name.
    :rtype: string
    """
    
    name = slugify(title)
    name = name.replace('_', '-')
    name = name[:30]
    basename = name
    
    return basename
    
    
def strip_schema_version(json_dict):
    """Returns the given JSON dict after stripping its schema version out

    :param json_dict: The JSON dict
    :type json_dict: dict
    :returns: The JSON dict with its schema version stripped out
    :rtype: dict
    """

    if 'version' in json_dict:
        del json_dict['version']
    return json_dict


def _get_param(request, name, default_value=None, required=True):
    """Gets a parameter from the given request that works for either read or write operations.

    :param request: The context of an active HTTP request.
    :type request: :class:`rest_framework.request.Request`
    :param name: The name of the parameter to parse.
    :type name: string
    :param default_value: The name of the parameter to parse.
    :type default_value: object
    :param required: Indicates whether or not the parameter is required. An exception will be raised if the parameter
        does not exist, there is no default value, and required is True.
    :type required: bool
    :returns: The value of the named parameter or the default value if provided.
    :rtype: object
    """
    value = None
    if name in request.query_params:
        value = request.query_params.get(name)
    if value is None and name in request.data:
        value = request.data.get(name)

    if value is None and default_value is not None:
        return default_value

    if value is None and required:
        raise BadParameter('Missing required parameter: "%s"' % name)
    return value


def _get_param_list(request, name, default_value=None, required=True):
    """Gets a list of parameters from the given request that works for either read or write operations.

    :param request: The context of an active HTTP request.
    :type request: :class:`rest_framework.request.Request`
    :param name: The name of the parameter to parse.
    :type name: string
    :param default_value: The name of the parameter to parse.
    :type default_value: object
    :returns: A list of the values of the named parameter or the default value if provided.
    :rtype: [object]
    """
    value = None
    if name in request.query_params:
        value = request.query_params.getlist(name)
    if value is None and name in request.data:
        value = request.data.get(name)

    if value is None and default_value is not None:
        return default_value

    if value is None and required:
        raise BadParameter('Missing required parameter: "%s"' % name)
        
    if value and not isinstance(value, list):
        value = [value]
    return value or []


def _check_accepted_value(name, value, accepted_values):
    """Checks that a parameter has a value that is acceptable.

    :param name: The name of the parameter.
    :type name: string
    :param value: A value to validate.
    :type value: object
    :param accepted_values: A list of values that are acceptable for the parameter.
    :type accepted_values: [object]
    """
    if value and accepted_values:
        if value not in accepted_values:
            raise BadParameter('Parameter "%s" values must be one of: %s' % (name, accepted_values))


def _check_accepted_values(name, values, accepted_values):
    """Checks that a list of parameters has values that are acceptable.

    :param name: The name of the parameter.
    :type name: string
    :param values: A list of values to validate.
    :type values: [object]
    :param accepted_values: A list of values that are acceptable for the parameter.
    :type accepted_values: [object]
    """
    if values and accepted_values:
        for value in values:
            _check_accepted_value(name, value, accepted_values)
