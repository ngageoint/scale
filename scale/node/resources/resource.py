"""Defines the node resource classes"""
from __future__ import unicode_literals

from abc import ABCMeta, abstractmethod


class Resource(object):
    """Abstract class for a node resource
    """

    __metaclass__ = ABCMeta

    def __init__(self, name, resource_type):
        """Constructor

        :param name: The name of the resource
        :type name: string
        :param resource_type: The type of the resource
        :type resource_type: string
        """

        self.name = name
        self.resource_type = resource_type

    @abstractmethod
    def copy(self):
        """Returns a deep copy of this resource. Editing one of the resource objects will not affect the other.

        :returns: A copy of this resource
        :rtype: :class:`node.resources.resource.Resource`
        """


class ScalarResource(Resource):
    """A type of resource represented by a scalar floating point value
    """

    def __init__(self, name, value):
        """Constructor

        :param name: The name of the resource
        :type name: string
        :param value: The value of the resource
        :type value: float
        """

        super(ScalarResource, self).__init__(name, 'SCALAR')
        self.value = value

    def copy(self):
        """See :meth:`node.resources.resource.Resource.copy`
        """

        return ScalarResource(self.name, self.value)


class Cpus(ScalarResource):
    """A scalar resource representing the number of CPUs
    """

    def __init__(self, value):
        """Constructor

        :param value: The number of CPUs
        :type value: float
        """

        super(Cpus, self).__init__('cpus', value)


class Mem(ScalarResource):
    """A scalar resource representing the amount of memory in MiB
    """

    def __init__(self, value):
        """Constructor

        :param value: The amount of memory in MiB
        :type value: float
        """

        super(Mem, self).__init__('mem', value)


class Disk(ScalarResource):
    """A scalar resource representing the amount of disk space in MiB
    """

    def __init__(self, value):
        """Constructor

        :param value: The amount of disk space in MiB
        :type value: float
        """

        super(Disk, self).__init__('disk', value)
