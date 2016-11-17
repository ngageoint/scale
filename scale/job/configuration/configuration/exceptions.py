"""Defines exceptions that can occur when interacting with job configuration"""


class InvalidJobConfiguration(Exception):
    """Exception indicating that the provided job configuration JSON was invalid
    """
    pass


class InvalidSetting(Exception):
    """Exception indicating that the proivided job settings were invaild
    """
    pass
