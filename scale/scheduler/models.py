from __future__ import unicode_literals

import logging

import django.contrib.postgres.fields
import mesos_api.api as mesos_api
from django.db import models, transaction
from mesos_api.api import MesosError

from queue.models import Queue, QUEUE_ORDER_FIFO, QUEUE_ORDER_LIFO

logger = logging.getLogger(__name__)


class SchedulerManager(models.Manager):
    """Provides additional methods for handling scheduler db entry
    """

    def get_master(self):
        """Gets the current master scheduler instance for the cluster.

        :returns: The master scheduler.
        :rtype: :class:`scheduler.models.Scheduler`
        """
        try:
            return Scheduler.objects.all().defer('status').get(pk=1)
        except Scheduler.DoesNotExist:
            logger.exception('Initial database import missing master scheduler: 1')
            raise

    def initialize_scheduler(self):
        """Initializes the scheduler table by creating a model if one does not already exist
        """

        if self.all().count() == 0:
            logger.info('Creating initial scheduler model in database')
            scheduler = Scheduler()
            scheduler.save()

    def is_master_active(self):
        """Checks whether the current master scheduler is ready to schedule.

        :returns: True if the master scheduler is not registered or not paused.
        :rtype: bool
        """
        scheduler = None
        try:
            scheduler = Scheduler.objects.get(pk=1)
            return not scheduler.is_paused
        except Scheduler.DoesNotExist:
            logger.warning('Unable to check master scheduler status.')
            pass
        return True

    def update_scheduler(self, new_data):
        """Update the data for the scheduler.

        :param new_data: Updated data for the node
        :type new_data: dict
        """

        self.all().update(**new_data)


class Scheduler(models.Model):
    """Represents a scheduler instance. There should only be a single instance of this and it's used for storing
    cluster-wide state related to scheduling in Mesos.

    :keyword is_paused: True if the entire cluster is currently paused and should not accept new jobs
    :type is_paused: :class:`django.db.models.BooleanField()`
    :keyword num_message_handlers: The number of message handlers to have scheduled 
    :type num_message_handlers: :class:`django.db.models.IntegerField`
    :keyword system_logging_level: The logging level for all scale system components
    :type system_logging_level: :class:`django.db.models.CharField`
    """

    QUEUE_MODES = (
        (QUEUE_ORDER_FIFO, QUEUE_ORDER_FIFO),
        (QUEUE_ORDER_LIFO, QUEUE_ORDER_LIFO),
    )

    is_paused = models.BooleanField(default=False)
    num_message_handlers = models.IntegerField(default=1)
    queue_mode = models.CharField(choices=QUEUE_MODES, default=QUEUE_ORDER_FIFO, max_length=50)
    status = django.contrib.postgres.fields.JSONField(default=dict)
    system_logging_level = models.CharField(max_length=10, default='INFO')

    objects = SchedulerManager()


    class Meta(object):
        """meta information for the db"""
        db_table = 'scheduler'
