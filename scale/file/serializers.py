"""Defines the serializers for products"""
from __future__ import unicode_literals

import rest_framework.fields as fields
import rest_framework.serializers as serializers

from batch.serializers import BatchBaseSerializerV6
from recipe.serializers import RecipeTypeBaseSerializer
from storage.serializers import ScaleFileSerializerV6
from util.rest import ModelIdSerializer


class FileBaseSerializer(ScaleFileSerializerV6):
    """Converts product file model fields to REST output"""
    is_superseded = serializers.BooleanField()
    superseded = serializers.DateTimeField()

    source_started = serializers.DateTimeField()
    source_ended = serializers.DateTimeField()

    job_type = ModelIdSerializer()
    job = ModelIdSerializer()
    job_exe = ModelIdSerializer()
    job_output = serializers.CharField()

    recipe_type = ModelIdSerializer()
    recipe = ModelIdSerializer()
    recipe_job = serializers.CharField()
    batch = ModelIdSerializer()


class FileSerializer(FileBaseSerializer):
    """Converts product file model fields to REST output"""
    from job.serializers import JobTypeBaseSerializer

    job_type = JobTypeBaseSerializer()
    batch = BatchBaseSerializerV6()
    recipe_type = RecipeTypeBaseSerializer()


class FileDetailsSerializer(FileSerializer):
    """Converts file model fields to REST output"""
    pass



