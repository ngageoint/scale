'''Defines the serializers for trigger events and rules'''
import rest_framework.pagination as pagination
import rest_framework.serializers as serializers

from util.rest import ModelIdSerializer


class TriggerRuleBaseSerializer(ModelIdSerializer):
    '''Converts trigger rule model fields to REST output.'''
    type = serializers.CharField()
    name = serializers.CharField()
    is_active = serializers.BooleanField()


class TriggerRuleSerializer(TriggerRuleBaseSerializer):
    '''Converts trigger rule model fields to REST output.'''
    created = serializers.DateTimeField()
    archived = serializers.DateTimeField()
    last_modified = serializers.DateTimeField()


class TriggerRuleDetailsSerializer(TriggerRuleBaseSerializer):
    '''Converts trigger rule model fields to REST output.'''
    configuration = serializers.CharField()


class TriggerRuleListSerializer(pagination.PaginationSerializer):
    '''Converts a list of trigger rule models to paginated REST output.'''
    class Meta:
        object_serializer_class = TriggerRuleSerializer


class TriggerEventBaseSerializer(ModelIdSerializer):
    '''Converts trigger event model fields to REST output.'''
    type = serializers.CharField()
    rule = ModelIdSerializer()
    occurred = serializers.DateTimeField()


class TriggerEventSerializer(TriggerEventBaseSerializer):
    '''Converts trigger event model fields to REST output.'''
    rule = TriggerRuleSerializer()


class TriggerEventDetailsSerializer(TriggerEventBaseSerializer):
    '''Converts trigger event model fields to REST output.'''
    rule = TriggerRuleDetailsSerializer()
    description = serializers.CharField()


class TriggerEventListSerializer(pagination.PaginationSerializer):
    '''Converts a list of trigger event models to paginated REST output.'''
    class Meta:
        object_serializer_class = TriggerEventSerializer
