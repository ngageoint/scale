"""Defines the serializers for jobs and job types"""
import rest_framework.serializers as serializers

from job.models import Job
from node.serializers import NodeBaseSerializer
from util.rest import ModelIdSerializer


class JobTypeBaseSerializer(ModelIdSerializer):
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


class JobTypeSerializer(JobTypeBaseSerializer):
    """Converts job type model fields to REST output"""
    uses_docker = serializers.BooleanField()
    docker_privileged = serializers.BooleanField()
    docker_image = serializers.CharField()
    revision_num = serializers.IntegerField()

    priority = serializers.IntegerField()
    max_scheduled = serializers.IntegerField()
    timeout = serializers.IntegerField()
    max_tries = serializers.IntegerField()
    cpus_required = serializers.FloatField()
    mem_required = serializers.FloatField(source='mem_const_required')
    mem_const_required = serializers.FloatField()
    mem_mult_required = serializers.FloatField()
    shared_mem_required = serializers.FloatField()
    disk_out_const_required = serializers.FloatField()
    disk_out_mult_required = serializers.FloatField()

    created = serializers.DateTimeField()
    archived = serializers.DateTimeField()
    paused = serializers.DateTimeField()
    last_modified = serializers.DateTimeField()


class JobTypeStatusCountsSerializer(serializers.Serializer):
    """Converts node status count object fields to REST output."""
    status = serializers.ChoiceField(choices=Job.JOB_STATUSES)
    count = serializers.IntegerField()
    most_recent = serializers.DateTimeField()
    category = serializers.CharField()


class JobTypeDetailsSerializer(JobTypeSerializer):
    """Converts job type model fields to REST output."""
    from error.serializers import ErrorSerializer
    from trigger.serializers import TriggerRuleDetailsSerializer

    interface = serializers.JSONField(default=dict)
    configuration = serializers.JSONField(default=dict)
    custom_resources = serializers.JSONField(source='convert_custom_resources')
    error_mapping = serializers.JSONField(default=dict)
    errors = ErrorSerializer(many=True)
    trigger_rule = TriggerRuleDetailsSerializer()

    job_counts_6h = JobTypeStatusCountsSerializer(many=True)
    job_counts_12h = JobTypeStatusCountsSerializer(many=True)
    job_counts_24h = JobTypeStatusCountsSerializer(many=True)


class JobTypeStatusSerializer(serializers.Serializer):
    """Converts job type status model and extra statistic fields to REST output."""
    job_type = JobTypeBaseSerializer()
    job_counts = JobTypeStatusCountsSerializer(many=True)


class JobTypePendingStatusSerializer(serializers.Serializer):
    """Converts job type pending status model and extra statistic fields to REST output."""
    job_type = JobTypeBaseSerializer()
    count = serializers.IntegerField()
    longest_pending = serializers.DateTimeField()


class JobTypeRunningStatusSerializer(serializers.Serializer):
    """Converts job type running status model and extra statistic fields to REST output."""
    job_type = JobTypeBaseSerializer()
    count = serializers.IntegerField()
    longest_running = serializers.DateTimeField()


class JobTypeFailedStatusSerializer(serializers.Serializer):
    """Converts job type failed status model and extra statistic fields to REST output."""
    from error.serializers import ErrorSerializer

    job_type = JobTypeBaseSerializer()
    error = ErrorSerializer()
    count = serializers.IntegerField()
    first_error = serializers.DateTimeField()
    last_error = serializers.DateTimeField()


class JobTypeRevisionBaseSerializer(ModelIdSerializer):
    """Converts job type revision model fields to REST output."""
    job_type = ModelIdSerializer()
    revision_num = serializers.IntegerField()


class JobTypeRevisionSerializer(JobTypeRevisionBaseSerializer):
    """Converts job type revision model fields to REST output."""
    interface = serializers.JSONField(default=dict)
    created = serializers.DateTimeField()


class JobBaseSerializer(ModelIdSerializer):
    """Converts job model fields to REST output."""
    job_type = JobTypeBaseSerializer()
    job_type_rev = ModelIdSerializer()
    event = ModelIdSerializer()
    node = ModelIdSerializer()
    error = ModelIdSerializer()

    status = serializers.ChoiceField(choices=Job.JOB_STATUSES)
    priority = serializers.IntegerField()
    num_exes = serializers.IntegerField()


class JobSerializer(JobBaseSerializer):
    """Converts job model fields to REST output."""
    from error.serializers import ErrorBaseSerializer
    from trigger.serializers import TriggerEventBaseSerializer

    job_type_rev = JobTypeRevisionBaseSerializer()
    event = TriggerEventBaseSerializer()
    node = NodeBaseSerializer()
    error = ErrorBaseSerializer()

    timeout = serializers.IntegerField()
    max_tries = serializers.IntegerField()

    cpus_required = serializers.FloatField()
    mem_required = serializers.FloatField()
    disk_in_required = serializers.FloatField()
    disk_out_required = serializers.FloatField()

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


