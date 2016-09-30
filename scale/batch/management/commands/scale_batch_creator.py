"""Defines the command line method for creating a Scale batch"""
from __future__ import unicode_literals

import logging
import sys
from optparse import make_option

from django.core.management.base import BaseCommand

from batch.models import Batch

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Command that creates a Scale batch"""

    option_list = BaseCommand.option_list + (
        make_option('-i', '--batch-id', action='store', type='int', help='The ID of the batch to create'),
    )

    help = 'Creates a new batch of jobs and recipes to be processed on the cluster'

    def __init__(self):
        """Constructor"""
        super(Command, self).__init__()

    def handle(self, **options):
        """See :meth:`django.core.management.base.BaseCommand.handle`.

        This method starts the Scale batch creation process.
        """

        batch_id = options.get('batch_id')

        logger.info('Command starting: scale_batch_creator - Batch ID: %i', batch_id)
        try:
            batch = Batch.objects.get(pk=batch_id)
        except Batch.DoesNotExist:
            logger.exception('Unable to find batch: %i', batch_id)
            sys.exit(1)

        logger.info('Creating batch: %i', batch.id)

        # TODO Schedule all the batch jobs

        logger.info('Command completed: scale_batch_creator')
