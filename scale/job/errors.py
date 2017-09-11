"""Defines functions for getting basic job errors"""
from __future__ import unicode_literals

from error.models import Error


def get_invalid_manifest_error():
    """Returns the error for invalid results manifest

    :returns: The invalid results error
    :rtype: :class:`error.models.Error`
    """
    return Error.objects.get_error('invalid-results-manifest')


def get_missing_output_error():
    """Returns the error for missing a required output

    :returns: The missing output error
    :rtype: :class:`error.models.Error`
    """

    return Error.objects.get_error('missing-required-output')
