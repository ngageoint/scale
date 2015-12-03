'''Defines the functions for handling job execution metrics'''
from __future__ import unicode_literals

from datetime import timedelta
import json
import logging
from urllib import urlencode
from urllib2 import urlopen

from django.conf import settings
from django.db import transaction

from job.models import JobExecution


logger = logging.getLogger(__name__)


def save_job_exe_metrics(job_exe):
    '''Collects and saves the metrics for the given job execution. All database changes occur in an atomic transaction.

    :param job_exe: The job execution
    :type job_exe: :class:`job.models.JobExecution`
    '''

    if settings.INFLUXDB_BASE_URL is not None:
        try:
            logger.info('Storing job execution metrics')
            TFMT = "%Y-%m-%d %H:%M:%S"
            start_time = job_exe.job_started
            end_time = job_exe.job_completed if job_exe.job_completed else job_exe.ended
            end_time += timedelta(seconds=1)
            url = settings.INFLUXDB_BASE_URL + urlencode({
              'q': r"SELECT derivative(cpu_cumulative_usage) AS cpu_usage, max(memory_usage) AS memory_usage, max(memory_working_set) AS memory_working_set " \
                   r" FROM stats WHERE container_name='mesos-%s' and time > '%s' and time < '%s' group by time(2s)" %
                                    (job_exe.job_task_id, start_time.strftime(TFMT), end_time.strftime(TFMT))})
            logger.debug('Opening url: %s', url)
            rsp = urlopen(url, None, 60)
            if rsp.getcode() != 200:
                logger.warning("Unable to access task metrics [%r]: %r %r", url, rsp.getcode(), rsp.read())
            else:
                # reorder data
                data = json.loads(rsp.read())
                if len(data) == 0:
                    logger.warning("Task metrics not found: %r  %r - %r" % (job_exe.job_task_id, start_time.strftime(TFMT), end_time.strftime(TFMT)))
                else:
                    data = data[0]
                    data['points'].reverse()  # influxdb returns these in descending time order
                    data['points'] = zip(*data['points'])
                    # convert billionths of a CPU to CPUs
                    data['points'][1] = map(lambda v: v / 1.e9, data['points'])
                    del data['name']  # not necessary, always "stats"
                    logger.debug("Inserting %d points into the metrics field", len(data['points'][0]))
                    with transaction.atomic():
                        job_exe = JobExecution.objects.select_for_update().defer('stdout', 'stderr').get(pk=job_exe.id)
                        job_exe.job_metrics = data
                        job_exe.save()
        except Exception:  # we catch all because we never want the stats gather to cause the cleanup job to fail
            logger.warning("Unable to access task metrics", exc_info=True)
