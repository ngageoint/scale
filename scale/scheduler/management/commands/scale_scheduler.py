from __future__ import unicode_literals

import json
import logging
import signal
import socket
import sys

from django.conf import settings
from django.core.management.base import BaseCommand

from mesoshttp.client import MesosClient

from scheduler.manager import scheduler_mgr
from scheduler.scale_scheduler import ScaleScheduler

logger = logging.getLogger(__name__)

GLOBAL_SHUTDOWN = None


class Command(BaseCommand):
    """Command that launches the Scale scheduler
    """

    help = 'Launches the Scale scheduler'

    def handle(self, *args, **options):
        """See :meth:`django.core.management.base.BaseCommand.handle`.

        This method starts the scheduler.
        """

        # Register a listener to handle clean shutdowns
        signal.signal(signal.SIGTERM, self._onsigterm)

        # Set up global shutdown
        global GLOBAL_SHUTDOWN
        GLOBAL_SHUTDOWN = self._shutdown

        logger.info('Scale Scheduler %s', settings.VERSION)

        self.run_scheduler(settings.MESOS_MASTER)

    def run_scheduler(self, mesos_master):
        logger.info("Scale rising...")
        self.scheduler = ScaleScheduler()
        self.scheduler.initialize()
        scheduler_mgr.hostname = socket.getfqdn()

        logger.info('Connecting to Mesos master at %s', mesos_master)

        logging.getLogger('mesoshttp').setLevel(logging.DEBUG)

        # By default use ZK for master detection
        self.client = MesosClient(mesos_urls=[settings.MESOS_MASTER],
                                  # We have to run tasks as root, so docker commands may be executed
                                  frameworkUser='root',
                                  frameworkName=settings.FRAMEWORK_NAME,
                                  frameworkWebUI=settings.WEBSERVER_ADDRESS)
        if settings.SERVICE_SECRET:
            # We are in Enterprise mode and using service account
            self.client.set_service_account(json.loads(settings.SERVICE_SECRET))
        elif settings.PRINCIPAL and settings.SECRET:
            self.client.set_credentials(settings.PRINCIPAL, settings.SECRET)

        self.client.add_capability('GPU_RESOURCES')

        try:
            self.scheduler.run(self.client)
            status = 0
        except:
            status = 1
            logger.exception('Mesos Scheduler Driver returned an exception')

        #Perform a shut down and return any non-zero status
        shutdown_status = self._shutdown()
        status = status or shutdown_status

        logger.info('Exiting...')
        sys.exit(status)

    def _onsigterm(self, signum, _frame):
        """See signal callback registration: :py:func:`signal.signal`.

        This callback performs a clean shutdown when a TERM signal is received.
        """
        logger.info('Scheduler command terminated due to signal: %i', signum)
        self._shutdown()
        sys.exit(1)

    def _shutdown(self):
        """Performs any clean up required by this command.

        :returns: The exit status code based on whether the shutdown operation was clean with no exceptions.
        :rtype: int
        """
        status = 0

        try:
            if self.scheduler:
                self.scheduler.shutdown()
        except:
            logger.exception('Failed to properly shutdown Scale scheduler.')
            status = 1

        return status
