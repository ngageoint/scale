"""Defines the serializers for jobs and job types"""
from __future__ import absolute_import

import logging

import rest_framework.serializers as serializers

from util.rest import ModelIdSerializer

logger = logging.getLogger(__name__)

class DataSetBaseSerializer(ModelIdSerializer):
    """Converts dataset model fields to REST output"""
    name = serializers.CharField()
    version = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()

class DataSetListSerializerV6(DataSetBaseSerializer):
    """Converts dataset model fields to REST output"""
    id = None
    version = None
    versions = serializers.ListField(child=serializers.CharField())
    latest_version = serializers.CharField(source='version')

class DataSetSerializer(DataSetBaseSerializer):
    """Converts dataset model fields to REST output"""
    
    created_time = serializers.DateTimeField()

class DataSetDetailsSerializer(DataSetSerializer):
    """Converts dataset model feields to REST output"""
    
    definition = serializers.JSONField(source='get_v6_definition_json')
    