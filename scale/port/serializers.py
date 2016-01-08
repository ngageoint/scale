'''Defines the serializers for import/export configuration'''
import rest_framework.serializers as serializers

from error.models import Error
from job.models import JobType
from recipe.models import RecipeType
from trigger.models import TriggerRule
from util.rest import JSONField


class ConfigurationErrorSerializer(serializers.ModelSerializer):
    '''Converts error model fields to REST output.'''
    name = serializers.CharField()
    title = serializers.CharField(required=False)
    description = serializers.CharField(required=False)
    category = serializers.CharField(required=False)

    class Meta:
        model = Error
        fields = ('name', 'title', 'description', 'category')


class ConfigurationTriggerRuleSerializer(serializers.ModelSerializer):
    '''Converts trigger rule model fields to REST output.'''
    type = serializers.CharField(required=False)
    name = serializers.CharField(required=False)
    is_active = serializers.BooleanField(required=False)

    configuration = JSONField()

    class Meta:
        model = TriggerRule
        fields = ('type', 'name', 'is_active', 'configuration')


class ConfigurationJobTypeSerializer(serializers.ModelSerializer):
    '''Converts job type model fields to REST output.'''
    name = serializers.CharField()
    version = serializers.CharField()

    title = serializers.CharField(required=False)
    description = serializers.CharField(required=False)
    category = serializers.CharField(required=False)
    author_name = serializers.CharField(required=False)
    author_url = serializers.CharField(required=False)

    is_operational = serializers.BooleanField(required=False)

    icon_code = serializers.CharField(required=False)

    docker_privileged = serializers.BooleanField(required=False)
    docker_image = serializers.CharField(required=False)

    priority = serializers.IntegerField(required=False)
    timeout = serializers.IntegerField(required=False)
    max_tries = serializers.IntegerField(required=False)
    cpus_required = serializers.FloatField(required=False)
    mem_required = serializers.FloatField(required=False)
    disk_out_const_required = serializers.FloatField(required=False)
    disk_out_mult_required = serializers.FloatField(required=False)

    interface = JSONField(required=False)
    error_mapping = JSONField(required=False)
    trigger_rule = ConfigurationTriggerRuleSerializer(required=False)

    class Meta:
        model = JobType
        fields = ('name', 'version', 'title', 'description', 'category', 'author_name', 'author_url', 'is_operational',
                  'icon_code', 'docker_privileged', 'docker_image', 'priority', 'timeout', 'max_tries', 'cpus_required',
                  'mem_required', 'disk_out_const_required', 'disk_out_mult_required', 'interface', 'error_mapping',
                  'trigger_rule')


class ConfigurationRecipeTypeSerializer(serializers.ModelSerializer):
    '''Converts recipe type model fields to REST output.'''
    name = serializers.CharField()
    version = serializers.CharField()
    title = serializers.CharField(required=False)
    description = serializers.CharField(required=False)

    definition = JSONField(required=False)
    trigger_rule = ConfigurationTriggerRuleSerializer(required=False)

    class Meta:
        model = RecipeType
        fields = ('name', 'version', 'title', 'description', 'definition', 'trigger_rule')


class ConfigurationSerializer(serializers.Serializer):
    '''Converts export fields to REST output'''
    version = serializers.CharField()
    recipe_types = ConfigurationRecipeTypeSerializer()
    job_types = ConfigurationJobTypeSerializer()
    errors = ConfigurationErrorSerializer()
