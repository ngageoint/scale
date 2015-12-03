'''Defines the command that performs job execution cleanup'''
from __future__ import unicode_literals

import logging
import sys
from optparse import make_option

from django.core.management.base import BaseCommand

from job.execution.cleanup import cleanup_job_exe


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    '''Command that performs the cleanup for a job execution
    '''

    option_list = BaseCommand.option_list + (
        make_option('-i', '--job-exe-id', action='store', type='int', help=('The ID of the job execution to clean up')),
    )

    help = 'Performs the cleanup for a job execution'

    def handle(self, **options):
        '''See :meth:`django.core.management.base.BaseCommand.handle`.

        This method starts the command.
        '''

        job_exe_id = options.get('job_exe_id')

        logger.info('Command starting: scale_cleanup - Job Execution ID: %i', job_exe_id)
        try:
            cleanup_job_exe(job_exe_id)
        except Exception:
            logger.exception('Error performing job execution cleanup')

            sys.exit(-1)

        logger.info('Command completed successfully: scale_cleanup')
