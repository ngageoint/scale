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


class SchedulerInfo(object):
    """Represents summary information about a host system.

    :keyword is_online: True if the system is online, False otherwise.
    :type is_online: bool
    :keyword total: The total hardware resources available to the system.
    :type total: :class:`mesos_api.api.HardwareResources`
    :keyword scheduled: The hardware resources allocated for potential use by the system.
    :type scheduled: :class:`mesos_api.api.HardwareResources`
    :keyword used: The hardware resources actively being used by the system.
    :type used: :class:`mesos_api.api.HardwareResources`
    """
    def __init__(self, hostname, is_online, total=None, scheduled=None, used=None):
        self.hostname = hostname
        self.is_online = is_online
        self.total = total
        self.scheduled = scheduled
        self.used = used

    def to_dict(self):
        """Converts this object to a dictionary representation.

        :returns: All of the object attributes formatted as a dictionary.
        :rtype: dict
        """
        return {
            'hostname': self.hostname,
            'is_online': self.is_online,
            'resources': {
                'total': self.total.to_dict() if self.total else None,
                'scheduled': self.scheduled.to_dict() if self.scheduled else None,
                'used': self.used.to_dict() if self.used else None,
            }
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


def get_scheduler(hostname, port):
    """Queries the Mesos master REST API to get hardware resource usage for the entire cluster

    :param hostname: The hostname of the master
    :type hostname: str
    :param port: The port of the master
    :type port: int
    :returns: A summary of resource utilization and allocation for the cluster scheduler
    :rtype: :class:`mesos_api.api.SchedulerInfo`
    """

    # Fetch raw status information from the Mesos API
    try:
        url = 'http://%s:%i/master/state.json' % (hostname, port)
        response = urllib2.urlopen(url)
        if response.code != 200:
            raise MesosError('Failed to read response from master: %s:%i' % (hostname, port))
        state_dict = json.load(response)
    except MesosError:
        logger.exception('Mesos API returned unexpected status code: %s:%i -> %i' % (hostname, port, response.code))
        raise
    except:
        logger.exception('Mesos API unavailable: %s:%i' % (hostname, port))
        raise MesosError('Failed to connect to master: %s:%i' % (hostname, port))

    # Compute the total resources available to the cluster
    # We could use the /metrics/snapshot URL, but we compute the values here to avoid the extra call
    total = HardwareResources()
    for slave_dict in state_dict['slaves']:
        res_dict = slave_dict['resources']
        if res_dict:
            total.cpus += float(res_dict['cpus'])
            total.mem += float(res_dict['mem'])
            total.disk += float(res_dict['disk'])

    # Figure out scheduler and resource allocation from the framework
    fw_dict, online = _get_framework(state_dict)
    if fw_dict:
        hostname = fw_dict['hostname']

        # Mesos labels resources allocated for work as "used", but we refer to that as "scheduled"
        sched_dict = fw_dict['used_resources']
        scheduled = HardwareResources(float(sched_dict['cpus']), float(sched_dict['mem']), float(sched_dict['disk']))
    else:
        hostname = None
        scheduled = HardwareResources()

    # TODO Mesos only provides true real-time usage if we query each slave individually
    used = HardwareResources()

    return SchedulerInfo(hostname, online, total, scheduled, used)


def get_slaves(hostname, port):
    """Queries the Mesos master REST API to get information for all registered slaves.

    :param hostname: The hostname of the master
    :type hostname: str
    :param port: The port of the master
    :type port: int
    :returns: A list of slave information.
    :rtype: list[:class:`mesos_api.api.SlaveInfo`]
    :raises MesosError: If the slave cannot be found
    """
    slaves_dict = _get_slaves_dict(hostname, port)
    return [_parse_slave_info(s) for s in slaves_dict]


def get_slave(hostname, port, slave_id, resources=False):
    """Queries the Mesos master REST API to get information for the given slave

    :param hostname: The hostname of the master
    :type hostname: str
    :param port: The port of the master
    :type port: int
    :param slave_id: The ID of the slave
    :type slave_id: str
    :returns: A summary of the slave information
    :rtype: :class:`mesos_api.api.SlaveInfo`
    :raises MesosError: If the slave cannot be found
    """
    slave_dict = _get_slave_dict(hostname, port, slave_id)
    if not slave_dict:
        raise MesosError('Slave not found: %s' % slave_id)
    slave_info = _parse_slave_info(slave_dict)

    if resources:
        return _parse_slave_resources(slave_info.hostname, slave_info.port)
    return slave_info


def get_slave_task_directory(hostname, port, task_id):
    """Queries the Mesos slave REST API to get the directory for the stdout and stderr files for the given task

    :param hostname: The hostname of the slave
    :type hostname: str
    :param port: The port of the slave
    :type port: int
    :param task_id: The ID of the Mesos task
    :type task_id: str
    :returns: The directory on the slave, possibly None
    :rtype: str
    :raises MesosError: If the task cannot be found
    """
    url = 'http://%s:%i/state.json' % (hostname, port)
    response = urllib2.urlopen(url)
    state_dict = json.load(response)
    for framework in state_dict['frameworks']:
        for executor in framework['executors']:
            if executor['id'] == task_id:
                return executor['directory'].replace('\\', '')

    raise MesosError('Task not found: %s' % task_id)


def get_slave_task_run_id(hostname, port, task_id):
    """Queries the Mesos slave REST API to get the run ID for the given task

    :param hostname: The hostname of the slave
    :type hostname: str
    :param port: The port of the slave
    :type port: int
    :param task_id: The ID of the Mesos task
    :type task_id: str
    :returns: The directory on the slave, possibly None
    :rtype: str
    :raises MesosError: If the task cannot be found
    """
    url = 'http://%s:%i/state.json' % (hostname, port)
    response = urllib2.urlopen(url)
    state_dict = json.load(response)
    for framework in state_dict['frameworks']:
        for executor in framework['executors']:
            if executor['id'] == task_id:
                tmp = executor['directory'].replace('\\', '')
                # TODO: This is fragile but appears to be the only way to get this value right now.
                # revisit and fix this when we upgrade mesos
                return tmp.split('/')[-1]

    raise MesosError('Task not found: %s' % task_id)


def get_slave_task_file(hostname, port, task_dir, file_name):
    """Queries the Mesos slave REST API to get the specified file from the given task directory

    :param hostname: The hostname of the slave
    :type hostname: str
    :param port: The port of the slave
    :type port: int
    :param task_dir: The directory on the slave that has the task's files
    :type task_dir: str
    :param file_name: The name of the file to retrieve
    :type file_name: str
    :returns: The contents of the file
    :rtype: str
    """
    url = get_slave_task_url(hostname, port, task_dir, file_name)
    response = urllib2.urlopen(url)
    return response.read()


def get_slave_task_url(hostname, port, task_dir, file_name):
    """Generate a query URL for Mesos slave REST API for access to a specified file from the given task directory

    :param hostname: The hostname of the slave
    :type hostname: str
    :param port: The port of the slave
    :type port: int
    :param task_dir: The directory on the slave that has the task's files
    :type task_dir: str
    :param file_name: The name of the file to retrieve
    :type file_name: str
    :returns: The URL
    :rtype: str
    """
    base_url = 'http://%s:%i/files/download.json?' % (hostname, port)
    query_args = urllib.urlencode({'path':   '%s/%s' % (task_dir, file_name)})
    return base_url + query_args


def _get_slave_dict(hostname, port, slave_id):
    """Queries the Mesos master REST API to get information for the given slave

    :param hostname: The hostname of the master
    :type hostname: str
    :param port: The port of the master
    :type port: int
    :param slave_id: The ID of the slave
    :type slave_id: str
    :returns: A dictionary structure representing the slave information.
    :rtype: dict
    """
    slaves_dict = _get_slaves_dict(hostname, port)
    for slave_dict in slaves_dict:
        if slave_dict['id'] == slave_id:
            return slave_dict


def _get_slaves_dict(hostname, port):
    """Queries the Mesos master REST API to get information for the given slave

    :param hostname: The hostname of the master
    :type hostname: str
    :param port: The port of the master
    :type port: int
    :returns: A dictionary structure representing the slave information.
    :rtype: dict
    """
    url = 'http://%s:%i/master/state.json' % (hostname, port)
    response = urllib2.urlopen(url)
    state_dict = json.load(response)
    return state_dict['slaves']


def _parse_slave_info(slave_dict):
    """Parses the given Mesos API dictionary into a recognized object model.

    :param slave_dict: The raw slave information to parse.
    :type slave_dict: dict
    :returns: A summary of the slave information.
    :rtype: :class:`mesos_api.api.SlaveInfo`
    """

    # Extract the general host attributes
    slave_id = slave_dict['id']
    hostname = slave_dict['hostname']
    match = PORT_REGEX.search(slave_dict['pid'])
    port = int(match.group(1))

    # Extract the total resource usage metrics
    total_dict = slave_dict['resources']
    total = HardwareResources(float(total_dict['cpus']), float(total_dict['mem']), float(total_dict['disk']))

    return SlaveInfo(hostname, port, total, slave_id=slave_id)


def _parse_slave_resources(hostname, port):
    url = 'http://%s:%i/state.json' % (hostname, port)
    response = urllib2.urlopen(url)
    state_dict = json.load(response)

    # Extract the total resource usage metrics
    total_dict = state_dict['resources']
    total = HardwareResources(float(total_dict['cpus']), float(total_dict['mem']), float(total_dict['disk']))

    scheduled = HardwareResources()
    fw_dict, _online = _get_framework(state_dict)
    if fw_dict:
        for exec_dict in fw_dict['executors']:
            res_dict = exec_dict['resources']
            if res_dict:
                scheduled.cpus += float(res_dict['cpus'])
                scheduled.mem += float(res_dict['mem'])
                scheduled.disk += float(res_dict['disk'])

    # TODO Mesos only provides true real-time usage if we query each slave individually
    used = HardwareResources()

    return SlaveInfo(hostname, port, total, scheduled, used)


def _get_framework(state_dict):
    """Finds the default scheduler framework within the Mesos API response

    :param state_dict: The API response dictionary to parse.
    :type state_dict: dict
    :returns: A tuple of the framework dictionary and whether it is currently online.
    :rtype: tuple(dict, bool)
    """
    for key_name in ['frameworks', 'completed_frameworks', 'unregistered_frameworks']:
        if key_name in state_dict:
            for fw_dict in state_dict[key_name]:
                # TODO We may want to come up with a less hard-coded way to identify our framework
                if 'scale' in fw_dict['name'].lower():
                    online = key_name == 'frameworks' and (fw_dict['active'] if 'active' in fw_dict else False)
                    return fw_dict, online
    return None, False
