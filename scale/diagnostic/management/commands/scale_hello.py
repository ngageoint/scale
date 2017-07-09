"""Defines the command line method for running the Scale Hello job"""
from __future__ import unicode_literals

import logging

from django.core.management.base import BaseCommand


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Command that executes the Scale Hello job
    """

    help = 'Prints out "Hello Scale!"'

    def handle(self, *args, **options):
        """See :meth:`django.core.management.base.BaseCommand.handle`.
        """
        
        logger.warning('Hello Scale! (stderr)')
        logger.info('Hello Scale! (stdout)')
