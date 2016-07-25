from __future__ import unicode_literals

import django
from django.test import TestCase

from ingest.strike.monitors.dir_monitor import DirWatcherMonitor
from ingest.strike.monitors.exceptions import InvalidMonitorConfiguration


class TestDirWatcherMonitor(TestCase):

    def setUp(self):
        django.setup()

    def test_validate_configuration_missing_transfer_suffix(self):
        """Tests calling DirWatcherMonitor.validate_configuration() with missing transfer_suffix"""

        config = {
            'type': 'dir-watcher'
        }
        self.assertRaises(InvalidMonitorConfiguration, DirWatcherMonitor().validate_configuration, config)

    def test_validate_configuration_bad_transfer_suffix(self):
        """Tests calling DirWatcherMonitor.validate_configuration() with bad type for transfer_suffix"""

        config = {
            'type': 'dir-watcher',
            'transfer_suffix': 1
        }
        self.assertRaises(InvalidMonitorConfiguration, DirWatcherMonitor().validate_configuration, config)

    def test_validate_configuration_empty_transfer_suffix(self):
        """Tests calling DirWatcherMonitor.validate_configuration() with empty transfer_suffix"""

        config = {
            'type': 'dir-watcher',
            'transfer_suffix': ''
        }
        self.assertRaises(InvalidMonitorConfiguration, DirWatcherMonitor().validate_configuration, config)

    def test_validate_configuration_success(self):
        """Tests calling DirWatcherMonitor.validate_configuration() successfully"""

        config = {
            'type': 'dir-watcher',
            'transfer_suffix': '_tmp'
        }
        DirWatcherMonitor().validate_configuration(config)
