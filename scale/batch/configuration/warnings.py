"""Defines warnings that can occur when interacting with batch configuration"""


class ValidationWarning(object):
    """Tracks batch configuration warnings during validation"""

    def __init__(self, key, details):
        """Constructor

        :param key: A unique identifier clients can use to recognize the warning
        :type key: string
        :param details: A user-friendly description of the problem, including field names and/or associated values
        :type details: string
        """

        self.key = key
        self.details = details
