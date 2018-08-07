"""Defines exceptions that can occur when interacting with Scan configuration"""


class InvalidScanConfiguration(ValidationException):
    """Exception indicating that the provided Scan configuration was invalid"""

    def __init__(self, description):
        """Constructor

        :param description: The description of the validation error
        :type description: string
        """

        super(InvalidScanConfiguration, self).__init__('INVALID_SCAN_CONFIGURATION', description)