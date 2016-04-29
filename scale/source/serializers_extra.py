"""Defines the serializers for sources that require extra fields from other applications"""
import rest_framework.serializers as serializers

from source.serializers import SourceFileSerializer


class SourceFileDetailsSerializer(SourceFileSerializer):
    """Converts source file model fields to REST output"""
    is_parsed = serializers.BooleanField()
    parsed = serializers.DateTimeField()

    # Attempt to serialize related model fields
    # Use a localized import to make higher level application dependencies optional
    try:
        from ingest.serializers import IngestBaseSerializer
        ingests = IngestBaseSerializer(many=True)
    except:
        ingests = []

    try:
        from product.serializers import ProductFileSerializer
        products = ProductFileSerializer(many=True)
    except:
        products = []
