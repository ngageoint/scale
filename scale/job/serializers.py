"""Defines the serializers for jobs and job types"""
from __future__ import absolute_import

import logging

import rest_framework.serializers as serializers

from job.models import Job
from node.serializers import NodeBaseSerializer
from util.rest import ModelIdSerializer

logger = logging.getLogger(__name__)


class SeedJsonSerializer(serializers.Serializer):
    """Converts Seed formatted input / output JSON to REST ouput"""

    name = serializers.CharField()
    type = serializers.CharField()
    value = serializers.CharField()


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
    title = serializers.CharField()
    description = serializers.CharField()
    icon_code = serializers.CharField()
    num_versions = serializers.IntegerField(source='revision_num')
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

    num_versions = None
    latest_version = None
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
    from error.serializers import ErrorSerializer
    from trigger.serializers import TriggerRuleDetailsSerializer

    interface = serializers.JSONField(default=dict, source='manifest')

    configuration = serializers.JSONField(default=dict)
    custom_resources = serializers.JSONField(source='convert_custom_resources')
    error_mapping = serializers.JSONField(default=dict)
    errors = ErrorSerializer(many=True)
    trigger_rule = TriggerRuleDetailsSerializer()

    job_counts_6h = JobTypeStatusCountsSerializer(many=True)
    job_counts_12h = JobTypeStatusCountsSerializer(many=True)
    job_counts_24h = JobTypeStatusCountsSerializer(many=True)
    
class JobTypeDetailsSerializerV6(JobTypeSerializerV6):
    """Converts job type model fields to REST output."""

    manifest = serializers.JSONField(default=dict)
    
    configuration = serializers.JSONField(default=dict)


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
    from error.serializers import ErrorSerializer

    job_type = JobTypeBaseSerializerV5()
    error = ErrorSerializer()
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
    manifest = serializers.JSONField(default=dict)
    created = serializers.DateTimeField()


class JobBaseSerializerV5(ModelIdSerializer):
    """Converts job model fields to REST output."""
    job_type = JobTypeBaseSerializerV5()
    job_type_rev = ModelIdSerializer()
    event = ModelIdSerializer()
    node = ModelIdSerializer()
    error = ModelIdSerializer()

    status = serializers.ChoiceField(choices=Job.JOB_STATUSES)
    priority = serializers.IntegerField()
    num_exes = serializers.IntegerField()


class JobBaseSerializerV6(ModelIdSerializer):
    """Converts job model fields to REST output."""
    job_type = JobTypeBaseSerializerV6()
    job_type_rev = ModelIdSerializer()
    event = ModelIdSerializer()
    node = ModelIdSerializer()
    error = ModelIdSerializer()

    status = serializers.ChoiceField(choices=Job.JOB_STATUSES)
    priority = serializers.IntegerField()
    num_exes = serializers.IntegerField()


# TODO: remove this function when REST API v5 is removed
class JobSerializerV5(JobBaseSerializerV5):
    """Converts job model fields to REST output."""
    from error.serializers import ErrorBaseSerializer
    from trigger.serializers import TriggerEventBaseSerializer

    job_type_rev = JobTypeRevisionBaseSerializer()
    event = TriggerEventBaseSerializer()
    node = NodeBaseSerializer()
    error = ErrorBaseSerializer()

    timeout = serializers.IntegerField()
    max_tries = serializers.IntegerField()

    cpus_required = ''
    mem_required = ''
    disk_out_required = ''
    disk_in_required = serializers.FloatField(source='input_file_size')

    is_superseded = serializers.BooleanField()
    root_superseded_job = ModelIdSerializer()
    superseded_job = ModelIdSerializer()
    superseded_by_job = ModelIdSerializer()
    delete_superseded = serializers.BooleanField()

    created = serializers.DateTimeField()
    queued = serializers.DateTimeField()
    started = serializers.DateTimeField()
    ended = serializers.DateTimeField()
    last_status_change = serializers.DateTimeField()
    superseded = serializers.DateTimeField()
    last_modified = serializers.DateTimeField()
    
