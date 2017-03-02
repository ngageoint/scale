"""Defines utility functions for parsing data."""
from __future__ import unicode_literals

import datetime
import re

import django.utils.dateparse as dateparse
import django.utils.six as six
import django.utils.timezone as timezone

iso8601_duration_re = re.compile(
    r'^P'
    r'(?:(?P<days>\d+(.\d+)?)D)?'
    r'(?:T'
    r'(?:(?P<hours>\d+(.\d+)?)H)?'
    r'(?:(?P<minutes>\d+(.\d+)?)M)?'
    r'(?:(?P<seconds>\d+(.\d+)?)S)?'
    r')?'
    r'$'
)


# TODO The following is from the Django 1.8 django.utils.dateparse, we can remove this when upgrading.
def parse_duration(value):
    """Parses a duration string and returns a datetime.timedelta.
    Unlike the standard Django 1.8 function, this only accepts ISO 8601 durations.
    """
    match = iso8601_duration_re.match(value)
    if match:
        kw = match.groupdict()
        kw = {k: float(v) for k, v in six.iteritems(kw) if v is not None}
        return datetime.timedelta(**kw)


# Hack to fix ISO8601 for datetime filters.
# This should be taken care of by a future Django fix.  And might even be handled
# by a newer version of django-rest-framework.  Unfortunately, both of these solutions
# will accept datetimes without timezone information which we do not want to allow
# see https://code.djangoproject.com/tickets/23448
# Solution modified from http://akinfold.blogspot.com/2012/12/datetimefield-doesnt-accept-iso-8601.html
def parse_datetime(value):
    if 'Z' not in value and '+' not in value:
        raise ValueError('Datetime value must include a timezone: %s' % value)
    return dateparse.parse_datetime(value)


def parse_timestamp(value):
    """Parses any valid ISO date/time, duration, or timestamp.

    :param value: The raw string value to parse.
    :type value: str
    :returns: The result of parsing the given string value.
    :rtype: datetime.datetime
    """
    if value and value.startswith('P'):
        return timezone.now() - parse_duration(value)
    return parse_datetime(value)
