"""Defines the command line method for running the Scale Roulette job"""
from __future__ import unicode_literals

import logging
import random
import sys
import time

from django.core.management.base import BaseCommand

from diagnostic.exceptions import TestException
from error.exceptions import ScaleError

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Command that executes the Scale Two-Face job
    """

    help = 'Randomly returns true or false'

    def handle(self, *args, **options):
        """See :meth:`django.core.management.base.BaseCommand.handle`.
        """

        logger.info('Flipping a coin...')
        time.sleep(1)  # One second
        random.seed(True)
        result = random.choice([True, False])

        try:
            if result:
                logger.info('Landed on heads')
            else:
                logger.error('Landed on tails')

        except ScaleError as err:
            sys.exit(err.exit_code)

        # Need to return the value to the job...somehow. 
