"""Defines the serializers for batches"""
from __future__ import unicode_literals

import rest_framework.serializers as serializers

from batch.models import Batch
from util.rest import ModelIdSerializer


# Serializers for v6 REST API
class BatchBaseSerializerV6(ModelIdSerializer):
    """Base serializer for batches"""

    title = serializers.CharField()
    description = serializers.CharField()


class BatchSerializerV6(BatchBaseSerializerV6):
    """Serializer for a list of batches"""

    from recipe.serializers import RecipeTypeBaseSerializerV6, RecipeTypeRevisionBaseSerializerV6
    from trigger.serializers import TriggerEventBaseSerializer

    recipe_type = RecipeTypeBaseSerializerV6()
    recipe_type_rev = RecipeTypeRevisionBaseSerializerV6()
    event = TriggerEventBaseSerializer()

    is_superseded = serializers.BooleanField()
    root_batch = BatchBaseSerializerV6()
    superseded_batch = BatchBaseSerializerV6()

    is_creation_done = serializers.BooleanField()
    jobs_total = serializers.IntegerField()
    jobs_pending = serializers.IntegerField()
    jobs_blocked = serializers.IntegerField()
    jobs_queued = serializers.IntegerField()
    jobs_running = serializers.IntegerField()
    jobs_failed = serializers.IntegerField()
    jobs_completed = serializers.IntegerField()
    jobs_canceled = serializers.IntegerField()
    recipes_estimated = serializers.IntegerField()
    recipes_total = serializers.IntegerField()
    recipes_completed = serializers.IntegerField()

    created = serializers.DateTimeField()
    superseded = serializers.DateTimeField()
    last_modified = serializers.DateTimeField()


class BatchDetailsSerializerV6(BatchSerializerV6):
    """Detailed serializer for a single batch"""

    from recipe.serializers import RecipeTypeRevisionSerializerV6
    from trigger.serializers import TriggerEventDetailsSerializer

    recipe_type_rev = RecipeTypeRevisionSerializerV6()
    event = TriggerEventDetailsSerializer()

    definition = serializers.JSONField(source='get_v6_definition_json')
    configuration = serializers.JSONField(source='get_v6_configuration_json')
    job_metrics = serializers.JSONField()


# Serializers for v5 REST API
class BatchBaseSerializerV5(ModelIdSerializer):
    """Converts batch model fields to REST output."""
    title = serializers.CharField()
    description = serializers.CharField()
    status = serializers.ChoiceField(choices=Batch.BATCH_STATUSES)

    recipe_type = ModelIdSerializer()
    event = ModelIdSerializer()
    creator_job = ModelIdSerializer()


class BatchSerializerV5(BatchBaseSerializerV5):
    """Converts batch model fields to REST output."""
    from job.serializers import JobBaseSerializer
    from recipe.serializers import RecipeTypeBaseSerializer
    from trigger.serializers import TriggerEventBaseSerializer

    recipe_type = RecipeTypeBaseSerializer()
    event = TriggerEventBaseSerializer()
    creator_job = JobBaseSerializer()

    created_count = serializers.IntegerField()
    failed_count = serializers.IntegerField()
    completed_job_count = serializers.IntegerField(source='jobs_completed')
    completed_recipe_count = serializers.IntegerField(source='recipes_completed')
    total_count = serializers.IntegerField()

    created = serializers.DateTimeField()
    last_modified = serializers.DateTimeField()


class BatchDetailsSerializerV5(BatchSerializerV5):
    """Converts batch model fields to REST output."""
    from job.serializers import JobSerializer
    from recipe.serializers import RecipeTypeSerializer
    from trigger.serializers import TriggerEventDetailsSerializer

    recipe_type = RecipeTypeSerializer()
    event = TriggerEventDetailsSerializer()
    creator_job = JobSerializer()

    definition = serializers.JSONField(source='get_old_definition_json')
