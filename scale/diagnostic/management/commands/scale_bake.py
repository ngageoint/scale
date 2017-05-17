"""Defines the command line method for running the Scale Bake job"""
from __future__ import unicode_literals

import logging
import time

from django.core.management.base import BaseCommand


logger = logging.getLogger(__name__)

FIFTEEN_MIN = 15 * 60  # In seconds


class Command(BaseCommand):
    """Command that executes the Scale Bake job
    """

    help = 'Sleeps for 15 minutes'

    def handle(self, *args, **options):
        """See :meth:`django.core.management.base.BaseCommand.handle`.
        """

        logger.info('Cookies are in the oven, setting the timer for 15 minutes...')
        time.sleep(FIFTEEN_MIN)
        logger.info('DING! Cookies are done.')
