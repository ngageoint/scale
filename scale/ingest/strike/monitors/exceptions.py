"""Defines the exceptions related to Strike monitors"""

from ingest.strike.configuration.exceptions import InvalidStrikeConfiguration


class InvalidMonitorConfiguration(InvalidStrikeConfiguration):
    """Exception indicating that a monitor configuration was invalid
    """

    pass
