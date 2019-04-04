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
    created = serializers.DateTimeField()


class BatchSerializerV6(BatchBaseSerializerV6):
    """Serializer for a list of batches"""

    from recipe.serializers import RecipeTypeBaseSerializerV6, RecipeTypeRevisionBaseSerializerV6
    from trigger.serializers import TriggerEventBaseSerializerV6

    recipe_type = RecipeTypeBaseSerializerV6()
    recipe_type_rev = RecipeTypeRevisionBaseSerializerV6()
    event = TriggerEventBaseSerializerV6()

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

    superseded = serializers.DateTimeField()
    last_modified = serializers.DateTimeField()


class BatchDetailsSerializerV6(BatchSerializerV6):
    """Detailed serializer for a single batch"""

    from recipe.serializers import RecipeTypeRevisionSerializerV6
    from trigger.serializers import TriggerEventDetailsSerializerV6

    recipe_type_rev = RecipeTypeRevisionSerializerV6()
    event = TriggerEventDetailsSerializerV6()

    definition = serializers.JSONField(source='get_v6_definition_json')
    configuration = serializers.JSONField(source='get_v6_configuration_json')
    job_metrics = serializers.JSONField()
