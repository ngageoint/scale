import rest_framework.serializers as serializers

import logging

from util.rest import ModelIdSerializer

from storage.models import ScaleFile

logger = logging.getLogger(__name__)

# Serializers for v6 REST API
class RecipeTypeBaseSerializerV6(ModelIdSerializer):
    """Base serializer for recipe types"""

    name = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()
    revision_num = serializers.IntegerField()

class RecipeTypeSerializerV6(RecipeTypeBaseSerializerV6):
    """Converts recipe type model fields to REST output."""
    is_active = serializers.BooleanField()
    is_system = serializers.BooleanField()
    revision_num = serializers.IntegerField()
    definition = None
    job_types = None
    sub_recipe_types = None
    created = serializers.DateTimeField()
    deprecated = serializers.DateTimeField()
    last_modified = serializers.DateTimeField()

class RecipeTypeListSerializerV6(ModelIdSerializer):
    """List serializer for recipe types"""

    name = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()
    is_active = serializers.BooleanField()
    is_system = serializers.BooleanField()
    revision_num = serializers.IntegerField()
    job_types = serializers.JSONField()
    sub_recipe_types = serializers.JSONField()
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

    recipe_type = RecipeTypeSerializerV6()
    definition = serializers.JSONField(source='get_v6_definition_json')


class RecipeTypeDetailsSerializerV6(RecipeTypeSerializerV6):
    """Converts recipe type model fields to REST output."""
    from job.job_type_serializers import JobTypeDetailsSerializerV6
    definition = serializers.JSONField(source='get_v6_definition_json')
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


class RecipeBaseSerializerV6(ModelIdSerializer):
    """Converts recipe model fields to REST output."""
    recipe_type = RecipeTypeBaseSerializerV6()
    recipe_type_rev = ModelIdSerializer()
    event = ModelIdSerializer()


class RecipeSerializerV6(RecipeBaseSerializerV6):
    """Converts recipe model fields to REST output."""
    from batch.serializers import BatchBaseSerializerV6
    from ingest.ingest_event_serializers import IngestEventBaseSerializerV6
    from trigger.serializers import TriggerEventBaseSerializerV6

    recipe_type_rev = RecipeTypeRevisionBaseSerializerV6()
    event = TriggerEventBaseSerializerV6()
    ingest_event = IngestEventBaseSerializerV6()
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


class RecipeJobsSerializerV6(serializers.Serializer):
    """Converts recipe model fields to REST output."""
    from job.serializers import JobSerializerV6

    job = JobSerializerV6()
    job_name = serializers.CharField(source='node_name')
    is_original = serializers.BooleanField()
    recipe = ModelIdSerializer()


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
            from storage.serializers import ScaleFileSerializerV6
            if obj['type'] == 'file':
                value = ScaleFileSerializerV6().to_representation(obj['value'])
            elif obj['type'] == 'files':
                if not obj['value']:
                    logger.warning('Empty file list')
                    value = []
                elif isinstance(obj['value'], ScaleFile):
                    logger.warning('Unexpected single file with type "files": %s' % obj['value'])
                    value = [ScaleFileSerializerV6().to_representation(obj['value'])]
                else:
                    value = [ScaleFileSerializerV6().to_representation(v) for v in obj['value']]
            else:
                value = obj['value']
        result['value'] = value
        return result


class RecipeDetailsSerializerV6(RecipeSerializerV6):
    """Converts related recipe model fields to REST output."""
    from trigger.serializers import TriggerEventDetailsSerializerV6
    from ingest.ingest_event_serializers import IngestEventDetailsSerializerV6
    from job.job_type_serializers import JobTypeBaseSerializerV6

    recipe_type_rev = RecipeTypeRevisionDetailsSerializerV6()
    event = TriggerEventDetailsSerializerV6()
    ingest_event = IngestEventDetailsSerializerV6()

    superseded_recipe = RecipeBaseSerializerV6()
    superseded_by_recipe = RecipeBaseSerializerV6()

    input = serializers.JSONField(source='get_v6_input_data_json')

    details = serializers.JSONField(source='get_v6_recipe_instance_json')

    job_types = JobTypeBaseSerializerV6(many=True)
    sub_recipe_types = RecipeTypeBaseSerializerV6(many=True)