class JobSerializerV6(JobBaseSerializerV6):
    """Converts job model fields to REST output."""
    from error.serializers import ErrorBaseSerializer
    from trigger.serializers import TriggerEventBaseSerializer

    job_type_rev = JobTypeRevisionBaseSerializer()
    event = TriggerEventBaseSerializer()
    node = NodeBaseSerializer()
    error = ErrorBaseSerializer()
    resources = serializers.JSONField(source='get_resources_dict')

    timeout = serializers.IntegerField()
    max_tries = serializers.IntegerField()

    input_file_size = serializers.FloatField()

    is_superseded = serializers.BooleanField()
    root_superseded_job = ModelIdSerializer()
    superseded_job = ModelIdSerializer()
    superseded_by_job = ModelIdSerializer()
    delete_superseded = serializers.BooleanField()

    created = serializers.DateTimeField()
    queued = serializers.DateTimeField()
    started = serializers.DateTimeField()
    ended = serializers.DateTimeField()
    last_status_change = serializers.DateTimeField()
    superseded = serializers.DateTimeField()
    last_modified = serializers.DateTimeField()


class JobRevisionSerializerV5(JobSerializerV5):
    """Converts job model fields to REST output."""
    job_type_rev = JobTypeRevisionSerializerV5()
    
class JobRevisionSerializerV6(JobSerializerV6):
    """Converts job model fields to REST output."""
    job_type_rev = JobTypeRevisionSerializerV6()

# TODO: remove this function when REST API v5 is removed
class JobExecutionBaseSerializerV5(ModelIdSerializer):
    """Converts job execution model fields to REST output"""
    status = serializers.CharField(source='get_status')
    command_arguments = serializers.CharField()
    timeout = serializers.IntegerField()

    pre_started = serializers.DateTimeField()
    pre_completed = serializers.DateTimeField()
    pre_exit_code = serializers.IntegerField()

    job_started = serializers.DateTimeField()
    job_completed = serializers.DateTimeField()
    job_exit_code = serializers.IntegerField()

    post_started = serializers.DateTimeField()
    post_completed = serializers.DateTimeField()
    post_exit_code = serializers.IntegerField()

    created = serializers.DateTimeField()
    queued = serializers.DateTimeField()
    started = serializers.DateTimeField()
    ended = serializers.DateTimeField(source='jobexecutionend.ended')
    last_modified = serializers.DateTimeField(source='created')

    job = ModelIdSerializer()
    node = ModelIdSerializer()
    error = ModelIdSerializer()

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

class JobDetailsInputSerializer(serializers.Serializer):
    """Converts job detail model input fields to REST output"""

    name = serializers.CharField()
    type = serializers.CharField()

    def to_representation(self, obj):
        result = super(JobDetailsInputSerializer, self).to_representation(obj)

        value = None
        if 'value' in obj:
            if obj['type'] == 'file':
                value = self.Meta.FILE_SERIALIZER().to_representation(obj['value'])
            elif obj['type'] == 'files':
                value = [self.Meta.FILE_SERIALIZER().to_representation(v) for v in obj['value']]
            else:
                value = obj['value']
        result['value'] = value
        return result

    class Meta:
        from storage.serializers import ScaleFileSerializerV5
        FILE_SERIALIZER = ScaleFileSerializerV5

class JobDetailsOutputSerializer(JobDetailsInputSerializer):
    """Converts job detail model output fields to REST output

    TODO: Deprecated in v6
    """
    class Meta:
        try:
            from product.serializers import ProductFileBaseSerializer
            FILE_SERIALIZER = ProductFileBaseSerializer
        except:
            pass


# TODO: remove this function when REST API v5 is removed
class JobDetailsSerializerV5(JobSerializerV5):
    """Converts job model and related fields to REST output."""
    from error.serializers import ErrorSerializer
    from trigger.serializers import TriggerEventDetailsSerializer

    job_type = JobTypeSerializerV5()
    job_type_rev = JobTypeRevisionSerializerV5()
    event = TriggerEventDetailsSerializer()
    error = ErrorSerializer()

    data = serializers.JSONField(default=dict, source='input')
    results = serializers.JSONField(default=dict, source='output')

    root_superseded_job = JobBaseSerializerV5()
    superseded_job = JobBaseSerializerV5()
    superseded_by_job = JobBaseSerializerV5()

    # Attempt to serialize related model fields
    # Use a localized import to make higher level application dependencies optional
    try:
        from recipe.serializers import RecipeSerializer

        recipes = RecipeSerializer(many=True)
    except:
        recipes = []

    job_exes = JobExecutionBaseSerializerV5(many=True)

    inputs = JobDetailsInputSerializer(many=True)
    outputs = JobDetailsOutputSerializer(many=True)


