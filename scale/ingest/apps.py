"""The Scale ingest application"""
from __future__ import unicode_literals

from django.apps import AppConfig


class IngestConfig(AppConfig):
    """Configuration for the ingest app
    """
    name = 'ingest'
    label = 'ingest'
    verbose_name = 'Ingest'

    def ready(self):
        """
        Override this method in subclasses to run code when Django starts.
        """

        # Register ingest job type timeout error
        from job.execution.tasks.main_task import JOB_TYPE_TIMEOUT_ERRORS
        JOB_TYPE_TIMEOUT_ERRORS['scale-ingest'] = 'ingest-timeout'

        # Registers the Strike monitors with the monitor system
        import ingest.strike.monitors.factory as factory
        from ingest.strike.monitors.dir_monitor import DirWatcherMonitor
        from ingest.strike.monitors.s3_monitor import S3Monitor

        # Register monitor types
        factory.add_monitor_type(DirWatcherMonitor)
        factory.add_monitor_type(S3Monitor)

        # Registers the scanners with the Scan system
        import ingest.scan.scanners.factory as factory
        from ingest.scan.scanners.dir_scanner import DirScanner
        from ingest.scan.scanners.s3_scanner import S3Scanner

        # Register monitor types
        factory.add_scanner_type(DirScanner)
        factory.add_scanner_type(S3Scanner)
        
        # Register messages
        from ingest.messages.create_ingest_jobs import CreateIngest
        from messaging.messages.factory import add_message_type
        add_message_type(CreateIngest)
