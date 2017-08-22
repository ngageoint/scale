"""Defines exceptions that can occur when interacting with job executions"""
from __future__ import unicode_literals


class InvalidTaskResults(Exception):
    """Exception indicating that the provided task results JSON was invalid
    """

    pass