class JobDetailsSerializerV6(JobSerializerV6):
    """Converts job model and related fields to REST output."""
    from error.serializers import ErrorSerializer
    from trigger.serializers import TriggerEventDetailsSerializer

    job_type = JobTypeSerializerV6()
    job_type_rev = JobTypeRevisionSerializerV6()
    event = TriggerEventDetailsSerializer()
    error = ErrorSerializer()

    try:
        from recipe.serializers import RecipeBaseSerializer
        recipe = RecipeBaseSerializer()
    except:
        recipe = {}

    input = serializers.JSONField(default=dict)
    output = serializers.JSONField(default=dict)
    execution = JobExecutionBaseSerializerV6()

    root_superseded_job = JobBaseSerializerV6()
    superseded_job = JobBaseSerializerV6()
    superseded_by_job = JobBaseSerializerV6()


# TODO: remove this function when REST API v5 is removed
class JobUpdateSerializerV5(JobSerializerV5):
    """Converts job updates to REST output"""
    from storage.serializers import ScaleFileSerializerV5

    input_files = ScaleFileSerializerV5(many=True)
    
class JobUpdateSerializerV6(JobSerializerV6):
    """Converts job updates to REST output"""
    from storage.serializers import ScaleFileSerializerV6

    input_files = ScaleFileSerializerV6(many=True)


# TODO: remove this function when REST API v5 is removed
class JobExecutionSerializerV5(JobExecutionBaseSerializerV5):
    """Converts job execution model fields to REST output"""

    from error.serializers import ErrorBaseSerializer
    from node.serializers import NodeBaseSerializerV4

    job = JobBaseSerializerV5()
    node = NodeBaseSerializerV4()
    error = ErrorBaseSerializer(source='jobexecutionend.error')


class JobExecutionSerializerV6(JobExecutionBaseSerializerV6):
    """Converts job execution model fields to REST output"""

    from error.serializers import ErrorBaseSerializer
    from node.serializers import NodeBaseSerializer

    job = ModelIdSerializer()
    node = NodeBaseSerializer()
    error = ErrorBaseSerializer(source='jobexecutionend.error')
    job_type = JobTypeBaseSerializerV6()

    timeout = serializers.IntegerField()
    input_file_size = serializers.FloatField()


# TODO: remove this function when REST API v5 is removed
class JobExecutionDetailsSerializerV5(JobExecutionSerializerV5):
    """Converts job execution model fields to REST output"""

    from error.serializers import ErrorSerializer
    from node.serializers import NodeSerializerV4

    job = JobSerializerV5()
    node = NodeSerializerV4()
    error = ErrorSerializer(source='jobexecutionend.error')
    
    
class JobExecutionDetailsSerializerV6(JobExecutionSerializerV6):
    """Converts job execution model fields to REST output"""

    task_results = serializers.JSONField(default=dict, source='jobexecutionend.task_results')
    resources = serializers.JSONField(default=dict)
    configuration = serializers.JSONField(default=dict)
    output = serializers.JSONField(default=dict, source='jobexecutionoutput.output')


class JobExecutionLogSerializerV5(JobExecutionSerializerV5):
    """Converts job execution model fields to REST output"""
    is_finished = serializers.BooleanField()
    stdout = serializers.CharField()
    stderr = serializers.CharField()
    
class JobExecutionLogSerializerV6(JobExecutionSerializerV6):
    """Converts job execution model fields to REST output"""
    is_finished = serializers.BooleanField()
    stdout = serializers.CharField()
    stderr = serializers.CharField()


# TODO: remove when REST API v5 is removed
class JobWithExecutionSerializerV5(JobSerializerV5):
    """Converts job with latest execution model fields to REST output"""
    latest_job_exe = JobExecutionBaseSerializerV5()
