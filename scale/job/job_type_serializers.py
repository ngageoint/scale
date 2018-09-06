"""Defines the serializers for jobs and job types"""
from __future__ import absolute_import

import logging

import rest_framework.serializers as serializers

from job.models import Job
from util.rest import ModelIdSerializer

logger = logging.getLogger(__name__)


# TODO: remove this function when REST API v5 is removed
class JobTypeBaseSerializerV5(ModelIdSerializer):
    """Converts job type model fields to REST output"""
    name = serializers.CharField()
    version = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()
    category = serializers.CharField()
    author_name = serializers.CharField()
    author_url = serializers.CharField()

    is_system = serializers.BooleanField()
    is_long_running = serializers.BooleanField()
    is_active = serializers.BooleanField()
    is_operational = serializers.BooleanField()
    is_paused = serializers.BooleanField()

    icon_code = serializers.CharField()

class JobTypeBaseSerializerV6(ModelIdSerializer):
    """Converts job type model fields to REST output"""
    name = serializers.CharField()
    version = serializers.CharField() 
    title = serializers.CharField()
    description = serializers.CharField()
    icon_code = serializers.CharField()

class JobTypeListSerializerV6(JobTypeBaseSerializerV6):
    """Converts job type model fields to REST output"""
    id = None
    version = None
    num_versions = serializers.IntegerField()
    latest_version = serializers.CharField(source='version')

# TODO: remove this function when REST API v5 is removed
class JobTypeSerializerV5(JobTypeBaseSerializerV5):
    """Converts job type model fields to REST output"""
    uses_docker = serializers.NullBooleanField()
    docker_privileged = serializers.NullBooleanField()
    docker_image = serializers.CharField()
    revision_num = serializers.IntegerField()

    priority = serializers.IntegerField()
    max_scheduled = serializers.IntegerField()
    timeout = serializers.IntegerField()
    max_tries = serializers.IntegerField()
    cpus_required = serializers.FloatField(source='get_cpus_required')
    mem_required = serializers.FloatField(source='get_mem_const_required')
    mem_const_required = serializers.FloatField(source='get_mem_const_required')
    mem_mult_required = serializers.FloatField(source='get_mem_mult_required')
    shared_mem_required = serializers.FloatField(source='get_shared_mem_required')
    disk_out_const_required = serializers.FloatField(source='get_disk_out_const_required')
    disk_out_mult_required = serializers.FloatField(source='get_disk_out_mult_required')

    created = serializers.DateTimeField()
    archived = serializers.DateTimeField(source='deprecated')
    paused = serializers.DateTimeField()
    last_modified = serializers.DateTimeField()

class JobTypeSerializerV6(JobTypeBaseSerializerV6):
    """Converts job type model fields to REST output"""

    version = serializers.CharField()
    
    is_active = serializers.BooleanField()
    is_paused = serializers.BooleanField()
    is_system = serializers.BooleanField()
    max_scheduled = serializers.IntegerField()
    revision_num = serializers.IntegerField()
    docker_image = serializers.CharField()

    created = serializers.DateTimeField()
    deprecated = serializers.DateTimeField()
    paused = serializers.DateTimeField()
    last_modified = serializers.DateTimeField()


class JobTypeStatusCountsSerializer(serializers.Serializer):
    """Converts node status count object fields to REST output."""
    status = serializers.ChoiceField(choices=Job.JOB_STATUSES)
    count = serializers.IntegerField()
    most_recent = serializers.DateTimeField()
    category = serializers.CharField()


class JobTypeDetailsSerializerV5(JobTypeSerializerV5):
    """Converts job type model fields to REST output for legacy job types."""
    from error.serializers import ErrorSerializerV5
    from trigger.serializers import TriggerRuleDetailsSerializer

    interface = serializers.JSONField(default=dict, source='manifest')

    configuration = serializers.JSONField(default=dict)
    custom_resources = serializers.JSONField(source='convert_custom_resources')
    error_mapping = serializers.JSONField(default=dict)
    errors = ErrorSerializerV5(many=True)
    trigger_rule = TriggerRuleDetailsSerializer()

    job_counts_6h = JobTypeStatusCountsSerializer(many=True)
    job_counts_12h = JobTypeStatusCountsSerializer(many=True)
    job_counts_24h = JobTypeStatusCountsSerializer(many=True)
    
class JobTypeDetailsSerializerV6(JobTypeSerializerV6):
    """Converts job type model fields to REST output."""

    manifest = serializers.JSONField(default=dict)
    
    configuration = serializers.JSONField(source='get_v6_configuration_json')


class JobTypeStatusSerializer(serializers.Serializer):
    """Converts job type status model and extra statistic fields to REST output."""
    job_type = JobTypeBaseSerializerV5()
    job_counts = JobTypeStatusCountsSerializer(many=True)


class JobTypePendingStatusSerializer(serializers.Serializer):
    """Converts job type pending status model and extra statistic fields to REST output."""
    job_type = JobTypeBaseSerializerV5()
    count = serializers.IntegerField()
    longest_pending = serializers.DateTimeField()


class JobTypeRunningStatusSerializer(serializers.Serializer):
    """Converts job type running status model and extra statistic fields to REST output."""
    job_type = JobTypeBaseSerializerV5()
    count = serializers.IntegerField()
    longest_running = serializers.DateTimeField()


class JobTypeFailedStatusSerializer(serializers.Serializer):
    """Converts job type failed status model and extra statistic fields to REST output."""
    from error.serializers import ErrorSerializerV5

    job_type = JobTypeBaseSerializerV5()
    error = ErrorSerializerV5()
    count = serializers.IntegerField()
    first_error = serializers.DateTimeField()
    last_error = serializers.DateTimeField()


class JobTypeRevisionBaseSerializer(ModelIdSerializer):
    """Converts job type revision model fields to REST output."""
    job_type = ModelIdSerializer()
    revision_num = serializers.IntegerField()


class JobTypeRevisionSerializerV5(JobTypeRevisionBaseSerializer):
    """Converts job type revision model fields to REST output."""
    interface = serializers.JSONField(default=dict, source='manifest')
    created = serializers.DateTimeField()
    
class JobTypeRevisionSerializerV6(JobTypeRevisionBaseSerializer):
    """Converts job type revision model fields to REST output."""
    job_type = JobTypeBaseSerializerV6()
    docker_image = serializers.CharField()
    created = serializers.DateTimeField()
    
class JobTypeRevisionDetailsSerializerV6(JobTypeRevisionSerializerV6):
    """Converts job type revision model fields to REST output."""
    job_type = JobTypeBaseSerializerV6()
    manifest = serializers.JSONField(default=dict)
