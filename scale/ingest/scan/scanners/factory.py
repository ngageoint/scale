"""Defines the factory for creating monitors"""
from __future__ import unicode_literals

import logging
logger = logging.getLogger(__name__)

_SCANNERS = {}



def add_scanner_type(scanner_class):
    """Registers a scanner class so it can be used for Scale Scans

    :param scanner_class: The class definition for a scanner
    :type scanner_class: class:`ingest.scan.scanners.scanner.Scanner`
    """

    scanner = scanner_class()
    if scanner.scanner_type in _SCANNERS:
        logger.warning('Duplicate scanner registration: %s', scanner.scanner_type)
    _SCANNERS[scanner.scanner_type] = scanner_class


def get_scanner(scanner_type):
    """Returns a scanner of the given type that is set to scan the given workspace

    :param scanner_type: The unique identifier of a registered scanner
    :type scanner_type: string
    :returns: A scanner for storing and retrieving files.
    :rtype: :class:`ingest.scan.scanners.scanner.Scanner`
    """

    if scanner_type in _SCANNERS:
        return _SCANNERS[scanner_type]()
    raise KeyError('\'%s\' is an invalid scanner type' % scanner_type)


def get_scanner_types():
    """Returns a list of type identifiers for all registered scanners

    :returns: A list of scanner types
    :rtype: [string]
    """

    return _SCANNERS.keys()
