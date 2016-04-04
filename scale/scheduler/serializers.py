"""Defines the serializers for schedulers"""
import rest_framework.serializers as serializers

from scheduler.models import Scheduler


class SchedulerSerializer(serializers.ModelSerializer):
    """Serializer for the scheduler"""

    class Meta(object):
        """Meta class used to define what is serialized and how"""
        model = Scheduler
        fields = (u'is_paused',)
