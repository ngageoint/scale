"""Provides initialization functionality for the Scale system"""
from __future__ import unicode_literals

import logging

from django.conf import settings
from django.db import transaction
from django.utils.timezone import now

from data.data.data import Data
from job.messages.process_job_input import create_process_job_input_messages
from job.models import Job, JobType
from messaging.manager import CommandMessageManager
from queue.models import Queue
from scheduler.models import Scheduler
from trigger.models import TriggerEvent


logger = logging.getLogger(__name__)


def initialize_system():
    """Performs any necessary functions needed for initializing Scale"""

    logger.info('Initializing system')

    Scheduler.objects.initialize_scheduler()

    # Make sure clock job has been created
    clock_job_type = JobType.objects.get_clock_job_type()
    count = Job.objects.filter(job_type_id=clock_job_type.id).count()
    if not count:
        logger.info('Queuing Scale Clock job')
        with transaction.atomic():
            init_event = TriggerEvent.objects.create_trigger_event('SCALE_INIT', None, {}, now())
            job = Queue.objects.queue_new_job_v6(clock_job_type, Data(), init_event)
            CommandMessageManager().send_messages(create_process_job_input_messages([job.pk]))
