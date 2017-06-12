"""Defines the node resource classes"""
from __future__ import unicode_literals

from abc import ABCMeta


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

    def copy(self):
        """Returns a deep copy of this resource. Editing one of the resource objects will not affect the other.

        :returns: A copy of this resource
        :rtype: :class:`node.resources.NodeResources`
        """

        raise NotImplementedError


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
