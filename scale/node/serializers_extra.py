"""Defines the serializers for nodes that require extra fields from other applications"""
import rest_framework.serializers as serializers

from node.serializers import NodeSerializer
from util.rest import ModelIdSerializer


class NodeDetailsSerializer(NodeSerializer):
    """Converts node model fields to REST output."""
    try:
        from job.serializers import JobExecutionSerializer

        class NodeStatusJobExecutionSerializer(JobExecutionSerializer):
            """Converts job execution model fields to REST output"""
            node = ModelIdSerializer()

            cpus_scheduled = serializers.FloatField()
            mem_scheduled = serializers.FloatField()
            disk_in_scheduled = serializers.FloatField()
            disk_out_scheduled = serializers.FloatField()
            disk_total_scheduled = serializers.FloatField()

        job_exes_running = NodeStatusJobExecutionSerializer(many=True)
    except:
        pass


class NodeStatusCountsSerializer(serializers.Serializer):
    """Converts node status count object fields to REST output."""
    status = serializers.CharField()
    count = serializers.IntegerField()
    most_recent = serializers.DateTimeField()
    category = serializers.CharField()


class NodeStatusSerializer(serializers.Serializer):
    """Converts node model fields with job execution counts to REST output."""
    node = NodeSerializer()
    is_online = serializers.BooleanField()
    job_exe_counts = NodeStatusCountsSerializer(many=True)

    # Attempt to serialize related model fields
    # Use a localized import to make higher level application dependencies optional
    try:
        from job.serializers import JobExecutionSerializer

        class NodeStatusJobExecutionSerializer(JobExecutionSerializer):
            """Converts job execution model fields to REST output"""
            node = ModelIdSerializer()

            cpus_scheduled = serializers.FloatField()
            mem_scheduled = serializers.FloatField()
            disk_in_scheduled = serializers.FloatField()
            disk_out_scheduled = serializers.FloatField()
            disk_total_scheduled = serializers.FloatField()

        job_exes_running = NodeStatusJobExecutionSerializer(many=True)
    except:
        pass
