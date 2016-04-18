"""Defines the serializers for source files"""
import rest_framework.fields as fields
import rest_framework.serializers as serializers

from storage.serializers import ScaleFileBaseSerializer


class SourceFileBaseSerializer(ScaleFileBaseSerializer):
    """Converts source file model fields to REST output"""
    is_parsed = serializers.BooleanField()
    parsed = serializers.DateTimeField()


class SourceFileSerializer(SourceFileBaseSerializer):
    """Converts source file model fields to REST output"""
    pass


class SourceFileUpdateField(fields.Field):
    """Field for displaying the update information for a source file"""

    type_name = 'UpdateField'
    type_label = 'update'

    def to_representation(self, value):
        """Converts the model to its update information

        :param value: the source file model
        :type value: :class:`source.models.SourceFile`
        :rtype: dict
        :returns: the dict with the update information
        """

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
    """Converts source file updates to REST output"""
    update = SourceFileUpdateField(source='*')
