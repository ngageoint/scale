"""Defines the configuration for a mount that will be mounted into a job's container"""
from __future__ import unicode_literals

import os
from abc import ABCMeta

from job.configuration.exceptions import InvalidJobConfiguration
from job.configuration.volume import HOST_TYPE, VOLUME_TYPE


class MountConfig(object):
    """Defines the configuration for a job's mount
    """

    __metaclass__ = ABCMeta

    def __init__(self, name, mount_type):
        """Creates a mount configuration

        :param name: The name of the mount
        :type name: string
        :param mount_type: The type of the mount
        :type mount_type: string
        """

        self.name = name
        self.mount_type = mount_type

    def validate(self):
        """Validates this mount configuration

        :returns: A list of warnings discovered during validation
        :rtype: list

        :raises :class:`job.configuration.exceptions.InvalidJobConfiguration`: If the configuration is invalid
        """

        return []


class HostMountConfig(MountConfig):
    """Defines the configuration for a host mount
    """

    def __init__(self, name, host_path):
        """Creates a host mount configuration

        :param name: The name of the mount
        :type name: string
        :param host_path: The path on the host to be mounted into the container
        :type host_path: string
        """

        super(HostMountConfig, self).__init__(name, HOST_TYPE)

        self.host_path = host_path

    def validate(self):
        """See :meth:`job.configuration.mount.MountConfig.validate`
        """

        warnings = super(HostMountConfig, self).validate()

        if not os.path.isabs(self.host_path):
            msg = 'Host mount %s must use an absolute host path'
            raise InvalidJobConfiguration('HOST_ABSOLUTE_PATH', msg % self.name)

        return warnings


class VolumeMountConfig(MountConfig):
    """Defines the configuration for a volume mount
    """

    def __init__(self, name, driver=None, driver_opts=None):
        """Creates a volume mount configuration

        :param name: The name of the volume
        :type name: string
        :param driver: The volume driver to use
        :type driver: string
        :param driver_opts: The driver options to use
        :type driver_opts: dict
        """

        super(VolumeMountConfig, self).__init__(name, VOLUME_TYPE)

        self.driver = driver if driver else None
        self.driver_opts = driver_opts if driver_opts else {}
