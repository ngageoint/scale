"""Defines the interface for executing a job"""
from __future__ import unicode_literals

import json
import logging
from copy import deepcopy

import os

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from job.seed.exceptions import InvalidSeedMetadataDefinition

logger = logging.getLogger(__name__)

SCHEMA_FILENAME = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'schema/seed.metadata.schema.json')
with open(SCHEMA_FILENAME) as schema_file:
    METADATA_SCHEMA = json.load(schema_file)
METADATA_SUFFIX = '.metadata.json'

UNSUPPORTED_TYPES = ('FeatureCollection', 'GeometryCollection')


class SeedMetadata(object):
    """Represents the extended metadata for a single file in Seed job.

    Object instantiation from existing JSON should be accomplished via the metadata_from json helper.
    This will safeguard us from having to deal with FeatureCollection and GeometryCollection objects."""

    def __init__(self):
        """Initialize the metadata object with a basic placeholder"""

        self._data = {
            'type': 'Feature',
            'geometry': None,
            'properties': None
        }

    @staticmethod
    def metadata_from_json(metadata, do_validate=True):
        """Creates a metadata object from the given definition. If the definition is invalid, a
        :class:`job.seed.exceptions.InvalidSeedMetadataDefinition` exception will be thrown.

        :param metadata: The metadata definition
        :type metadata: dict
        :param do_validate: Whether to perform validation on the JSON schema
        :type do_validate: bool
        :raises InvalidSeedMetadataDefinition: If schema validation fails
        """

        self = SeedMetadata()

        try:
            if do_validate:
                validate(metadata, METADATA_SCHEMA)
        except ValidationError as validation_error:
            raise InvalidSeedMetadataDefinition('JSON_VALIDATION_ERROR', 'Error validating against schema: %s' %
                                                validation_error)
        if metadata['type'] in UNSUPPORTED_TYPES:
            raise InvalidSeedMetadataDefinition('UNSUPPORTED_GEOJSON', 'Scale does not process GeoJSON '
                                                                       'FeatureCollection or GeometryCollection type')
        # Ensure we never have to deal with anything but sanitized Feature GeoJSON objects
        if metadata['type'] != 'Feature':
            self._data['geometry'] = metadata
        else:
            self._data = metadata

        return self

    @property
    def properties(self):
        """Retrieves a valid properties dictionary

        :return: Properties found within metadata file
        :rtype: dict
        """

        self._data.setdefault('properties', {})
        if self._data['properties'] is None:
            self._data['properties'] = {}

        return self._data['properties']

    @property
    def data(self):
        """Retrieves the internal dictionary of GeoJSON"""

        return deepcopy(self._data)

    def get_property(self, key):
        return self.properties.get(key)

    def set_property(self, key, value):
        self.properties[key] = value