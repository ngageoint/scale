"""Manages the v6 batch configuration schema"""
from __future__ import unicode_literals

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from batch.configuration.configuration import BatchConfiguration
from batch.configuration.exceptions import InvalidConfiguration


SCHEMA_VERSION = '6'

BATCH_CONFIGURATION_SCHEMA = {
    'type': 'object',
    'required': ['version'],
    'additionalProperties': False,
    'properties': {
        'version': {
            'description': 'Version of the batch configuration schema',
            'type': 'string',
        },
        'priority': {
            'description': 'The ID of the previous batch',
            'type': 'integer',
        }
    },
}


def convert_configuration_to_v6(configuration):
    """Returns the v6 configuration JSON for the given batch configuration

    :param configuration: The batch configuration
    :type configuration: :class:`batch.configuration.configuration.BatchConfiguration`
    :returns: The v6 configuration JSON
    :rtype: :class:`batch.configuration.json.configuration_v6.BatchConfigurationV6`
    """

    json_dict = {'version': '6'}
    if configuration.priority is not None:
        json_dict['priority'] = configuration.priority
    return BatchConfigurationV6(configuration=json_dict, do_validate=False)


class BatchConfigurationV6(object):
    """Represents a v6 configuration JSON for a batch"""

    def __init__(self, configuration=None, do_validate=False):
        """Creates a v6 batch configuration JSON object from the given dictionary

        :param configuration: The batch configuration JSON dict
        :type configuration: dict
        :param do_validate: Whether to perform validation on the JSON schema
        :type do_validate: bool

        :raises :class:`batch.configuration.exceptions.InvalidConfiguration`: If the given configuration is invalid
        """

        if not configuration:
            configuration = {}
        self._configuration = configuration

        if 'version' not in self._configuration:
            self._configuration['version'] = SCHEMA_VERSION

        if self._configuration['version'] != SCHEMA_VERSION:
            msg = '%s is an unsupported version number' % self._configuration['version']
            raise InvalidConfiguration('INVALID_BATCH_CONFIGURATION', msg)

        try:
            if do_validate:
                validate(self._configuration, BATCH_CONFIGURATION_SCHEMA)
        except ValidationError as ex:
            raise InvalidConfiguration('INVALID_BATCH_CONFIGURATION', 'Invalid batch configuration: %s' % unicode(ex))

    def get_configuration(self):
        """Returns the batch configuration represented by this JSON

        :returns: The batch configuration
        :rtype: :class:`batch.configuration.configuration.BatchConfiguration`:
        """

        configuration = BatchConfiguration()
        if 'priority' in self._configuration:
            configuration.priority = self._configuration['priority']

        return configuration

    def get_dict(self):
        """Returns the internal dictionary

        :returns: The internal dictionary
        :rtype: dict
        """

        return self._configuration
