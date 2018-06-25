"""Defines the interface for executing a job"""
from __future__ import unicode_literals

import json
import logging
import os

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from job.seed.exceptions import InvalidSeedMetadataDefinition

logger = logging.getLogger(__name__)

SCHEMA_FILENAME = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'schema/seed.metadata.schema.json')
with open(SCHEMA_FILENAME) as schema_file:
    METADATA_SCHEMA = json.load(schema_file)
METADATA_SUFFIX = '.metadata.json'


class SeedMetadata(object):
    """Represents the extended metadata for a single file captured from a Seed job"""

    def __init__(self, definition, do_validate=True):
        """Creates a metadata class from the given definition. If the definition is invalid, a
        :class:`job.configuration.interface.exceptions.InvalidMetadataDefinition` exception will be thrown.

        :param definition: The interface definition
        :type definition: dict
        :param do_validate: Whether to perform validation on the JSON schema
        :type do_validate: bool
        """

        self.definition = definition

        try:
            if do_validate:
                validate(definition, METADATA_SCHEMA)
        except ValidationError as validation_error:
            raise InvalidSeedMetadataDefinition(validation_error)

        self._populate_default_values()

    def get_geometry(self):
        """Retrieves GeoJSON geometry if it is available in metadata object

        :return: Geometry as defined by GeoJSON specification, possibly None if unset
        :rtype: dict or None
        """
        geometry = None

        if 'geometry' in self.definition:
            geometry = self.definition['geometry']

        return geometry

    def get_time(self):
        """Retrieves Timestamp of data if it is available in metadata object

        :return: Timestamp as defined in ISO8601 string format, possibly None if unset
        :rtype: dict or None
        """

        timestamp = None

        if 'time' in self.definition:
            timestamp = self.definition['time']

        return timestamp
