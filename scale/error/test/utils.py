"""Defines utility methods for testing errors"""
from __future__ import unicode_literals

from error.models import Error

NAME_COUNTER = 1


def create_error(name=None, title=None, description='Test error description', category='SYSTEM', is_builtin=False):
    """Creates a error model for unit testing

    :returns: The error model
    :rtype: :class:`error.models.Error`
    """

    if not name:
        global NAME_COUNTER
        name = u'error-%i' % NAME_COUNTER
        NAME_COUNTER += 1

    return Error.objects.create(name=name, title=title, description=description, category=category,
                                is_builtin=is_builtin)
