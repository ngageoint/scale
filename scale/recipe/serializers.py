import rest_framework.serializers as serializers

from util.rest import ModelIdSerializer


# Serializers for v6 REST API
class RecipeTypeBaseSerializerV6(ModelIdSerializer):
    """Base serializer for recipe types"""

    name = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()
    revision_num = serializers.IntegerField()


class RecipeTypeListSerializerV6(ModelIdSerializer):
    """List serializer for recipe types"""

    name = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()
    is_active = serializers.BooleanField()
    is_system = serializers.BooleanField()
    revision_num = serializers.IntegerField()
    created = serializers.DateTimeField()
    deprecated = serializers.DateTimeField()
    last_modified = serializers.DateTimeField()

class RecipeTypeRevisionBaseSerializerV6(ModelIdSerializer):
    """Base serializer for recipe type revisions"""

    recipe_type = ModelIdSerializer()
    revision_num = serializers.IntegerField()


class RecipeTypeRevisionSerializerV6(RecipeTypeRevisionBaseSerializerV6):
    """Serializer for recipe type revisions"""

    recipe_type = RecipeTypeBaseSerializerV6()
    created = serializers.DateTimeField()

class RecipeTypeRevisionDetailsSerializerV6(RecipeTypeRevisionSerializerV6):
    """Serializer for recipe type revisions"""

    recipe_type = RecipeTypeListSerializerV6()
    definition = serializers.JSONField(source='get_v6_definition_json')


class RecipeTypeBaseSerializerV5(ModelIdSerializer):
    """Converts recipe type model fields to REST output."""
    name = serializers.CharField()
    version = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()


class RecipeTypeSerializerV5(RecipeTypeBaseSerializerV5):
    """Converts recipe type model fields to REST output."""
    is_system = serializers.BooleanField()
    is_active = serializers.BooleanField()
    definition = serializers.JSONField(default=dict)
    revision_num = serializers.IntegerField()
    created = serializers.DateTimeField()
    last_modified = serializers.DateTimeField()
    archived = serializers.DateTimeField(source='deprecated')

    trigger_rule = ModelIdSerializer()


class RecipeTypeSerializerV6(RecipeTypeBaseSerializerV6):
    """Converts recipe type model fields to REST output."""
    is_active = serializers.BooleanField()
    is_system = serializers.BooleanField()
    revision_num = serializers.IntegerField()
    definition = serializers.JSONField(default=dict)
    job_types = None
    sub_recipe_types = None
    created = serializers.DateTimeField()
    deprecated = serializers.DateTimeField()
    last_modified = serializers.DateTimeField()


class RecipeTypeDetailsSerializerV5(RecipeTypeSerializerV5):
    """Converts recipe type model fields to REST output."""
    from job.job_type_serializers import JobTypeBaseSerializerV5
    from trigger.serializers import TriggerRuleDetailsSerializer

    class RecipeTypeDetailsJobSerializer(JobTypeBaseSerializerV5):
        interface = serializers.JSONField(default=dict, source='manifest')

    trigger_rule = TriggerRuleDetailsSerializer()
    job_types = RecipeTypeDetailsJobSerializer(many=True)


class RecipeTypeDetailsSerializerV6(RecipeTypeSerializerV6):
    """Converts recipe type model fields to REST output."""
    from job.job_type_serializers import JobTypeDetailsSerializerV6
    job_types = JobTypeDetailsSerializerV6(many=True)
    sub_recipe_types = RecipeTypeSerializerV6(many=True)


class RecipeTypeRevisionBaseSerializer(ModelIdSerializer):
    """Converts recipe type revision model fields to REST output."""
    recipe_type = ModelIdSerializer()
    revision_num = serializers.IntegerField()


class RecipeTypeRevisionSerializer(RecipeTypeRevisionBaseSerializer):
    """Converts recipe type revision model fields to REST output."""
    definition = serializers.JSONField(default=dict)
    created = serializers.DateTimeField()


class RecipeBaseSerializerV5(ModelIdSerializer):
    """Converts recipe model fields to REST output."""
    recipe_type = RecipeTypeBaseSerializerV5()
    recipe_type_rev = ModelIdSerializer()
    event = ModelIdSerializer()

class RecipeBaseSerializerV6(ModelIdSerializer):
    """Converts recipe model fields to REST output."""
    recipe_type = RecipeTypeBaseSerializerV6()
    recipe_type_rev = ModelIdSerializer()
    event = ModelIdSerializer()


class RecipeSerializerV5(RecipeBaseSerializerV5):
    """Converts recipe model fields to REST output."""
    from trigger.serializers import TriggerEventBaseSerializerV5

    recipe_type_rev = RecipeTypeRevisionBaseSerializer()
    event = TriggerEventBaseSerializerV5()

    is_superseded = serializers.BooleanField()
    root_superseded_recipe = ModelIdSerializer()
    superseded_recipe = ModelIdSerializer()
    superseded_by_recipe = ModelIdSerializer()

    created = serializers.DateTimeField()
    completed = serializers.DateTimeField()
    superseded = serializers.DateTimeField()
    last_modified = serializers.DateTimeField()


