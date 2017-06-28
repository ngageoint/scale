"""Defines the class that represents a set of resources on a node"""
from __future__ import unicode_literals

from util.exceptions import ScaleLogicBug

from node.resources.resource import Cpus, Disk, Mem


class NodeResources(object):
    """This class encapsulates a set of node resources
    """

    def __init__(self, resources=None):
        """Constructor

        :param resources: The list of node resources
        :type resources: list
        """

        self._resources = {}  # {Name: Resource}
        if resources:
            for resource in resources:
                if resource.resource_type != 'SCALAR':
                    raise ScaleLogicBug('Resource type "%s" is not currently supported', resource.resource_type)
                self._resources[resource.name] = resource

        # Make sure standard resources are defined
        if 'cpus' not in self._resources:
            self._resources['cpus'] = Cpus(0.0)
        if 'mem' not in self._resources:
            self._resources['mem'] = Mem(0.0)
        if 'disk' not in self._resources:
            self._resources['disk'] = Disk(0.0)

    def __str__(self):
        """Converts the resource to a readable logging string

        :returns: A readable string for logging
        :rtype: string
        """

        logging_str = ', '.join(['%.2f %s' % (resource.value, resource.name) for resource in self._resources.values()])
        return '[%s]' % logging_str

    @property
    def cpus(self):
        """The number of CPUs

        :returns: The number of CPUs
        :rtype: float
        """

        return self._resources['cpus'].value

    @property
    def disk(self):
        """The amount of disk space in MiB

        :returns: The amount of disk space
        :rtype: float
        """

        return self._resources['disk'].value

    @property
    def mem(self):
        """The amount of memory in MiB

        :returns: The amount of memory
        :rtype: float
        """

        return self._resources['mem'].value

    @property
    def resources(self):
        """The list of resources

        :returns: The list of resources
        :rtype: list
        """

        return self._resources.values()

    def add(self, node_resources):
        """Adds the given resources

        :param node_resources: The resources to add
        :type node_resources: :class:`node.resources.NodeResources`
        """

        for resource in node_resources.resources:
            if resource.name in self._resources:
                self._resources[resource.name].value += resource.value  # Assumes SCALAR type
            else:
                self._resources[resource.name] = resource.copy()

    def copy(self):
        """Returns a deep copy of these resources. Editing one of the resources objects will not affect the other.

        :returns: A copy of these resources
        :rtype: :class:`node.resources.node_resources.NodeResources`
        """

        resources_copy = NodeResources()
        resources_copy.add(self)
        return resources_copy

    def generate_status_json(self, resource_dict, key_name, total_resources=None):
        """Generates the portion of the status JSON that describes these resources

        :param resource_dict: The dict for these resources
        :type resource_dict: dict
        :param key_name: The key name for describing these resources
        :type key_name: string
        :param total_resources: The total amount of the resources (for percentages), possibly None
        :type total_resources: :class:`node.resources.NodeResources`
        """

        for resource in self._resources.values():
            # Assumes SCALAR type
            results = {key_name: {'value': resource.value}}
            if total_resources:
                total_value = total_resources._resources[resource.name].value
                if total_value:
                    percentage = int(round(resource.value / total_value, 0))
                else:
                    percentage = 0.0
                results[key_name]['percentage'] = percentage
            resource_dict[resource.name] = results

    def get_json(self):
        """Returns these resources as a JSON schema

        :returns: The resources as a JSON schema
        :rtype: :class:`node.resources.json.Resources`
        """

        from node.resources.json.resources import Resources
        resources_dict = {}
        for resource in self._resources.values():
            resources_dict[resource.name] = resource.value  # Assumes SCALAR type
        return Resources({'resources': resources_dict})

    def increase_up_to(self, node_resources):
        """Increases each resource up to the value in the given node resources

        :param node_resources: The resources
        :type node_resources: :class:`node.resources.NodeResources`
        """

        for resource in node_resources.resources:
            if resource.name in self._resources:
                if self._resources[resource.name].value < resource.value:  # Assumes SCALAR type
                    self._resources[resource.name].value = resource.value
            else:
                self._resources[resource.name] = resource.copy()

    def is_equal(self, node_resources):
        """Indicates if these resources are equal. This should be used for testing only.

        :param node_resources: The resources to compare
        :type node_resources: :class:`node.resources.NodeResources`
        :returns: True if these resources are equal, False otherwise
        :rtype: bool
        """

        # Make sure they have the exact same set of resource names
        names = set()
        for resource in node_resources.resources:
            names.add(resource.name)
        if set(self._resources.keys()) != names:
            return False

        for resource in node_resources.resources:
            if round(self._resources[resource.name].value, 5) != round(resource.value, 5):  # Assumes SCALAR type
                return False

        return True

    def is_sufficient_to_meet(self, node_resources):
        """Indicates if these resources are sufficient to meet the requested resources

        :param node_resources: The requested resources
        :type node_resources: :class:`node.resources.NodeResources`
        :returns: True if these resources are sufficient for the request, False otherwise
        :rtype: bool
        """

        for resource in node_resources.resources:
            if resource.name in self._resources:
                if self._resources[resource.name].value < resource.value:  # Assumes SCALAR type
                    return False
            else:
                # Do not have this resource, not a problem if requesting 0.0
                if resource.value > 0.0:
                    return False

        return True

    def limit_to(self, node_resources):
        """Limits each resource, subtracting any amount that goes over the amount in the given node resources

        :param node_resources: The resources
        :type node_resources: :class:`node.resources.NodeResources`
        """

        for resource in self._resources.values():
            if resource.name in node_resources._resources:
                if resource.value > node_resources._resources[resource.name].value:  # Assumes SCALAR type
                    resource.value = node_resources._resources[resource.name].value
            else:
                self.remove_resource(resource.name)

    def remove_resource(self, name):
        """Removes the resource with the given name

        :param name: The name of the resource to remove
        :type name: string
        """

        if name in self._resources:
            if name in ['cpus', 'mem', 'disk']:
                self._resources[name].value = 0.0
            else:
                del self._resources[name]

    def round_values(self):
        """Rounds all of the resource values
        """

        for resource in self._resources.values():
            resource.value = round(resource.value, 2)  # Assumes SCALAR type

    def subtract(self, node_resources):
        """Subtracts the given resources

        :param node_resources: The resources to subtract
        :type node_resources: :class:`node.resources.NodeResources`
        """

        for resource in node_resources.resources:
            if resource.name in self._resources:
                self._resources[resource.name].value -= resource.value  # Assumes SCALAR type
