"""Defines the JSON schema for a set of resources"""
from __future__ import unicode_literals

import logging

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from node.resources.exceptions import InvalidResources
from node.resources.node_resources import NodeResources
from node.resources.resource import ScalarResource

logger = logging.getLogger(__name__)

SCHEMA_VERSION = '1.0'

RESOURCES_SCHEMA = {
    'type': 'object',
    'additionalProperties': False,
    'properties': {
        'version': {
            'description': 'Version of the resources schema',
            'type': 'string',
            'default': SCHEMA_VERSION,
            'pattern': '^.{0,50}$',
        },
        'resources': {
            'description': 'Defines the resource values',
            'type': 'object',
            'additionalProperties': {
                'type': 'number',
            },
        },
    },
}


class Resources(object):
    """Represents the schema for a set of resources"""

    def __init__(self, resources=None, validate=True):
        """Creates a resources object from the given dict

        :param resources: The resources dict
        :type resources: dict
        :param validate: Whether to perform validation on the JSON schema
        :type validate: bool

        :raises :class:`node.resources.exceptions.InvalidResources`: If the given resources dict is invalid
        """

        if resources is None:
            resources = {}

        self._resources = resources

        if 'version' not in self._resources:
            self._resources['version'] = SCHEMA_VERSION
        if self._resources['version'] != SCHEMA_VERSION:
            raise InvalidResources('%s is an invalid version' % self._resources['version'])

        try:
            if validate:
                validate(resources, RESOURCES_SCHEMA)
        except ValidationError as validation_error:
            raise InvalidResources(validation_error)

        self._populate_default_values()

    def get_dict(self):
        """Returns the internal dictionary representing these resources

        :returns: The internal dictionary
        :rtype: dict
        """

        return self._resources

    def get_node_resources(self):
        """Returns the node resources represented by this schema

        :returns: The node resources
        :rtype: :class:`node.resources.NodeResources`
        """

        resource_list = []
        for name, value in self._resources['resources'].items():
            resource_list.append(ScalarResource(name, float(value)))
        return NodeResources(resource_list)

    def _populate_default_values(self):
        """Populates any missing default values"""

        if 'resources' not in self._resources:
            self._resources['resources'] = {}