class JobRevisionSerializer(JobSerializer):
    """Converts job model fields to REST output."""
    job_type_rev = JobTypeRevisionSerializer()


class JobExecutionBaseSerializer(ModelIdSerializer):
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
        from storage.serializers import ScaleFileSerializer
        FILE_SERIALIZER = ScaleFileSerializer


class JobDetailsOutputSerializer(JobDetailsInputSerializer):
    """Converts job detail model output fields to REST output"""
    class Meta:
        try:
            from product.serializers import ProductFileBaseSerializer
            FILE_SERIALIZER = ProductFileBaseSerializer
        except:
            pass


class JobDetailsSerializer(JobSerializer):
    """Converts job model and related fields to REST output."""
    from error.serializers import ErrorSerializer
    from trigger.serializers import TriggerEventDetailsSerializer

    job_type = JobTypeSerializer()
    job_type_rev = JobTypeRevisionSerializer()
    event = TriggerEventDetailsSerializer()
    error = ErrorSerializer()

    data = serializers.JSONField(default=dict)
    results = serializers.JSONField(default=dict)

    root_superseded_job = JobBaseSerializer()
    superseded_job = JobBaseSerializer()
    superseded_by_job = JobBaseSerializer()

    # Attempt to serialize related model fields
    # Use a localized import to make higher level application dependencies optional
    try:
        from recipe.serializers import RecipeSerializer
        recipes = RecipeSerializer(many=True)
    except:
        recipes = []

    job_exes = JobExecutionBaseSerializer(many=True)

    inputs = JobDetailsInputSerializer(many=True)
    outputs = JobDetailsOutputSerializer(many=True)


class JobUpdateSerializer(JobSerializer):
    """Converts job updates to REST output"""
    from storage.serializers import ScaleFileSerializer

    input_files = ScaleFileSerializer(many=True)


# TODO: remove this function when REST API v5 is removed
class OldJobExecutionSerializer(JobExecutionBaseSerializer):
    """Converts job execution model fields to REST output"""

    from error.serializers import ErrorBaseSerializer
    from node.serializers import NodeBaseSerializerV4

    job = JobBaseSerializer()
    node = NodeBaseSerializerV4()
    error = ErrorBaseSerializer(source='jobexecutionend.error')


class JobExecutionSerializer(JobExecutionBaseSerializer):
    """Converts job execution model fields to REST output"""

    from error.serializers import ErrorBaseSerializer
    from node.serializers import NodeBaseSerializerV4

    job = JobBaseSerializer()
    node = NodeBaseSerializerV4()
    error = ErrorBaseSerializer(source='jobexecutionend.error')

    job_type = JobTypeSerializer()
    exe_num = serializers.IntegerField()
    cluster_id = serializers.CharField()
    input_file_size = serializers.FloatField()

    cpus_scheduled = serializers.FloatField()
    mem_scheduled = serializers.FloatField()
    disk_out_scheduled = serializers.FloatField()
    disk_in_scheduled = serializers.FloatField(source='input_file_size')
    disk_total_scheduled = serializers.FloatField()


# TODO: remove this function when REST API v5 is removed
class OldJobExecutionDetailsSerializer(OldJobExecutionSerializer):
    """Converts job execution model fields to REST output"""

    from error.serializers import ErrorSerializer
    from node.serializers import NodeSerializerV4

    job = JobSerializer()
    node = NodeSerializerV4()
    error = ErrorSerializer(source='jobexecutionend.error')

    cpus_scheduled = serializers.FloatField()
    mem_scheduled = serializers.FloatField()
    disk_in_scheduled = serializers.FloatField(source='input_file_size')
    disk_out_scheduled = serializers.FloatField()
    disk_total_scheduled = serializers.FloatField()

    environment = serializers.JSONField(default=dict)
    results = serializers.JSONField(default=dict, source='jobexecutionoutput.output')
    results_manifest = serializers.JSONField(default=dict)


class JobExecutionDetailsSerializer(JobExecutionSerializer):
    """Converts job execution model fields to REST output"""

    from error.serializers import ErrorSerializer
    from node.serializers import NodeSerializerV4

    job = JobSerializer()
    node = NodeSerializerV4()
    error = ErrorSerializer(source='jobexecutionend.error')

    task_results = serializers.JSONField(default=dict)
    resources = serializers.JSONField(default=dict)
    configuration = serializers.JSONField(default=dict)

    environment = serializers.JSONField(default=dict)
    results = serializers.JSONField(default=dict, source='jobexecutionoutput.output')
    results_manifest = serializers.JSONField(default=dict)


class JobExecutionLogSerializer(JobExecutionSerializer):
    """Converts job execution model fields to REST output"""
    is_finished = serializers.BooleanField()
    stdout = serializers.CharField()
    stderr = serializers.CharField()


# TODO: remove when REST API v5 is removed
class JobWithExecutionSerializer(JobSerializer):
    """Converts job with latest execution model fields to REST output"""
    latest_job_exe = JobExecutionBaseSerializer()
