"""Defines classes for encapsulating sets of resources"""


class JobResources(object):
    """This class encapsulates a set of resources used for executing jobs
    """

    def __init__(self, cpus=0.0, mem=0.0, disk_in=0.0, disk_out=0.0, disk_total=0.0):
        """Constructor

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
        """

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
    """This class encapsulates a set of resources available on a node
    """

    def __init__(self, cpus=0.0, mem=0.0, disk=0.0):
        """Constructor

        :param cpus: The number of CPUs
        :type cpus: float
        :param mem: The amount of memory in MiB
        :type mem: float
        :param disk: The amount of disk space in MiB
        :type disk: float
        """

        if cpus < 0.0:
            raise Exception('cpus cannot be negative')
        if mem < 0.0:
            raise Exception('mem cannot be negative')
        if disk < 0.0:
            raise Exception('disk cannot be negative')

        self.cpus = cpus
        self.mem = mem
        self.disk = disk

    def add(self, resources):
        """Adds the given resources

        :param resources: The resources to add
        :type resources: :class:`job.resources.NodeResources`
        """

        self.cpus += resources.cpus
        self.mem += resources.mem
        self.disk += resources.disk

    def generate_status_json(self, resource_dict):
        """Generates the portion of the status JSON that describes these resources

        :param resource_dict: The dict for these resources
        :type resource_dict: dict
        """

        resource_dict['cpus'] = self.cpus
        resource_dict['memory'] = self.mem
        resource_dict['disk'] = self.disk

    def increase_up_to(self, resources):
        """Increases each resource up to the value in the given resources

        :param resources: The resources
        :type resources: :class:`job.resources.NodeResources`
        """

        if self.cpus < resources.cpus:
            self.cpus = resources.cpus
        if self.mem < resources.mem:
            self.mem = resources.mem
        if self.disk < resources.disk:
            self.disk = resources.disk

    def subtract(self, resources):
        """Subtracts the given resources

        :param resources: The resources to subtract
        :type resources: :class:`job.resources.NodeResources`
        """

        self.cpus -= resources.cpus
        self.mem -= resources.mem
        self.disk -= resources.disk
