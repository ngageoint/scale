'''Defines the serializers for errors'''
import rest_framework.pagination as pagination
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


class ErrorListSerializer(pagination.PaginationSerializer):
    '''Converts a list of job type models to paginated REST output.'''
    class Meta:
        object_serializer_class = ErrorSerializer
