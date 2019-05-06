"""Defines the serializers for errors"""
import rest_framework.serializers as serializers

from util.rest import ModelIdSerializer

class ErrorBaseSerializerV6(ModelIdSerializer):
    """Converts error model fields to REST output"""
    name = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()
    job_type_name = serializers.CharField()
    category = serializers.CharField()
    is_builtin = serializers.BooleanField()
    should_be_retried = serializers.BooleanField()


class ErrorSerializerV6(ErrorBaseSerializerV6):
    """Converts error model fields to REST output"""
    created = serializers.DateTimeField()
    last_modified = serializers.DateTimeField()


class ErrorDetailsSerializerV6(ErrorSerializerV6):
    """Converts error model fields to REST output"""
    pass