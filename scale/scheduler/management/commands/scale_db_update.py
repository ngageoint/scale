"""Defines the command that performs a Scale database update"""
from __future__ import unicode_literals

import logging
import os
import sys

from django.core.management.base import BaseCommand

from error.exceptions import ScaleError, get_error_by_exception
from job.models import JobExecution
from util.retry import retry_database_query


logger = logging.getLogger(__name__)


GENERAL_FAIL_EXIT_CODE = 1


class Command(BaseCommand):
    """Command that performs a Scale database update
    """

    help = 'Performs a Scale database update'

    def handle(self, *args, **options):
        """See :meth:`django.core.management.base.BaseCommand.handle`.

        This method starts the command.
        """

        logger.info('Starting Scale database update...')
        try:
            # TODO: implement, make sure to do sigterm
            pass
        except Exception as ex:
            logger.exception('Error performing Scale database update')
            sys.exit(GENERAL_FAIL_EXIT_CODE)

        logger.info('Completed Scale database update')
