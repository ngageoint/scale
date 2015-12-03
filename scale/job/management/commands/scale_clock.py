'''Defines the command line method for running the Scale clock process'''
import logging
import math
import signal
import sys
import time

from django.core.management.base import BaseCommand
from django.utils.timezone import now

import job.clock as clock
from job.models import Job, JobType


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    '''Command that executes the Scale clock
    '''

    help = 'Executes the Scale clock to perform necessary system functions at their scheduled time'

    def __init__(self):
        '''Constructor
        '''
        super(Command, self).__init__()
        self.running = False
        self.throttle = 60
        self.job_id = None

        # Number of executions for the clock job
        # Keeping track of this will allow us to kill the clock process if this becomes an old job execution that was
        # never killed, preventing duplicate clock processes running at the same time
        self.num_exes = None

    def handle(self, **options):
        '''See :meth:`django.core.management.base.BaseCommand.handle`.

        This method starts the Scale clock.
        '''
        self.running = True

        # Register a listener to handle clean shutdowns
        signal.signal(signal.SIGTERM, self._onsigterm)

        logger.info(u'Command starting: scale_clock')
        while self.running:
            secs_passed = 0
            try:
                if not self.job_id:
                    self._init_clock()
                else:
                    self._check_clock()

                started = now()
                clock.perform_tick()
                ended = now()

                secs_passed = (ended - started).total_seconds()
            except:
                logger.exception(u'Clock encountered error')
            finally:
                if self.running:
                    # If process time takes less than throttle time, throttle
                    if secs_passed < self.throttle:
                        # Delay until full throttle time reached
                        delay = math.ceil(self.throttle - secs_passed)
                        logger.debug(u'Pausing for %i seconds', delay)
                        time.sleep(delay)
        logger.info(u'Command completed: scale_clock')

        # Clock never successfully finishes, it should always run
        sys.exit(1)

    def _init_clock(self):
        '''Initializes the clock process by determining which job execution this process is
        '''
        logger.info(u'Initializing clock')
        clock_job_type = JobType.objects.get_clock_job_type()
        clock_job = Job.objects.get(job_type_id=clock_job_type.id)
        self.job_id = clock_job.id
        self.num_exes = clock_job.num_exes

    def _check_clock(self):
        '''Checks to ensure that this is not an old clock process
        '''
        logger.debug(u'Checking for duplicate clock processes')
        clock_job = Job.objects.get(pk=self.job_id)
        if self.num_exes != clock_job.num_exes:
            self.running = False
            raise Exception(u'Old clock process detected, shutting down')

    def _onsigterm(self, signum, _frame):
        '''See signal callback registration: :py:func:`signal.signal`.

        This callback performs a clean shutdown when a TERM signal is received.
        '''
        logger.info(u'Clock command terminated due to signal: %i', signum)
        self.running = False
