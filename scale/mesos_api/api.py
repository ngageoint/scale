from __future__ import unicode_literals

import json
import logging
import re
import urllib
import urllib2

logger = logging.getLogger(__name__)

PORT_REGEX = re.compile(r'.*?\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:(\d+)')


class MesosError(Exception):
    """Error when there is a problem fetching results from the Mesos REST API"""
    pass


class HardwareResources(object):
    """Represents hardware resource metrics for a host.

    :keyword cpus: The number of processing units.
    :type cpus: float
    :keyword mem: The amount of memory in MiB.
    :type mem: float
    :keyword disk: The amount of disk space in MiB.
    :type disk: float
    """
    def __init__(self, cpus=0.0, mem=0.0, disk=0.0):
        self.cpus = cpus
        self.mem = mem
        self.disk = disk

    def to_dict(self):
        """Converts this object to a dictionary representation.

        :returns: All of the object attributes formatted as a dictionary.
        :rtype: dict
        """
        return {
            'cpus': round(self.cpus, 1),
            'mem': round(self.mem, 1),
            'disk': round(self.disk, 1),
        }


class SlaveInfo(object):
    """Represents information about a host system.

    :keyword hostname: The network name of the host.
    :type hostname: string
    :keyword port: The network port of the host.
    :type port: int
    :keyword total: The total hardware resources available to the host.
    :type total: :class:`mesos_api.api.HardwareResources`
    :keyword scheduled: The hardware resources allocated for potential use by the host.
    :type scheduled: :class:`mesos_api.api.HardwareResources`
    :keyword used: The hardware resources actively being used by the host.
    :type used: :class:`mesos_api.api.HardwareResources`
    :keyword slave_id: The ID of the slave.
    :type slave_id: string
    """
    def __init__(self, hostname=None, port=0, total=None, scheduled=None, used=None, slave_id=None):
        self.slave_id = slave_id
        self.hostname = hostname
        self.port = port
        self.total = total
        self.scheduled = scheduled
        self.used = used

    def to_dict(self):
        """Converts this object to a dictionary representation.

        :returns: All of the object attributes formatted as a dictionary.
        :rtype: dict
        """
        result = {
            'hostname': self.hostname,
            'port': self.port,
            'resources': {
                'total': self.total.to_dict() if self.total else None,
                'scheduled': self.scheduled.to_dict() if self.scheduled else None,
                'used': self.used.to_dict() if self.used else None,
            }
        }

        # TODO: Remove theses resource values once the UI is migrated to the nested structures
        if self.total:
            result['resources'].update(self.total.to_dict()),
        return result
