"""Defines exceptions that can occur when interacting with jobs and job types"""
from __future__ import unicode_literals


class InvalidJobField(Exception):
    """Exception indicating that a job type or job field was given an invalid value
    """

    pass

class NonSeedJobType(Exception):
    """Exception indicating that a job type is not a seed job type
    """
    pass

class InactiveJobType(Exception):
    """Exception indicating that a job type is inactive
    """
    pass