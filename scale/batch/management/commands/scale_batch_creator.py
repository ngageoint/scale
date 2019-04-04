"""Defines the command line method for creating a Scale batch"""
from __future__ import unicode_literals

import logging
import sys
from optparse import make_option

from django.core.management.base import BaseCommand

from batch.models import Batch
from batch.messages.create_batch_recipes import create_batch_recipes_message
from messaging.manager import CommandMessageManager

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Command that creates a Scale batch"""

    help = 'Creates a new batch of jobs and recipes to be processed on the cluster'

    def add_arguments(self, parser):
        parser.add_argument('-i', '--batch-id', action='store', type=int,
                            help='The ID of the batch to create')

    def handle(self, *args, **options):
        """See :meth:`django.core.management.base.BaseCommand.handle`.

        This method starts the Scale batch creation process.
        """

        batch_id = options.get('batch_id')

        logger.info('Command starting: scale_batch_creator - Batch ID: %i', batch_id)

        # Schedule all the batch recipes
        try:
            batch = Batch.objects.get(id=batch_id)
            CommandMessageManager().send_messages([create_batch_recipes_message(batch_id)])
        except Batch.DoesNotExist:
            logger.exception('Unable to find batch: %i', batch_id)
            sys.exit(1)

        logger.info('Command completed: scale_batch_creator')
