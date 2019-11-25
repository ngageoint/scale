"""Defines the serializers for schedulers"""
from __future__ import unicode_literals

import rest_framework.serializers as serializers

from scheduler.models import Scheduler

class SchedulerSerializerV6(serializers.ModelSerializer):
    """V6 Serializer for the scheduler"""

    class Meta(object):
        """Meta class used to define what is serialized and how"""
        model = Scheduler
        fields = ('is_paused', 'num_message_handlers', 'system_logging_level', 'queue_mode')