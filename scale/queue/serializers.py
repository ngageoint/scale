'''Defines the serializers for queue models'''
import rest_framework.pagination as pagination
import rest_framework.serializers as serializers


class JobLoadGroupSerializer(serializers.Serializer):
    '''Converts job load model fields to REST output'''
    time = serializers.DateTimeField()

    pending_count = serializers.IntegerField()
    queued_count = serializers.IntegerField()
    running_count = serializers.IntegerField()


class JobLoadGroupListSerializer(pagination.PaginationSerializer):
    '''Converts a list of job load models to paginated REST output.'''
    class Meta:
        object_serializer_class = JobLoadGroupSerializer
