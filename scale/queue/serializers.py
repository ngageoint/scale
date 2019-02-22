"""Defines the serializers for queue models"""
import rest_framework.serializers as serializers


class JobLoadGroupSerializer(serializers.Serializer):
    """Converts job load model fields to REST output"""
    time = serializers.DateTimeField()

    pending_count = serializers.IntegerField()
    queued_count = serializers.IntegerField()
    running_count = serializers.IntegerField()


class QueueStatusSerializer(serializers.Serializer):
    """Converts queue status model fields to REST output"""
    from job.job_type_serializers import JobTypeBaseSerializerV6

    job_type = JobTypeBaseSerializerV6()
    count = serializers.IntegerField()
    longest_queued = serializers.DateTimeField()
    highest_priority = serializers.IntegerField()

class QueueStatusSerializerV6(serializers.Serializer):
    """Converts queue status model fields to REST output"""
    from job.job_type_serializers import JobTypeBaseSerializerV6

    job_type = JobTypeBaseSerializerV6()
    count = serializers.IntegerField()
    longest_queued = serializers.DateTimeField()
    highest_priority = serializers.IntegerField()
