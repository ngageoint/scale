"""Defines the serializers for ingests"""
import rest_framework.serializers as serializers
from util.rest import ModelIdSerializer

class IngestEventBaseSerializerV6(ModelIdSerializer):
    """Converts ingest event model fields to REST output"""
    type = serializers.CharField()
    occurred = serializers.DateTimeField()

class IngestEventSerializerV6(IngestEventBaseSerializerV6):
    """Converts ingest event model fields to REST output"""


class IngestEventDetailsSerializerV6(IngestEventBaseSerializerV6):
    """Converts ingest event model fields to REST output"""
    description = serializers.JSONField(default=dict)