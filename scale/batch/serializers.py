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
    from job.serializers import JobBaseSerializerV5
    from recipe.serializers import RecipeTypeBaseSerializerV5
    from trigger.serializers import TriggerEventBaseSerializerV5

    recipe_type = RecipeTypeBaseSerializerV5()
    event = TriggerEventBaseSerializerV5()
    creator_job = JobBaseSerializerV5()

    created_count = serializers.IntegerField()
    failed_count = serializers.IntegerField()
    completed_job_count = serializers.IntegerField(source='jobs_completed')
    completed_recipe_count = serializers.IntegerField(source='recipes_completed')
    total_count = serializers.IntegerField()

    created = serializers.DateTimeField()
    last_modified = serializers.DateTimeField()


class BatchDetailsSerializerV5(BatchSerializerV5):
    """Converts batch model fields to REST output."""
    from job.serializers import JobSerializerV5
    from recipe.serializers import RecipeTypeSerializerV5
    from trigger.serializers import TriggerEventDetailsSerializerV5

    recipe_type = RecipeTypeSerializerV5()
    event = TriggerEventDetailsSerializerV5()
    creator_job = JobSerializerV5()

    definition = serializers.JSONField(source='get_old_definition_json')
