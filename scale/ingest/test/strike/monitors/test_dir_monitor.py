from __future__ import unicode_literals

import django
from django.test import TestCase
from mock import Mock

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

    def test_process_ingest_rule_not_matched(self):
        """Tests _process_ingest when no rules are matched"""
        
        file_size = 10
        file_path = '/amazing'
        
        ingest_file = Mock()
        ingest_file.status = 'TRANSFERRED'
        ingest_file.is_there_rule_match.return_value = False

        DirWatcherMonitor()._process_ingest(ingest_file, file_path, file_size)

        ingest_file.save.assert_called_once()
        self.assertEqual(ingest_file.status, 'DEFERRED')
        self.assertEqual(ingest_file.file_size, file_size)
        self.assertEqual(ingest_file.file_path, file_path)
