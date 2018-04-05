"""Defines exceptions that can occur when interacting with a Seed job interface"""
from __future__ import unicode_literals

from rest_framework import status
from rest_framework.exceptions import APIException


class InvalidSeedManifestDefinition(APIException):
    """Exception indicating that the provided definition of a Seed Manifest was invalid
    """
    status_code = status.HTTP_400_BAD_REQUEST

    pass


class InvalidSeedMetadataDefinition(Exception):
    """Exception indicating that the provided definition of a Seed Metadata was invalid
    """
    pass
