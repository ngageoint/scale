"""Defines the serializers for jobs and job types"""
from __future__ import absolute_import

import logging

import rest_framework.serializers as serializers

from job.models import Job
from util.rest import ModelIdSerializer

logger = logging.getLogger(__name__)

class JobTypeBaseSerializerV6(ModelIdSerializer):
    """Converts job type model fields to REST output"""
    name = serializers.CharField()
    version = serializers.CharField()
    title = serializers.CharField(source='get_title')
    description = serializers.CharField(source='get_description')
    is_active = serializers.BooleanField()
    is_paused = serializers.BooleanField()
    is_published = serializers.BooleanField()
    icon_code = serializers.CharField()
    unmet_resources = serializers.CharField()

class JobTypeListSerializerV6(JobTypeBaseSerializerV6):
    """Converts job type model fields to REST output"""
    id = None
    version = None
    versions = serializers.ListField(child=serializers.CharField())
    latest_version = serializers.CharField(source='version')


class JobTypeSerializerV6(JobTypeBaseSerializerV6):
    """Converts job type model fields to REST output"""
    version = serializers.CharField()

    is_active = serializers.BooleanField()
    is_paused = serializers.BooleanField()
    is_system = serializers.BooleanField()
    max_scheduled = serializers.IntegerField()
    revision_num = serializers.IntegerField()
    docker_image = serializers.CharField()
    unmet_resources = serializers.CharField()

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


class JobTypeDetailsSerializerV6(JobTypeSerializerV6):
    """Converts job type model fields to REST output."""
    manifest = serializers.JSONField(default=dict)
    configuration = serializers.JSONField(source='get_v6_configuration_json')


class JobTypeStatusSerializer(serializers.Serializer):
    """Converts job type status model and extra statistic fields to REST output."""
    job_type = JobTypeBaseSerializerV6()
    job_counts = JobTypeStatusCountsSerializer(many=True)


class JobTypePendingStatusSerializer(serializers.Serializer):
    """Converts job type pending status model and extra statistic fields to REST output."""
    job_type = JobTypeBaseSerializerV6()
    count = serializers.IntegerField()
    longest_pending = serializers.DateTimeField()


class JobTypeRunningStatusSerializer(serializers.Serializer):
    """Converts job type running status model and extra statistic fields to REST output."""
    job_type = JobTypeBaseSerializerV6()
    count = serializers.IntegerField()
    longest_running = serializers.DateTimeField()


class JobTypeFailedStatusSerializer(serializers.Serializer):
    """Converts job type failed status model and extra statistic fields to REST output."""
    from error.serializers import ErrorSerializerV6

    job_type = JobTypeBaseSerializerV6()
    error = ErrorSerializerV6()

    count = serializers.IntegerField()
    first_error = serializers.DateTimeField()
    last_error = serializers.DateTimeField()

class JobTypeStatusSerializerV6(serializers.Serializer):
    """Converts job type status model and extra statistic fields to REST output."""
    job_type = JobTypeBaseSerializerV6()
    job_counts = JobTypeStatusCountsSerializer(many=True)


class JobTypePendingStatusSerializerV6(serializers.Serializer):
    """Converts job type pending status model and extra statistic fields to REST output."""
    job_type = JobTypeBaseSerializerV6()
    count = serializers.IntegerField()
    longest_pending = serializers.DateTimeField()


class JobTypeRunningStatusSerializerV6(serializers.Serializer):
    """Converts job type running status model and extra statistic fields to REST output."""
    job_type = JobTypeBaseSerializerV6()
    count = serializers.IntegerField()
    longest_running = serializers.DateTimeField()


class JobTypeFailedStatusSerializerV6(serializers.Serializer):
    """Converts job type failed status model and extra statistic fields to REST output."""
    from error.serializers import ErrorSerializerV6

    job_type = JobTypeBaseSerializerV6()
    error = ErrorSerializerV6()
    count = serializers.IntegerField()
    first_error = serializers.DateTimeField()
    last_error = serializers.DateTimeField()

class JobTypeRevisionBaseSerializer(ModelIdSerializer):
    """Converts job type revision model fields to REST output."""
    job_type = ModelIdSerializer()
    revision_num = serializers.IntegerField()


class JobTypeRevisionSerializerV6(JobTypeRevisionBaseSerializer):
    """Converts job type revision model fields to REST output."""
    job_type = JobTypeBaseSerializerV6()
    docker_image = serializers.CharField()
    created = serializers.DateTimeField()


class JobTypeRevisionDetailsSerializerV6(JobTypeRevisionSerializerV6):
    """Converts job type revision model fields to REST output."""
    job_type = JobTypeBaseSerializerV6()
    manifest = serializers.JSONField(default=dict)
