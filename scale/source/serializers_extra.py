"""Defines the serializers for sources that require extra fields from other applications"""
import rest_framework.serializers as serializers

from source.serializers import SourceFileSerializer


# TODO: remove when REST API v4 is removed
class SourceFileDetailsSerializerV4(SourceFileSerializer):
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

        class SourceFileDetailsProductFileSerializer(ProductFileSerializer):
            is_superseded = serializers.BooleanField()
            superseded = serializers.DateTimeField()

        products = SourceFileDetailsProductFileSerializer(many=True)
    except:
        products = []
