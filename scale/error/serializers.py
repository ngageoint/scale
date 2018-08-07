"""Defines the serializers for errors"""
import rest_framework.serializers as serializers

from util.rest import ModelIdSerializer


class ErrorBaseSerializerV5(ModelIdSerializer):
    """Converts error model fields to REST output"""
    name = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()
    category = serializers.CharField()
    is_builtin = serializers.BooleanField()


class ErrorSerializerV5(ErrorBaseSerializerV5):
    """Converts error model fields to REST output"""
    created = serializers.DateTimeField()
    last_modified = serializers.DateTimeField()


class ErrorDetailsSerializerV5(ErrorSerializerV5):
    """Converts error model fields to REST output"""
    pass

class ErrorBaseSerializerV6(ModelIdSerializer):
    """Converts error model fields to REST output"""
    name = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()
    job_type_name = serializers.CharField()
    category = serializers.CharField()
    is_builtin = serializers.BooleanField()


class ErrorSerializerV6(ErrorBaseSerializerV6):
    """Converts error model fields to REST output"""
    created = serializers.DateTimeField()
    last_modified = serializers.DateTimeField()


class ErrorDetailsSerializerV6(ErrorSerializerV6):
    """Converts error model fields to REST output"""
    pass