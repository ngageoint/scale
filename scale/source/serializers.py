'''Defines the serializers for source files'''
import rest_framework.pagination as pagination
import rest_framework.serializers as serializers
from rest_framework.fields import WritableField

from storage.serializers import ScaleFileBaseSerializer


class SourceFileBaseSerializer(ScaleFileBaseSerializer):
    '''Converts source file model fields to REST output'''
    is_parsed = serializers.BooleanField()
    parsed = serializers.DateTimeField()


class SourceFileSerializer(SourceFileBaseSerializer):
    '''Converts source file model fields to REST output'''
    pass


class SourceFileListSerializer(pagination.PaginationSerializer):
    '''Converts a list of source file models to paginated REST output'''

    class Meta(object):
        '''meta information for the serializer'''
        object_serializer_class = SourceFileSerializer


class SourceFileUpdateField(WritableField):
    '''Field for displaying the update information for a source file'''

    type_name = 'UpdateField'
    type_label = 'update'

    def to_native(self, value):
        '''Converts the model to its update information

        :param value: the source file model
        :type value: :class:`source.models.SourceFile`
        :rtype: dict
        :returns: the dict with the update information
        '''

        if value.is_deleted:
            action = 'DELETED'
            when = value.deleted
        elif value.is_parsed:
            action = 'PARSED'
            when = value.parsed
        else:
            action = 'CREATED'
            when = value.created

        return {'action': action, 'when': when}


class SourceFileUpdateSerializer(SourceFileSerializer):
    '''Converts source file updates to REST output'''
    update = SourceFileUpdateField(source='*')


class SourceFileUpdateListSerializer(pagination.PaginationSerializer):
    '''Converts a list of source file updates to paginated REST output'''

    class Meta(object):
        '''meta information for the serializer'''
        object_serializer_class = SourceFileUpdateSerializer
