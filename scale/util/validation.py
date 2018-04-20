"""Defines classes related to validating"""


class ValidationError(object):
    """Tracks errors during validation"""

    def __init__(self, name, description):
        """Constructor

        :param name: A unique name clients can use to recognize the error
        :type name: string
        :param description: A user-friendly description of the problem, including field names and/or associated values
        :type description: string
        """

        self.name = name
        self.description = description

    def to_dict(self):
        """Returns a dict representation of the error

        :returns: The dict representation
        :rtype: dict
        """

        return {'name': self.name, 'description': self.description}


class ValidationWarning(object):
    """Tracks warnings during validation"""

    def __init__(self, name, description):
        """Constructor

        :param name: A unique name clients can use to recognize the warning
        :type name: string
        :param description: A user-friendly description of the problem, including field names and/or associated values
        :type description: string
        """

        self.name = name
        self.description = description

    def to_dict(self):
        """Returns a dict representation of the warning

        :returns: The dict representation
        :rtype: dict
        """

        return {'name': self.name, 'description': self.description}
