"""Defines the serializers for batches"""
from __future__ import unicode_literals

import rest_framework.serializers as serializers

from batch.models import Batch
from util.rest import ModelIdSerializer


class BatchBaseSerializer(ModelIdSerializer):
    """Converts batch model fields to REST output."""
    title = serializers.CharField()
    description = serializers.CharField()
    status = serializers.ChoiceField(choices=Batch.BATCH_STATUSES)

    recipe_type = ModelIdSerializer()
    event = ModelIdSerializer()
    creator_job = ModelIdSerializer()


class BatchSerializer(BatchBaseSerializer):
    """Converts batch model fields to REST output."""
    from job.serializers import JobBaseSerializer
    from recipe.serializers import RecipeTypeBaseSerializer
    from trigger.serializers import TriggerEventBaseSerializer

    recipe_type = RecipeTypeBaseSerializer()
    event = TriggerEventBaseSerializer()
    creator_job = JobBaseSerializer()

    created_count = serializers.IntegerField()
    failed_count = serializers.IntegerField()
    total_count = serializers.IntegerField()

    created = serializers.DateTimeField()
    last_modified = serializers.DateTimeField()
