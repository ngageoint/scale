"""Defines a monitor that watches a file system directory for incoming files"""
import logging

from ingest.strike.monitors.monitor import Monitor


logger = logging.getLogger(__name__)


class DirWatcherMonitor(Monitor):
    """A monitor that watches a file system directory for incoming files
    """

    def __init__(self):
        """Constructor
        """

        super(DirWatcherMonitor, self).__init__('dir-watcher')

    def load_configuration(self, configuration, monitored_workspace, file_handler):
        """See :meth:`ingest.strike.monitors.monitor.Monitor.load_configuration`
        """

        # TODO:
        pass

    def run(self):
        """See :meth:`ingest.strike.monitors.monitor.Monitor.run`
        """

        # TODO:
        pass

    def stop(self):
        """See :meth:`ingest.strike.monitors.monitor.Monitor.stop`
        """

        # TODO:
        pass

    def validate_configuration(self, configuration):
        """See :meth:`ingest.strike.monitors.monitor.Monitor.validate_configuration`
        """

        # TODO:
        pass
