'''Defines the serializers for queue models'''
import rest_framework.serializers as serializers


class JobLoadGroupSerializer(serializers.Serializer):
    '''Converts job load model fields to REST output'''
    time = serializers.DateTimeField()

    pending_count = serializers.IntegerField()
    queued_count = serializers.IntegerField()
    running_count = serializers.IntegerField()
