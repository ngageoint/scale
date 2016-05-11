"""Defines exceptions that can occur when interacting with job configuration"""


class InvalidJobConfiguration(Exception):
    """Exception indicating that the provided job configuration JSON was invalid
    """
    pass
