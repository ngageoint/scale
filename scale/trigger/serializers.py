"""Defines the serializers for trigger events and rules"""
import rest_framework.serializers as serializers

from util.rest import ModelIdSerializer


class TriggerRuleBaseSerializer(ModelIdSerializer):
    """Converts trigger rule model fields to REST output."""
    type = serializers.CharField()
    name = serializers.CharField()
    is_active = serializers.BooleanField()


class TriggerRuleSerializer(TriggerRuleBaseSerializer):
    """Converts trigger rule model fields to REST output."""
    created = serializers.DateTimeField()
    archived = serializers.DateTimeField()
    last_modified = serializers.DateTimeField()


class TriggerRuleDetailsSerializer(TriggerRuleBaseSerializer):
    """Converts trigger rule model fields to REST output."""
    configuration = serializers.JSONField()


class TriggerEventBaseSerializer(ModelIdSerializer):
    """Converts trigger event model fields to REST output."""
    type = serializers.CharField()
    rule = ModelIdSerializer()
    occurred = serializers.DateTimeField()


class TriggerEventSerializer(TriggerEventBaseSerializer):
    """Converts trigger event model fields to REST output."""
    rule = TriggerRuleSerializer()


class TriggerEventDetailsSerializer(TriggerEventBaseSerializer):
    """Converts trigger event model fields to REST output."""
    rule = TriggerRuleDetailsSerializer()
    description = serializers.JSONField()
