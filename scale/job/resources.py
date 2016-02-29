'''Defines classes for encapsulating sets of resources'''


class JobResources(object):
    '''This class encapsulates a set of resources used for executing jobs
    '''

    def __init__(self, cpus=0.0, mem=0.0, disk_in=0.0, disk_out=0.0, disk_total=0.0):
        '''Constructor

        :param cpus: The number of CPUs
        :type cpus: float
        :param mem: The amount of memory in MiB
        :type mem: float
        :param disk_in: The amount of input disk space in MiB
        :type disk_in: float
        :param disk_out: The amount of output disk space in MiB
        :type disk_out: float
        :param disk_total: The amount of total disk space in MiB
        :type disk_total: float
        '''

        if cpus < 0.0:
            raise Exception('cpus cannot be negative')
        if mem < 0.0:
            raise Exception('mem cannot be negative')
        if disk_in < 0.0:
            raise Exception('disk_in cannot be negative')
        if disk_out < 0.0:
            raise Exception('disk_out cannot be negative')
        if disk_total < 0.0:
            raise Exception('disk_total cannot be negative')

        self.cpus = cpus
        self.mem = mem
        self.disk_in = disk_in
        self.disk_out = disk_out
        self.disk_total = disk_total


class NodeResources(object):
    '''This class encapsulates a set of resources available on a node
    '''

    def __init__(self, cpus=0.0, mem=0.0, disk=0.0):
        '''Constructor

        :param cpus: The number of CPUs
        :type cpus: float
        :param mem: The amount of memory in MiB
        :type mem: float
        :param disk: The amount of disk space in MiB
        :type disk: float
        '''

        if cpus < 0.0:
            raise Exception('cpus cannot be negative')
        if mem < 0.0:
            raise Exception('mem cannot be negative')
        if disk < 0.0:
            raise Exception('disk cannot be negative')

        self.cpus = cpus
        self.mem = mem
        self.disk = disk
