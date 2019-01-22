"""Defines the serializers for jobs and job types"""
from __future__ import absolute_import

import logging

import rest_framework.serializers as serializers

from util.rest import ModelIdSerializer

logger = logging.getLogger(__name__)

class DataSetBaseSerializerV6(ModelIdSerializer):
    """Converts dataset model fields to REST output"""
    name = serializers.CharField()
    version = serializers.CharField()
    title = serializers.CharField()

class DataSetListSerializerV6(DataSetBaseSerializerV6):
    """Converts dataset model fields to REST output"""
    id = serializers.IntegerField()
    # version = serializers.CharField()
    # versions = serializers.ListField(child=serializers.CharField())
    latest_version = serializers.CharField(source='version')

class DataSetMemberSerializerV6(ModelIdSerializer):
    dataset = serializers.IntegerField()
    created = serializers.DateTimeField()
    definition = serializers.JSONField(source='get_v6_definition_json')

class DataSetFilesSerializerV6(ModelIdSerializer):
    """Converts the datasetfile model fields to REST output"""
    dataset = serializers.IntegerField()
    scale_file = serializers.IntegerField()
    parameter_name = serializers.CharField()

class DataSetDetailsSerializerV6(DataSetBaseSerializerV6):
    """Converts dataset model feields to REST output"""

    description = serializers.CharField()
    created = serializers.DateTimeField()
    definition = serializers.JSONField(source='get_v6_definition_json')
    members = DataSetMemberSerializerV6(required=False, many=True)
    files = DataSetFilesSerializerV6(required=False, many=True)
