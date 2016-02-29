'''Defines the command line method for running a Strike process'''
from __future__ import unicode_literals

import logging
import math
import signal
import sys
import time
from optparse import make_option

from django.core.management.base import BaseCommand
from django.utils.timezone import now

from ingest.models import Strike
from ingest.strike.strike_processor import StrikeProcessor
from job.execution.cleanup import cleanup_job_exe
from job.models import JobExecution


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    '''Command that executes the Strike processor
    '''

    option_list = BaseCommand.option_list + (
        make_option('-i', '--strike-id', action='store', type='int', help=('ID of the Strike process to run')),
        make_option('-t', '--throttle', action='store', type='int', default=60,
                    help=('Minimum delay time in seconds before subsequent reads of the directory')),
    )

    help = 'Executes the Strike processor to monitor and process incoming files for ingest'

    def __init__(self):
        '''Constructor
        '''
        super(Command, self).__init__()
        self.running = False
        self.job_exe_id = None

        # TODO: this is not bullet proof, figure out a better way to ensure two Strike processes with the same Strike ID
        # cannot run at the same time
        # Number of executions for the Strike job
        # Keeping track of this will allow us to kill the Strike process if this becomes an old job execution that was
        # never killed, preventing duplicate Strike processes running at the same time
        self.num_exes = None

    def handle(self, **options):
        '''See :meth:`django.core.management.base.BaseCommand.handle`.

        This method starts the Strike processor.
        '''
        self.running = True

        # Register a listener to handle clean shutdowns
        signal.signal(signal.SIGTERM, self._onsigterm)

        strike_id = options.get('strike_id')
        throttle = options.get('throttle')

        logger.info('Command starting: scale_strike')
        logger.info(' - Strike ID: %i', strike_id)
        logger.info(' - Throttle: %i', throttle)
        self._run_processor(strike_id, throttle)
        logger.info('Command completed: scale_strike')

    def _init_processor(self, strike_id):
        '''Creates and initializes a Strike processor for the given Strike ID

        :param strike_id: The ID of the Strike process
        :type strike_id: int
        :returns: The Strike processor
        :rtype: :class:`ingest.strike.strike_processor.StrikeProcessor`
        '''
        logger.info('Initializing processor')

        strike = Strike.objects.select_related('job').get(pk=strike_id)
        self.job_exe_id = JobExecution.objects.get_latest([strike.job])[strike.job.id].id
        strike_proc = StrikeProcessor(strike_id, self.job_exe_id, strike.get_strike_configuration())
        self.num_exes = strike.job.num_exes

        return strike_proc

    def _reload_processor(self, strike_id, strike_proc):
        '''Reloads the configuration of the given Strike processor

        :param strike_id: The ID of the Strike process
        :type strike_id: int
        :param strike_proc: The Strike processor
        :type strike_proc: :class:`ingest.strike.strike_processor.StrikeProcessor`
        '''
        logger.debug('Reloading configuration')

        strike = Strike.objects.select_related('job').get(pk=strike_id)
        if self.num_exes != strike.job.num_exes:
            self.running = False
            raise Exception('Old Strike process detected, shutting down')

        strike_proc.load_configuration(strike.get_strike_configuration())

    def _run_processor(self, strike_id, throttle):
        '''Runs the given Strike processor

        :param strike_id: The ID of the Strike process to run
        :type strike_id: int
        :param throttle: The minimum delay time in seconds before subsequent reads of the directory
        :type throttle: int
        '''
        strike_proc = None

        # TODO: figure out how to guarantee only one Strike process runs at a time
        while self.running:
            secs_passed = 0
            try:
                if not strike_proc:
                    strike_proc = self._init_processor(strike_id)
                else:
                    self._reload_processor(strike_id, strike_proc)

                # Process the directory and record number of seconds used
                started = now()
                strike_proc.mount_and_process_dir()
                ended = now()

                secs_passed = (ended - started).total_seconds()
            except:
                logger.exception('Strike processor encountered error.')
            finally:
                if self.running:
                    # If process time takes less than user-specified time, throttle
                    if secs_passed < throttle:
                        # Delay until full throttle time reached
                        delay = math.ceil(throttle - secs_passed)
                        logger.debug('Pausing for %i seconds', delay)
                        time.sleep(delay)

        if self.job_exe_id:
            cleanup_job_exe(self.job_exe_id)
        logger.info('Strike processor has stopped running')

        # TODO: eventually implement a REST API call to permanently stop a Strike process, which should allow this
        # command line method to return 0 and complete successfully
        sys.exit(1)

    def _onsigterm(self, signum, _frame):
        '''See signal callback registration: :py:func:`signal.signal`.

        This callback performs a clean shutdown when a TERM signal is received.
        '''
        logger.info('Strike command terminated due to signal: %i', signum)
        self.running = False
