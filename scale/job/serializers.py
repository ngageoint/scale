"""Defines the serializers for jobs and job types"""
from __future__ import absolute_import

import logging

import rest_framework.serializers as serializers

from job.models import Job
from job.job_type_serializers import JobTypeBaseSerializerV5, JobTypeBaseSerializerV6
from job.job_type_serializers import JobTypeSerializerV5
from job.job_type_serializers import JobTypeRevisionBaseSerializer
from job.job_type_serializers import JobTypeRevisionSerializerV5, JobTypeRevisionSerializerV6
from job.job_type_serializers import JobTypeRevisionDetailsSerializerV6
from node.serializers import NodeBaseSerializer
from util.rest import ModelIdSerializer

logger = logging.getLogger(__name__)


class SeedJsonSerializer(serializers.Serializer):
    """Converts Seed formatted input / output JSON to REST ouput"""

    name = serializers.CharField()
    type = serializers.CharField()
    value = serializers.CharField()


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
    status = serializers.ChoiceField(choices=Job.JOB_STATUSES)


# TODO: remove this function when REST API v5 is removed
class JobSerializerV5(JobBaseSerializerV5):
    """Converts job model fields to REST output."""
    from error.serializers import ErrorBaseSerializerV5
    from trigger.serializers import TriggerEventBaseSerializerV5

    job_type_rev = JobTypeRevisionBaseSerializer()
    event = TriggerEventBaseSerializerV5()
    node = NodeBaseSerializer()
    error = ErrorBaseSerializerV5()

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
    from batch.serializers import BatchBaseSerializerV6
    from error.serializers import ErrorBaseSerializerV6
    from trigger.serializers import TriggerEventSerializerV6

    job_type_rev = JobTypeRevisionBaseSerializer()
    event = TriggerEventSerializerV6()
    try:
        from recipe.serializers import RecipeBaseSerializerV6
        recipe = RecipeBaseSerializerV6()
    except:
        recipe = {}
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
            from storage.serializers import ScaleFileSerializerV5
            if obj['type'] == 'file':
                value = ScaleFileSerializerV5().to_representation(obj['value'])
            elif obj['type'] == 'files':
                value = [ScaleFileSerializerV5().to_representation(v) for v in obj['value']]
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
    
    def to_representation(self, obj):
        result = super(JobDetailsOutputSerializer, self).to_representation(obj)

        value = None
        if 'value' in obj:
            from product.serializers import ProductFileBaseSerializer
            if obj['type'] == 'file':
                value = ProductFileBaseSerializer().to_representation(obj['value'])
            elif obj['type'] == 'files':
                value = [ProductFileBaseSerializer().to_representation(v) for v in obj['value']]
            else:
                value = obj['value']
        result['value'] = value
        return result


# TODO: remove this function when REST API v5 is removed
class JobDetailsSerializerV5(JobSerializerV5):
    """Converts job model and related fields to REST output."""
    from error.serializers import ErrorSerializerV5
    from trigger.serializers import TriggerEventDetailsSerializerV5
    from recipe.serializers import RecipeSerializerV5

    job_type = JobTypeSerializerV5()
    job_type_rev = JobTypeRevisionSerializerV5()
    event = TriggerEventDetailsSerializerV5()
    error = ErrorSerializerV5()

    data = serializers.JSONField(default=dict, source='input')
    results = serializers.JSONField(default=dict, source='output')

    root_superseded_job = JobBaseSerializerV5()
    superseded_job = JobBaseSerializerV5()
    superseded_by_job = JobBaseSerializerV5()
    
    recipes = RecipeSerializerV5(many=True)

    # Attempt to serialize related model fields
    # Use a localized import to make higher level application dependencies optional
    """try:
        from recipe.serializers import RecipeSerializerV5

        recipes = RecipeSerializerV5(many=True)
    except:
        recipes = []"""

    job_exes = JobExecutionBaseSerializerV5(many=True)

    inputs = JobDetailsInputSerializer(many=True)
    outputs = JobDetailsOutputSerializer(many=True)



# TODO: remove this function when REST API v5 is removed
class JobUpdateSerializerV5(JobSerializerV5):
    """Converts job updates to REST output"""
    from storage.serializers import ScaleFileSerializerV5

    input_files = ScaleFileSerializerV5(many=True)


# TODO: remove this function when REST API v5 is removed
class JobExecutionSerializerV5(JobExecutionBaseSerializerV5):
    """Converts job execution model fields to REST output"""

    from error.serializers import ErrorBaseSerializerV5
    from node.serializers import NodeBaseSerializerV4

    job = JobBaseSerializerV5()
    node = NodeBaseSerializerV4()
    error = ErrorBaseSerializerV5(source='jobexecutionend.error')


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


# TODO: remove this function when REST API v5 is removed
class JobExecutionDetailsSerializerV5(JobExecutionSerializerV5):
    """Converts job execution model fields to REST output"""

    from error.serializers import ErrorSerializerV5
    from node.serializers import NodeSerializerV4

    job = JobSerializerV5()
    node = NodeSerializerV4()
    error = ErrorSerializerV5(source='jobexecutionend.error')
    
    
class JobExecutionDetailsSerializerV6(JobExecutionSerializerV6):
    """Converts job execution model fields to REST output"""

    task_results = serializers.JSONField(default=dict, source='jobexecutionend.task_results')
    resources = serializers.JSONField(default=dict)
    configuration = serializers.JSONField(default=dict)
    output = serializers.JSONField(default=dict, source='jobexecutionoutput.output')

class JobDetailsSerializerV6(JobSerializerV6):
    """Converts job model and related fields to REST output."""

    job_type_rev = JobTypeRevisionDetailsSerializerV6()

    superseded_job = JobBaseSerializerV6()
    superseded_by_job = JobBaseSerializerV6()
    resources = serializers.JSONField(source='get_resources_dict')
    
    execution = JobExecutionDetailsSerializerV6()
    #input = serializers.JSONField(default=dict) #TODO: update to v6 json
    #output = serializers.JSONField(default=dict) #TODO: update to v6 json

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
