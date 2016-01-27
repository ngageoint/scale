'''Defines the command line method for running the Scale daily metrics process.'''
from __future__ import unicode_literals

import datetime
import logging
import sys

from django.core.management.base import BaseCommand

import metrics.registry as registry
from util.retry import retry_database_query


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    '''Command that executes the Scale daily metrics.'''

    help = 'Executes the Scale daily metrics to continuously calculate performance statistics for each day'

    def handle(self, day, **options):
        '''See :meth:`django.core.management.base.BaseCommand.handle`.

        This method starts the Scale daily metrics.
        '''

        logger.info('Command starting: scale_daily_metrics')
        logger.info(' - Day: %s', day)

        logger.info('Generating metrics...')
        date = datetime.datetime.strptime(day, '%Y-%m-%d')

        # Run the calculations against each provider for the requested date
        failed = 0
        for provider in registry.get_providers():
            metrics_type = provider.get_metrics_type()
            try:
                logger.info('Starting: %s', metrics_type.name)
                self._calculate_metrics(provider, date)
                logger.info('Completed: %s', metrics_type.name)
            except:
                failed += 1
                logger.exception('Unable to calculate metrics: %s', metrics_type.name)

        logger.info('Command completed: scale_daily_metrics')
        if failed:
            logger.info('Metric providers failed: %i', failed)
            sys.exit(failed)

    @retry_database_query
    def _calculate_metrics(self, provider, date):
        '''Calculates the Scale metrics for the given date with the given provider

        :param provider: The metrics provider
        :type provider: :class:`metrics.registry.MetricsTypeProvider`
        :param date: The date for generating metrics
        :type date: :class:`datetime.datetime`
        '''

        provider.calculate(date)
