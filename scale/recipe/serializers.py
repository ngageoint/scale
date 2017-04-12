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
    definition = serializers.JSONField(default=dict)
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
        interface = serializers.JSONField(default=dict)

    trigger_rule = TriggerRuleDetailsSerializer()
    job_types = RecipeTypeDetailsJobSerializer(many=True)


class RecipeTypeRevisionBaseSerializer(ModelIdSerializer):
    """Converts recipe type revision model fields to REST output."""
    recipe_type = ModelIdSerializer()
    revision_num = serializers.IntegerField()


class RecipeTypeRevisionSerializer(RecipeTypeRevisionBaseSerializer):
    """Converts recipe type revision model fields to REST output."""
    definition = serializers.JSONField(default=dict)
    created = serializers.DateTimeField()


class RecipeBaseSerializer(ModelIdSerializer):
    """Converts recipe model fields to REST output."""
    recipe_type = RecipeTypeBaseSerializer()
    recipe_type_rev = ModelIdSerializer()
    event = ModelIdSerializer()


class RecipeSerializer(RecipeBaseSerializer):
    """Converts recipe model fields to REST output."""
    from trigger.serializers import TriggerEventBaseSerializer

    recipe_type_rev = RecipeTypeRevisionBaseSerializer()
    event = TriggerEventBaseSerializer()

    is_superseded = serializers.BooleanField()
    root_superseded_recipe = ModelIdSerializer()
    superseded_recipe = ModelIdSerializer()
    superseded_by_recipe = ModelIdSerializer()

    created = serializers.DateTimeField()
    completed = serializers.DateTimeField()
    superseded = serializers.DateTimeField()
    last_modified = serializers.DateTimeField()


class RecipeJobsSerializer(serializers.Serializer):
    """Converts recipe model fields to REST output."""
    from job.serializers import JobSerializer

    job = JobSerializer()
    job_name = serializers.CharField()
    is_original = serializers.BooleanField()
    recipe = ModelIdSerializer()


class RecipeJobsDetailsSerializer(RecipeJobsSerializer):
    """Converts related recipe model fields to REST output."""
    from job.serializers import JobRevisionSerializer

    job = JobRevisionSerializer()


class RecipeDetailsInputSerializer(serializers.Serializer):
    """Converts recipe detail model input fields to REST output"""

    name = serializers.CharField()
    type = serializers.CharField()

    def to_representation(self, obj):
        result = super(RecipeDetailsInputSerializer, self).to_representation(obj)

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
        from storage.serializers import ScaleFileBaseSerializer
        FILE_SERIALIZER = ScaleFileBaseSerializer


class RecipeDetailsSerializer(RecipeSerializer):
    """Converts related recipe model fields to REST output."""
    from trigger.serializers import TriggerEventDetailsSerializer

    recipe_type = RecipeTypeSerializer()
    recipe_type_rev = RecipeTypeRevisionSerializer()
    event = TriggerEventDetailsSerializer()
    data = serializers.JSONField(default=dict)

    inputs = RecipeDetailsInputSerializer(many=True)
    jobs = RecipeJobsDetailsSerializer(many=True)

    root_superseded_recipe = RecipeBaseSerializer()
    superseded_recipe = RecipeBaseSerializer()
    superseded_by_recipe = RecipeBaseSerializer()


# TODO: API_V3 Remove this serializer
class RecipeDetailsSerializerV3(RecipeDetailsSerializer):
    """Converts related recipe model fields to REST output."""
    from storage.serializers import ScaleFileBaseSerializer

    input_files = ScaleFileBaseSerializer(many=True)
