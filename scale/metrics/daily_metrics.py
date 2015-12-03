'''Defines the clock event processor for daily system metrics.'''
import datetime
import logging

import django.utils.timezone as timezone

from job.clock import ClockEventError, ClockEventProcessor
from job.models import JobType
from queue.models import Queue

logger = logging.getLogger(__name__)


class DailyMetricsProcessor(ClockEventProcessor):
    '''This class schedules daily metrics jobs on the cluster.'''

    def process_event(self, event, last_event=None):
        '''See :meth:`job.clock.ClockEventProcessor.process_event`.

        Compares the new event with the last event any missing metrics jobs.
        '''

        # Attempt to get the daily metrics job type
        try:
            job_type = JobType.objects.filter(name=u'scale-daily-metrics').last()
        except JobType.DoesNotExist:
            raise ClockEventError(u'Missing required job type: scale-daily-metrics')

        if last_event:
            # Build a list of days that require metrics
            day_count = xrange((event.occurred.date() - last_event.occurred.date()).days)
            days = [last_event.occurred.date() + datetime.timedelta(days=d) for d in day_count]
        else:
            # Use the previous day when first triggered
            days = [timezone.now().date() - datetime.timedelta(days=1)]

        # Schedule one job for each required day
        for day in days:
            job_data = {
                u'input_data': [{
                    u'name': u'Day',
                    u'value': day.strftime(u'%Y-%m-%d'),
                }]
            }
            Queue.objects.queue_new_job(job_type, job_data, event)
