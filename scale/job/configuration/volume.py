"""Defines a Docker volume that will be mounted into a container"""
from __future__ import unicode_literals

from job.configuration.docker_param import DockerParameter

MODE_RO = 'ro'
MODE_RW = 'rw'


class Volume(object):
    """Defines a Docker volume that will be mounted into a container
    """

    def __init__(self, name, container_path, mode, is_host=True, host_path=None, driver=None, driver_opts=None):
        """Creates a volume to be mounted into a container

        :param name: The name of the volume
        :type name: string
        :param container_path: The path within the container onto which the volume will be mounted
        :type container_path: string
        :param mode: Either 'ro' for read-only or 'rw' for read-write
        :type mode: string
        :param is_host: True if this is a host mount, False if this is a normal volume
        :type is_host: bool
        :param host_path: The path on the host to mount into the container
        :type host_path: string
        :param driver: The volume driver to use
        :type driver: string
        :param driver_opts: The driver options to use
        :type driver_opts: dict
        """

        self.name = name
        self.container_path = container_path
        self.mode = mode
        self.is_host = is_host
        self.host_path = host_path
        self.driver = driver
        self.driver_opts = driver_opts

    def to_docker_param(self, is_created):
        """Returns a Docker parameter that will perform the mount of this volume

        :param is_created: Whether this volume has already been created
        :type is_created: bool
        :returns: The Docker parameter that will mount this volume
        :rtype: :class:`job.configuration.docker_param.DockerParameter`
        """

        if self.is_host:
            # Host mount is special, use host path for volume name
            volume_name = self.host_path
        else:
            # TODO: this is a hack, right now embedding volume create commands will fail when passed through Mesos, this
            # means that we need to just have Docker create the volumes implicitly with no driver or opt params
            # available to us
            is_created = True

            if is_created:
                # Re-use existing volume
                volume_name = self.name
            else:
                # Create named volume, possibly with driver and driver options
                driver_params = []
                if self.driver:
                    driver_params.append('--driver %s' % self.driver)
                if self.driver_opts:
                    for name, value in self.driver_opts.iteritems():
                        driver_params.append('--opt %s=%s' % (name, value))
                if driver_params:
                    volume_name = '$(docker volume create --name %s %s)' % (self.name, ' '.join(driver_params))
                else:
                    volume_name = '$(docker volume create --name %s)' % self.name

        volume_param = '%s:%s:%s' % (volume_name, self.container_path, self.mode)
        return DockerParameter('volume', volume_param)
