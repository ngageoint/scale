import rest_framework.serializers as serializers

from util.rest import ModelIdSerializer


# Serializers for v6 REST API
class RecipeTypeBaseSerializerV6(ModelIdSerializer):
    """Base serializer for recipe types"""

    name = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()
    revision_num = serializers.IntegerField()


class RecipeTypeRevisionBaseSerializerV6(ModelIdSerializer):
    """Base serializer for recipe type revisions"""

    recipe_type = ModelIdSerializer()
    revision_num = serializers.IntegerField()


class RecipeTypeRevisionSerializerV6(RecipeTypeRevisionBaseSerializerV6):
    """Serializer for recipe type revisions"""

    definition = serializers.JSONField(default=dict)
    created = serializers.DateTimeField()


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
    archived = serializers.DateTimeField()

    trigger_rule = ModelIdSerializer()


class RecipeTypeSerializerV6(RecipeTypeBaseSerializerV6):
    """Converts recipe type model fields to REST output."""
    is_system = serializers.BooleanField()
    is_active = serializers.BooleanField()
    definition = serializers.JSONField(default=dict)
    revision_num = serializers.IntegerField()
    created = serializers.DateTimeField()
    last_modified = serializers.DateTimeField()
    archived = serializers.DateTimeField()

    trigger_rule = ModelIdSerializer()


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
    from job.job_type_serializers import JobTypeBaseSerializerV6
    from trigger.serializers import TriggerRuleDetailsSerializer


    class RecipeTypeDetailsJobSerializer(JobTypeBaseSerializerV6):
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
    from trigger.serializers import TriggerEventBaseSerializerV6

    recipe_type_rev = RecipeTypeRevisionBaseSerializer()
    event = TriggerEventBaseSerializerV6()

    is_superseded = serializers.BooleanField()
    root_superseded_recipe = ModelIdSerializer()
    superseded_recipe = ModelIdSerializer()
    superseded_by_recipe = ModelIdSerializer()

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

    recipe_type_rev = RecipeTypeRevisionSerializer()
    event = TriggerEventDetailsSerializerV6()
    input = serializers.JSONField(default=dict)

    jobs = RecipeJobsDetailsSerializerV6(many=True)

    root_superseded_recipe = RecipeBaseSerializerV6()
    superseded_recipe = RecipeBaseSerializerV6()
    superseded_by_recipe = RecipeBaseSerializerV6()


# TODO: remove this class when REST API v5 is removed
class OldRecipeDetailsSerializer(RecipeSerializerV5):
    """Converts related recipe model fields to REST output."""
    from trigger.serializers import TriggerEventDetailsSerializerV5

    recipe_type = RecipeTypeSerializerV5()
    recipe_type_rev = RecipeTypeRevisionSerializer()
    event = TriggerEventDetailsSerializerV5()
    data = serializers.JSONField(default=dict, source='input')

    inputs = RecipeDetailsInputSerializer(many=True)
    jobs = RecipeJobsDetailsSerializerV5(many=True)

    root_superseded_recipe = RecipeBaseSerializerV5()
    superseded_recipe = RecipeBaseSerializerV5()
    superseded_by_recipe = RecipeBaseSerializerV5()
