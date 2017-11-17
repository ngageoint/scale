"""Provides initialization functionality for the Scale system"""
from __future__ import unicode_literals

import logging

from django.conf import settings
from django.db import transaction
from django.utils.timezone import now

from job.configuration.data.job_data import JobData
from job.models import Job, JobType
from queue.models import Queue
from scheduler.models import Scheduler
from trigger.models import TriggerEvent


logger = logging.getLogger(__name__)


def initialize_system():
    """Performs any necessary functions needed for initializing Scale"""

    logger.info('Initializing system')

    if settings.DEBUG_HOST and settings.DEBUG_PORT:
        logger.info('Attempting connection to remote debug server at %s:%s' % (settings.DEBUG_HOST, settings.DEBUG_PORT))
        from pydevd import settrace
        settrace(host=settings.DEBUG_HOST, port=settings.DEBUG_PORT)

    Scheduler.objects.initialize_scheduler()

    # Make sure clock job has been created
    clock_job_type = JobType.objects.get_clock_job_type()
    count = Job.objects.filter(job_type_id=clock_job_type.id).count()
    if not count:
        logger.info('Queuing Scale Clock job')
        with transaction.atomic():
            init_event = TriggerEvent.objects.create_trigger_event('SCALE_INIT', None, {}, now())
            Queue.objects.queue_new_job(clock_job_type, JobData(), init_event)
