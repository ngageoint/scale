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
    from job.job_type_serializers import JobTypeBaseSerializerV5

    job_type = JobTypeBaseSerializerV5()
    count = serializers.IntegerField()
    longest_queued = serializers.DateTimeField()
    highest_priority = serializers.IntegerField()


class RequeueJobSerializer(serializers.Serializer):
    """Converts re-queue job JSON input to dictionary attributes"""
    started = serializers.DateTimeField(required=False)
    ended = serializers.DateTimeField(required=False)
    status = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    job_ids = serializers.ListField(child=serializers.IntegerField(required=False))
    job_type_ids = serializers.ListField(child=serializers.IntegerField(required=False))
    job_type_names = serializers.ListField(child=serializers.CharField(required=False))
    job_type_categories = serializers.ListField(child=serializers.CharField(required=False))
    error_categories = serializers.ListField(child=serializers.CharField(required=False))
    priority = serializers.IntegerField(required=False)