class RecipeSerializerV6(RecipeBaseSerializerV6):
    """Converts recipe model fields to REST output."""
    from batch.serializers import BatchBaseSerializerV6
    from trigger.serializers import TriggerEventBaseSerializerV6

    recipe_type_rev = RecipeTypeRevisionBaseSerializerV6()
    event = TriggerEventBaseSerializerV6()
    batch = BatchBaseSerializerV6()
    recipe = RecipeBaseSerializerV6()

    is_superseded = serializers.BooleanField()
    superseded_recipe = ModelIdSerializer()
    superseded_by_recipe = None

    input_file_size = serializers.FloatField()

    source_started = serializers.DateTimeField()
    source_ended = serializers.DateTimeField()
    source_sensor_class = serializers.CharField()
    source_sensor = serializers.CharField()
    source_collection = serializers.CharField()
    source_task = serializers.CharField()

    jobs_total = serializers.IntegerField()
    jobs_pending = serializers.IntegerField()
    jobs_blocked = serializers.IntegerField()
    jobs_queued = serializers.IntegerField()
    jobs_running = serializers.IntegerField()
    jobs_failed = serializers.IntegerField()
    jobs_completed = serializers.IntegerField()
    jobs_canceled = serializers.IntegerField()
    sub_recipes_total = serializers.IntegerField()
    sub_recipes_completed = serializers.IntegerField()
    is_completed = serializers.BooleanField()

    created = serializers.DateTimeField()
    completed = serializers.DateTimeField()
    superseded = serializers.DateTimeField()
    last_modified = serializers.DateTimeField()


class RecipeJobsSerializerV5(serializers.Serializer):
    """Converts recipe model fields to REST output."""
    from job.serializers import JobSerializerV5

    job = JobSerializerV5()
    job_name = serializers.CharField(source='node_name')
    is_original = serializers.BooleanField()
    recipe = ModelIdSerializer()


class RecipeJobsSerializerV6(serializers.Serializer):
    """Converts recipe model fields to REST output."""
    from job.serializers import JobSerializerV6

    job = JobSerializerV6()
    job_name = serializers.CharField(source='node_name')
    is_original = serializers.BooleanField()
    recipe = ModelIdSerializer()


class RecipeJobsDetailsSerializerV5(RecipeJobsSerializerV5):
    """Converts related recipe model fields to REST output."""
    from job.serializers import JobRevisionSerializerV5

    job = JobRevisionSerializerV5()


class RecipeJobsDetailsSerializerV6(RecipeJobsSerializerV6):
    """Converts related recipe model fields to REST output."""
    from job.serializers import JobRevisionSerializerV6

    job = JobRevisionSerializerV6()


class RecipeDetailsInputSerializer(serializers.Serializer):
    """Converts recipe detail model input fields to REST output"""

    name = serializers.CharField()
    type = serializers.CharField()

    def to_representation(self, obj):
        result = super(RecipeDetailsInputSerializer, self).to_representation(obj)

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


class RecipeDetailsSerializerV6(RecipeSerializerV6):
    """Converts related recipe model fields to REST output."""
    from trigger.serializers import TriggerEventDetailsSerializerV6
    from job.job_type_serializers import JobTypeBaseSerializerV6

    recipe_type_rev = RecipeTypeRevisionDetailsSerializerV6()
    event = TriggerEventDetailsSerializerV6()

    superseded_recipe = RecipeBaseSerializerV6()
    superseded_by_recipe = RecipeBaseSerializerV6()

    input = serializers.JSONField(source='get_v6_input_data_json')

    details = serializers.JSONField(source='get_v6_recipe_instance_json')

    job_types = JobTypeBaseSerializerV6(many=True)
    sub_recipe_types = RecipeTypeBaseSerializerV6(many=True)


# TODO: remove this class when REST API v5 is removed
class OldRecipeDetailsSerializer(RecipeSerializerV5):
    """Converts related recipe model fields to REST output."""
    from trigger.serializers import TriggerEventDetailsSerializerV5

    recipe_type = RecipeTypeSerializerV5()
    recipe_type_rev = RecipeTypeRevisionSerializer()
    event = TriggerEventDetailsSerializerV5()
    data = serializers.JSONField(default=dict, source='input')

    jobs = RecipeJobsDetailsSerializerV5(many=True)

    root_superseded_recipe = RecipeBaseSerializerV5()
    superseded_recipe = RecipeBaseSerializerV5()
    superseded_by_recipe = RecipeBaseSerializerV5()
