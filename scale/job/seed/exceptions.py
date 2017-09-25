"""Defines exceptions that can occur when interacting with a Seed job interface"""
from __future__ import unicode_literals


class InvalidSeedManifestDefinition(Exception):
    """Exception indicating that the provided definition of a Seed Manifest was invalid
    """
    pass


class InvalidSeedMetadataDefinition(Exception):
    """Exception indicating that the provided definition of a Seed Metadata was invalid
    """
    pass
