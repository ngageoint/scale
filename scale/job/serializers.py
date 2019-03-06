"""Defines the serializers for jobs and job types"""
from __future__ import absolute_import

import logging

import rest_framework.serializers as serializers

from job.models import Job
from job.job_type_serializers import (JobTypeBaseSerializerV6, JobTypeRevisionBaseSerializer,
                                      JobTypeRevisionSerializerV6, JobTypeRevisionDetailsSerializerV6)

from node.serializers import NodeBaseSerializer
from util.rest import ModelIdSerializer

logger = logging.getLogger(__name__)


class SeedJsonSerializer(serializers.Serializer):
    """Converts Seed formatted input / output JSON to REST ouput"""
    name = serializers.CharField()
    type = serializers.CharField()
    value = serializers.CharField()


class JobBaseSerializerV6(ModelIdSerializer):
    """Converts job model fields to REST output."""
    job_type = JobTypeBaseSerializerV6()
    status = serializers.ChoiceField(choices=Job.JOB_STATUSES)


class JobSerializerV6(JobBaseSerializerV6):
    """Converts job model fields to REST output."""
    from batch.serializers import BatchBaseSerializerV6
    from error.serializers import ErrorBaseSerializerV6
    from ingest.ingest_event_serializers import IngestEventSerializerV6
    from recipe.serializers import RecipeBaseSerializerV6
    from trigger.serializers import TriggerEventSerializerV6

    job_type_rev = JobTypeRevisionBaseSerializer()
    event = TriggerEventSerializerV6()
    ingest_event = IngestEventSerializerV6()
    recipe = RecipeBaseSerializerV6()
    batch = BatchBaseSerializerV6()
    is_superseded = serializers.BooleanField()
    superseded_job = ModelIdSerializer()
    status = serializers.ChoiceField(choices=Job.JOB_STATUSES)
    node = NodeBaseSerializer()
    error = ErrorBaseSerializerV6()
    num_exes = serializers.IntegerField()
    input_file_size = serializers.FloatField()

    source_started = serializers.DateTimeField()
    source_ended = serializers.DateTimeField()
    source_sensor_class = serializers.CharField()
    source_sensor = serializers.CharField()
    source_collection = serializers.CharField()
    source_task = serializers.CharField()
    created = serializers.DateTimeField()
    queued = serializers.DateTimeField()
    started = serializers.DateTimeField()
    ended = serializers.DateTimeField()
    last_status_change = serializers.DateTimeField()
    superseded = serializers.DateTimeField()
    last_modified = serializers.DateTimeField()

    source_started = serializers.DateTimeField()
    source_ended = serializers.DateTimeField()
    source_sensor_class = serializers.CharField()
    source_sensor = serializers.CharField()
    source_collection = serializers.CharField()
    source_task = serializers.CharField()


class JobRevisionSerializerV6(JobSerializerV6):
    """Converts job model fields to REST output."""
    job_type_rev = JobTypeRevisionSerializerV6()


class JobExecutionBaseSerializerV6(ModelIdSerializer):
    """Converts job execution model fields to REST output"""
    status = serializers.CharField(source='get_status')
    exe_num = serializers.IntegerField()
    cluster_id = serializers.CharField()

    created = serializers.DateTimeField()
    queued = serializers.DateTimeField()
    started = serializers.DateTimeField()
    ended = serializers.DateTimeField(source='jobexecutionend.ended')

    job = ModelIdSerializer()
    node = ModelIdSerializer()
    error = ModelIdSerializer(source='jobexecutionend.error')
    job_type = ModelIdSerializer()


class JobExecutionSerializerV6(JobExecutionBaseSerializerV6):
    """Converts job execution model fields to REST output"""
    from error.serializers import ErrorBaseSerializerV6
    from node.serializers import NodeBaseSerializer

    job = ModelIdSerializer()
    node = NodeBaseSerializer()
    error = ErrorBaseSerializerV6(source='jobexecutionend.error')
    job_type = JobTypeBaseSerializerV6()

    timeout = serializers.IntegerField()
    input_file_size = serializers.FloatField()

class JobExecutionDetailsSerializerV6(JobExecutionSerializerV6):
    """Converts job execution model fields to REST output"""
    task_results = serializers.JSONField(default=dict, source='jobexecutionend.task_results')
    resources = serializers.JSONField(source='get_v6_resources_json')
    configuration = serializers.JSONField(default=dict)
    output = serializers.JSONField(default=dict, source='jobexecutionoutput.output')


class JobDetailsSerializerV6(JobSerializerV6):
    """Converts job model and related fields to REST output."""
    job_type_rev = JobTypeRevisionDetailsSerializerV6()

    superseded_job = JobBaseSerializerV6()
    superseded_by_job = JobBaseSerializerV6()
    resources = serializers.JSONField(source='get_v6_resources_json')

    execution = JobExecutionDetailsSerializerV6()
    input = serializers.JSONField(source='get_v6_input_data_json')
    output = serializers.JSONField(source='get_v6_output_data_json')


class JobExecutionLogSerializerV6(JobExecutionSerializerV6):
    """Converts job execution model fields to REST output"""
    is_finished = serializers.BooleanField()
    stdout = serializers.CharField()
    stderr = serializers.CharField()
