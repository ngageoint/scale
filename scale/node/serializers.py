"""Defines the serializers for nodes"""
import rest_framework.serializers as serializers

from util.rest import ModelIdSerializer


class NodeBaseSerializer(ModelIdSerializer):
    """Converts node model fields to REST output."""
    hostname = serializers.CharField()
    port = serializers.IntegerField()
    slave_id = serializers.CharField()


class NodeSerializer(NodeBaseSerializer):
    """Converts node model fields to REST output."""
    pause_reason = serializers.CharField()
    is_paused = serializers.BooleanField()
    is_paused_errors = serializers.BooleanField()
    is_active = serializers.BooleanField()

    archived = serializers.DateTimeField()
    created = serializers.DateTimeField()
    last_offer = serializers.DateTimeField()
    last_modified = serializers.DateTimeField()
