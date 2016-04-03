'''Defines the serializers for errors'''
import rest_framework.serializers as serializers

from util.rest import ModelIdSerializer


class ErrorBaseSerializer(ModelIdSerializer):
    '''Converts error model fields to REST output'''
    name = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()
    category = serializers.CharField()


class ErrorSerializer(ErrorBaseSerializer):
    '''Converts error model fields to REST output'''
    created = serializers.DateTimeField()
    last_modified = serializers.DateTimeField()


class ErrorDetailsSerializer(ErrorSerializer):
    '''Converts error model fields to REST output'''
    pass
