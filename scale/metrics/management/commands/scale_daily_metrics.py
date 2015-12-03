'''Defines the command line method for running the Scale daily metrics process.'''
import datetime
import logging
import sys

from django.core.management.base import BaseCommand

import metrics.registry as registry

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    '''Command that executes the Scale daily metrics.'''

    help = u'Executes the Scale daily metrics to continuously calculate performance statistics for each day'

    def handle(self, day, **options):
        '''See :meth:`django.core.management.base.BaseCommand.handle`.

        This method starts the Scale daily metrics.
        '''
        logger.info(u'Command starting: scale_daily_metrics')
        logger.info(u' - Day: %s', day)

        logger.info(u'Generating metrics...')
        date = datetime.datetime.strptime(day, u'%Y-%m-%d')

        # Run the calculations against each provider for the requested date
        failed = 0
        for provider in registry.get_providers():
            metrics_type = provider.get_metrics_type()
            try:
                logger.info('Starting: %s', metrics_type.name)
                provider.calculate(date)
                logger.info('Completed: %s', metrics_type.name)
            except:
                failed += 1
                logger.exception('Unable to calculate metrics: %s', metrics_type.name)

        logger.info(u'Command completed: scale_daily_metrics')
        if failed:
            logger.info('Metric providers failed: %i', failed)
            sys.exit(failed)
