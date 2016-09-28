"""Defines the command line method for running the Scale batch process"""
from __future__ import unicode_literals

import logging
import sys
from optparse import make_option

from django.core.management.base import BaseCommand

from batch.models import Batch

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Command that executes setup for a batch of re-processing jobs"""

    option_list = BaseCommand.option_list + (
        make_option('-i', '--batch-id', action='store', type='int', help='The ID of the batch to setup'),
    )

    help = 'Executes the Scale batch setup to schedule jobs for re-processing on the cluster'

    def __init__(self):
        """Constructor"""
        super(Command, self).__init__()

    def handle(self, **options):
        """See :meth:`django.core.management.base.BaseCommand.handle`.

        This method starts the Scale batch setup process.
        """

        batch_id = options.get('batch_id')

        logger.info('Command starting: scale_batch - Batch ID: %i', batch_id)
        try:
            batch = Batch.objects.get(pk=batch_id)
        except Batch.DoesNotExist:
            logger.exception('Unable to find batch: %i', batch_id)
            sys.exit(1)

        logger.info('Setting up batch: %i', batch.id)

        # TODO Schedule all the batch jobs

        logger.info('Command completed: scale_batch')
