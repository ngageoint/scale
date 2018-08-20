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
    configuration = serializers.JSONField(default=dict)


class TriggerEventBaseSerializerV5(ModelIdSerializer):
    """Converts trigger event model fields to REST output."""
    type = serializers.CharField()
    rule = ModelIdSerializer()
    occurred = serializers.DateTimeField()
    
class TriggerEventBaseSerializerV6(ModelIdSerializer):
    """Converts trigger event model fields to REST output."""
    type = serializers.CharField()
    occurred = serializers.DateTimeField()
    

class TriggerEventSerializerV5(TriggerEventBaseSerializerV5):
    """Converts trigger event model fields to REST output."""
    rule = TriggerRuleSerializer()
    
    
class TriggerEventSerializerV6(TriggerEventBaseSerializerV6):
    """Converts trigger event model fields to REST output."""
    

class TriggerEventDetailsSerializerV5(TriggerEventBaseSerializerV5):
    """Converts trigger event model fields to REST output."""
    rule = TriggerRuleDetailsSerializer()
    description = serializers.JSONField(default=dict)
    
class TriggerEventDetailsSerializerV6(TriggerEventBaseSerializerV6):
    """Converts trigger event model fields to REST output."""
    description = serializers.JSONField(default=dict)
