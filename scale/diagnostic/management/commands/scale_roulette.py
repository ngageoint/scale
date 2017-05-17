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
    """Command that executes the Scale Roulette job
    """

    help = 'Randomly succeeds or fails'

    def handle(self, *args, **options):
        """See :meth:`django.core.management.base.BaseCommand.handle`.
        """

        logger.info('Spinning roulette wheel...')
        time.sleep(1)  # One second
        random.seed()
        result = random.randint(0, 1)

        try:
            if result:
                logger.info('Landed on black')
            else:
                logger.error('Landed on red')
                raise TestException()
        except ScaleError as err:
            sys.exit(err.exit_code)
