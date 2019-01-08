"""Defines the class that represents a set of resources on a node"""
from __future__ import unicode_literals

import logging

from util.exceptions import ScaleLogicBug

from node.resources.resource import Cpus, Disk, Mem, Gpus, ScalarResource

logger = logging.getLogger(__name__)


class NodeResources(object):
    """This class encapsulates a set of node resources

    Node resources can be unreserved or specifically associated to a role
    """

    def __init__(self, resources=None):
        """Constructor

        :param resources: The list of node resources
        :type resources: [:class:`node.resources.resource.ScalarResource`]
        """

        self._resources = {}  # {Reservation: {Name: Resource}}

        if resources:
            for resource in resources:
                if resource.resource_type != 'SCALAR':
                    raise ScaleLogicBug('Resource type "%s" is not currently supported', resource.resource_type)
                self._add_resource(resource)

        self._initialize_default_resources('*')

    def _initialize_default_resources(self, reservation):
        """Initialize a role on resource with default resources

        :param reservation: Name of role
        :type reservation: string
        """

        if reservation not in self._resources:
            self._resources[reservation] = {}
        if 'cpus' not in self._resources[reservation]:
            self._resources[reservation]['cpus'] = Cpus(0.0, reservation=reservation)
        if 'mem' not in self._resources[reservation]:
            self._resources[reservation]['mem'] = Mem(0.0, reservation=reservation)
        if 'disk' not in self._resources[reservation]:
            self._resources[reservation]['disk'] = Disk(0.0, reservation=reservation)
        if 'gpus' not in self._resources[reservation]:
            self._resources[reservation]['gpus'] = Gpus(0.0, reservation=reservation)

    def _add_resource(self, resource):
        """Add a resource to those tracked by the object

        :param resource: ScalarResource
        :type resource: :class:`node.resources.resource.ScalarResource`
        """

        try:
        if resource.reservation not in self._resources:
            self._initialize_default_resources(resource.reservation)

        if resource.name in self._resources[resource.reservation]:
            self._resources[resource.reservation][resource.name].value += resource.value  # Assumes SCALAR type
        else:
            self._resources[resource.reservation] = {resource.name: resource.copy()}
        except Exception:
            logger.exception()

    def __str__(self):
        """Converts the resource to a readable logging string

        :returns: A readable string for logging
        :rtype: string
        """

        logging_str = ''

        values = []
        for reservation in self._resources.keys():
            values.append('[%s](%s)' % \
                          (', '.join(['%.2f %s' % (resource.value, resource.name) for resource in
                                      self._resources[reservation].values()]),
                           reservation
                           ))

        logging_str = ', '.join(values)

        return logging_str

    def _get_resource_sum(self, name):
        """Identify the entire scalar value sum of the resource, without respect for reservation

        :param name: Resource name
        :type name: basestring
        :returns: The resource's scalar value sum
        :rtype: float
        """

        total = 0.0

        for role in self._resources:
            for resource_name in self._resources[role]:
                if resource_name == name:
                    total += self._resources[role][resource_name].value

        return total

    @property
    def cpus(self):
        """The number of CPUs, without respect for reservation

        :returns: The number of CPUs
        :rtype: float
        """

        return self._get_resource_sum('cpus')

    @property
    def disk(self):
        """The amount of disk space in MiB, without respect for reservation

        :returns: The amount of disk space
        :rtype: float
        """

        return self._get_resource_sum('disk')

    @property
    def mem(self):
        """The amount of memory in MiB, without respect for reservation

        :returns: The amount of memory
        :rtype: float
        """

        return self._get_resource_sum('mem')

    @property
    def gpus(self):
        """The number of GPUs

        :returns: The amount of GPUs, without respect for reservation
        :rtype: float
        """

        return self._get_resource_sum('gpus')

    @property
    def resources(self):
        """The list of resources - may contain duplicates if reservations are not node complete

        :returns: The list of resources
        :rtype: list
        """

        resources = []
        for dicts in self._resources.values():
            resources.append(dicts.values())

        return resources

    @property
    def resource_names(self):
        """The list of resources names across all reservations

        :returns: The set of resource names
        :rtype: set
        """

        resource_names = set()
        for dicts in self._resources.values():
            resource_names.add(dicts.keys())

        return resource_names

    def get_resources_by_reservation(self, reservation):
        """

        @param reservation:
        @return:
        """

        return self._resources[reservation]

    def add(self, node_resources):
        """Adds the given resources

        :param node_resources: The resources to add
        :type node_resources: :class:`node.resources.NodeResources`
        """

        for resource in node_resources.resources:
            self._add_resource(resource)

    def copy(self):
        """Returns a deep copy of these resources. Editing one of the resources objects will not affect the other.

        :returns: A copy of these resources
        :rtype: :class:`node.resources.node_resources.NodeResources`
        """

        resources_copy = NodeResources()
        resources_copy.add(self)
        return resources_copy

    def generate_status_json(self, resources_dict, key_name):
        """Generates the portion of the status JSON that describes these resources

        :param resources_dict: The dict for all resources
        :type resources_dict: dict
        :param key_name: The key name for describing these resources
        :type key_name: string
        """

        # TODO: Update status json to include principal associated with reservation

        for resource in self.resources:
            if resource.name in resources_dict:
                resource_dict = resources_dict[resource.name]
            else:
                resource_dict = {}
                resources_dict[resource.name] = resource_dict

            # Assumes SCALAR type
            resource_dict[key_name] = resource.value

    def get_json(self):
        """Returns these resources as a JSON schema

        :returns: The resources as a JSON schema
        :rtype: :class:`node.resources.json.Resources`
        """

        from node.resources.json.resources import Resources
        resources_dict = {}
        for resource in self.resources:
            resources_dict[resource.name] = resource.value  # Assumes SCALAR type
        return Resources({'resources': resources_dict}, do_validate=False)

    def increase_up_to(self, node_resources):
        """Increases each resource up to the value in the given node resources

        This is tricky with multiple role reserved resources. We are going to assume all incoming
        NodeResources are of one role. This should be a reasonable assumption as this method is always
        used in the context of ensuring enough resources are available. We aren't increasing to
        associate with any particular role.

        :param node_resources: The resources
        :type node_resources: :class:`node.resources.NodeResources`
        """

        for resource in node_resources.resources:
            resource_sum = self._get_resource_sum(resource.name)
            if resource_sum < resource.value:
                grow_resource = ScalarResource(name=resource.name,
                                               value=resource.value - resource_sum,
                                               reservation=resource.reservation)
                self._add_resource(grow_resource)
                logger.info("Increased beyond existing resource using: %s." % grow_resource)

    def is_equal(self, node_resources):
        """Indicates if these resources are equal. This should be used for testing only.

        :param node_resources: The resources to compare
        :type node_resources: :class:`node.resources.NodeResources`
        :returns: True if these resources are equal, False otherwise
        :rtype: bool
        """

        # Make sure the roles match
        if set(self._resources.keys()).difference(set(node_resources._resources.keys())):
            return False

        for reservation in self._resources.keys():
            # Make sure they have the exact same set of resource names
            names = set()
            for resource in node_resources.get_resources_by_reservation(reservation):
                names.add(resource.name)
            if set(self.get_resources_by_reservation(reservation).keys()) != names:
                return False

            for resource in node_resources.get_resources_by_reservation(reservation):
                if round(self.get_resources_by_reservation(reservation)[resource.name].value, 5) != round(resource.value, 5):  # Assumes SCALAR type
                    return False

        return True

    def is_sufficient_to_meet(self, node_resources):
        """Indicates if these resources are sufficient to meet the requested resources

        :param node_resources: The requested resources
        :type node_resources: :class:`node.resources.NodeResources`
        :returns: True if these resources are sufficient for the request, False otherwise
        :rtype: bool
        """

        # TODO: If it is sufficient, how do we ensure that the caller knows which reservation(s) is sufficient?

        for resource in node_resources.resources:
            resource_sum = self._get_resource_sum(resource.name)
            if resource.value > 0.0 and resource_sum < resource.value: # Assumes SCALAR type
                return False

        return True

    def limit_to(self, node_resources):
        """Limits each resource, subtracting any amount that goes over the amount in the given node resources

        :param node_resources: The resources
        :type node_resources: :class:`node.resources.NodeResources`
        """

        for resource_name in self.resource_names:
            if resource_name in node_resources.resource_names:
                resource_sum = node_resources._get_resource_sum(resource_name)
                self.remove_resource(resource_name, resource_sum) # Reduce to the limit.
            else:
                self.remove_resource(resource_name)

    def remove_resource(self, name, limit=0.0):
        """Removes or reduces to specified limit the resource with the given name

        :param name: The name of the resource to remove
        :type name: string
        :param limit: The value to reduce to or remove, if 0.0 reserved types (cpus, mem, etc.) are never removed
        :type limit: float
        """

        # We need to track the remainder of resource available and iterate until the sum
        # of all resources associated with roles are reduced to the specified limit
        remainder = self._get_resource_sum(name)

        # Already beneath limit, no-op
        if remainder <= limit:
            return

        roles = self._resources.values()
        # Ensure we evaluate unreserved resources first
        if '*' in roles:
            roles.insert(0, roles.pop(roles.index('*')))

        for role in roles:
            if name in self._resources[role]:
                if remainder > limit:
                    value = self._resources[role][name].value
                    if value < remainder:
                        self._resources[role][name].value = 0.0
                        remainder -= value
                    else:
                        self._resources[role][name].value = remainder
                        remainder = 0.0

    def round_values(self):
        """Rounds all of the resource values
        """

        for resource in self._resources.values():
            resource.value = round(resource.value, 2)  # Assumes SCALAR type

    def subtract(self, node_resources):
        """Subtracts the given resources, irrespective of associated reservations

        :param node_resources: The resources to subtract
        :type node_resources: :class:`node.resources.NodeResources`
        """

        roles = self._resources.values()
        # Ensure we evaluate unreserved resources first
        if '*' in roles:
            roles.insert(0, roles.pop(roles.index('*')))

        for resource in node_resources.resources:
            if self._get_resource_sum(resource.name) > 0.0:

                # We need to track the remainder of resource available and iterate until all resources
                # associated with roles are reduced to the specified limit
                remainder = resource.value
                name = resource.name

                for role in roles:
                    if name in self._resources[role]:
                        if remainder > 0.0:
                            value = self._resources[role][name].value
                            if value < remainder:
                                self._resources[role][name].value = 0.0 # Assumes SCALAR type
                                remainder -= value
                            else:
                                self._resources[role][name].value -= remainder # Assumes SCALAR type
                                remainder = 0.0