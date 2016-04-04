import rest_framework.serializers as serializers

from util.rest import ModelIdSerializer


class RecipeTypeBaseSerializer(ModelIdSerializer):
    """Converts recipe type model fields to REST output."""
    name = serializers.CharField()
    version = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()


class RecipeTypeSerializer(RecipeTypeBaseSerializer):
    """Converts recipe type model fields to REST output."""
    is_active = serializers.BooleanField()
    definition = serializers.JSONField()
    revision_num = serializers.IntegerField()
    created = serializers.DateTimeField()
    last_modified = serializers.DateTimeField()
    archived = serializers.DateTimeField()

    trigger_rule = ModelIdSerializer()


class RecipeTypeDetailsSerializer(RecipeTypeSerializer):
    """Converts recipe type model fields to REST output."""
    from job.serializers import JobTypeBaseSerializer
    from trigger.serializers import TriggerRuleDetailsSerializer

    class RecipeTypeDetailsJobSerializer(JobTypeBaseSerializer):
        interface = serializers.JSONField()

    trigger_rule = TriggerRuleDetailsSerializer()
    job_types = RecipeTypeDetailsJobSerializer(many=True)


class RecipeTypeRevisionBaseSerializer(ModelIdSerializer):
    """Converts recipe type revision model fields to REST output."""
    recipe_type = ModelIdSerializer()
    revision_num = serializers.IntegerField()


class RecipeTypeRevisionSerializer(RecipeTypeRevisionBaseSerializer):
    """Converts recipe type revision model fields to REST output."""
    definition = serializers.JSONField()
    created = serializers.DateTimeField()


class RecipeBaseSerializer(ModelIdSerializer):
    """Converts recipe model fields to REST output."""
    recipe_type = ModelIdSerializer()
    recipe_type_rev = ModelIdSerializer()
    event = ModelIdSerializer()


class RecipeSerializer(RecipeBaseSerializer):
    """Converts recipe model fields to REST output."""
    from trigger.serializers import TriggerEventBaseSerializer

    recipe_type = RecipeTypeBaseSerializer()
    recipe_type_rev = RecipeTypeRevisionBaseSerializer()
    event = TriggerEventBaseSerializer()

    created = serializers.DateTimeField()
    completed = serializers.DateTimeField()
    last_modified = serializers.DateTimeField()


class RecipeJobsSerializer(serializers.Serializer):
    """Converts recipe model fields to REST output."""
    from job.serializers import JobSerializer

    job = JobSerializer()
    job_name = serializers.CharField()
    recipe = ModelIdSerializer()


class RecipeJobsDetailsSerializer(RecipeJobsSerializer):
    """Converts related recipe model fields to REST output."""
    from job.serializers import JobRevisionSerializer

    job = JobRevisionSerializer()


class RecipeDetailsSerializer(RecipeSerializer):
    """Converts related recipe model fields to REST output."""
    from storage.serializers import ScaleFileBaseSerializer
    from trigger.serializers import TriggerEventDetailsSerializer

    recipe_type = RecipeTypeSerializer()
    recipe_type_rev = RecipeTypeRevisionSerializer()
    event = TriggerEventDetailsSerializer()
    data = serializers.JSONField()

    input_files = ScaleFileBaseSerializer(many=True)
    jobs = RecipeJobsDetailsSerializer(many=True)
